"""Part E: the cost of persistent false alarms (FR14) and baselines from the closest works (FR10).
See PREREGISTRATION_persistence.md.

Usage:  python -m ereplan.persistence_exp dev        # tune B9-B11 on development seeds 1500-1505
        python -m ereplan.persistence_exp confirm    # pre-registered test, seeds 1400-1419
Options: --procs N (default: all cores), --tuned PATH (tuned.json from the dev step; default: newest)
"""
import argparse, glob, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon

from .config import Setting
from .runner import run

DROPS, QS, LEAKS = (0.95, 0.85, 0.75, 0.60), (0.8, 0.95), (1.0, 3.0)
FS, PIS = (0.05, 0.15), (0.0, 0.5, 0.8, 1.0)
TEST_SEEDS, DEV_SEEDS = tuple(range(1400, 1420)), tuple(range(1500, 1506))
SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
V4 = dict(SESSION, q_prior_strength=3.0)
FIXED = {
    "never": ("B2_never", dict(window=30)),
    "always": ("B1_always", dict(window=30)),
    "cusum": ("B4_cusum", dict(h=6, p1=0.8)),
    "v4": ("Rule_v4_fa", dict(V4)),                         # the pre-registered rule v4 (pi_hat = 1)
    "v4_ind": ("Rule_v4_pi", dict(V4, pi_assumed=0.0)),     # independence assumption (VRR-Stop §3.2)
    "v4_match": ("Rule_v4_pi", dict(V4)),                   # pi_hat = the true pi (as measured by the repeat test)
}
GRIDS = {   # tuning grids for the literature baselines (pre-registered)
    "b9_vrr": ("B9_vrr", [dict(window=30, reverify_k=k) for k in (1, 2)]),
    "b10_pb": ("B10_pbandit", [dict(gamma=g, check_rate=c) for g in (0.95, 0.98, 0.995) for c in (0.0, 0.2, 0.5)]),
    "b11_btm": ("B11_btm", [dict(n_off=n, horizon_mode="session", session_cap=50) for n in (20.0, 100.0)]),
}
NEVER_CHECKS = {"never", "b11_btm"}       # results cannot depend on f or pi


def setting(q, lm, f, pi):
    return Setting().with_(q_true=q, q_assumed=q, check_frac=0.15, leak_mult=lm, false_alarm=f,
                           fa_persistence=pi if f > 0 else -1.0)


def _job(a):
    key, name, params, drop, q, lm, f, pi, seed = a
    params = dict(params)
    if key == "v4_match":
        params["pi_assumed"] = pi
    r = run(name, params, setting(q, lm, f, pi), f"drop_{drop:.2f}", seed)
    return dict(strategy=key, drop=drop, q=q, leak_mult=lm, f=f, pi=pi, seed=seed, loss=r["total_loss_fail"],
                fail_rate=r["fail_rate"], leak_rate=r["leak_rate"], checks=r["checks_per_task"],
                fa_failed=r["fa_failed_rate"], rechecks=r["rechecks_per_task"],
                false_switches=r["false_switches_per_1000"], switches=r["switches"],
                tool_check=r["tool_check_spend_per_task"], switch_spend=r["switch_spend_per_task"],
                leak_cost=r["leak_cost_per_task"], fail_cost=r["fail_cost_per_task"])


def conditions(drops, qs, leaks):
    """f = 0 once per (drop, q, leak) (pi is meaningless there), then every f > 0 with every pi."""
    out = [(d, q, lm, 0.0, 1.0) for d, q, lm in itertools.product(drops, qs, leaks)]
    out += [(d, q, lm, f, pi) for d, q, lm, f, pi in itertools.product(drops, qs, leaks, FS, PIS)]
    return out


def make_jobs(strats, conds, seeds):
    jobs, copies = [], []
    for key, (name, params) in strats.items():
        for (d, q, lm, f, pi), sd in itertools.product(conds, seeds):
            if key in NEVER_CHECKS and f > 0:
                copies.append((key, (d, q, lm, 0.0, 1.0, sd), (d, q, lm, f, pi, sd))); continue
            if key in ("v4_ind", "v4_match") and f == 0:            # f = 0: no false-alarm term, same as v4
                copies.append((key, ("v4", d, q, lm, 0.0, 1.0, sd), (d, q, lm, f, pi, sd))); continue
            if key == "v4_match" and pi in (0.0, 1.0):              # identical to v4_ind / v4 by construction
                copies.append((key, ("v4_ind" if pi == 0.0 else "v4", d, q, lm, f, pi, sd), (d, q, lm, f, pi, sd))); continue
            jobs.append((key, name, params, d, q, lm, f, pi, sd))
    return jobs, copies


def execute(strats, conds, seeds, procs):
    jobs, copies = make_jobs(strats, conds, seeds)
    with Pool(procs) as pool:
        rows = pool.map(_job, jobs, chunksize=4)
    idx = {(r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"], r["seed"]): r for r in rows}
    for key, src, dst in copies:
        if len(src) == 6:
            r = dict(idx[(key,) + src])
        else:
            r = dict(idx[src])
        r.update(strategy=key, drop=dst[0], q=dst[1], leak_mult=dst[2], f=dst[3], pi=dst[4], seed=dst[5], copied=True)
        rows.append(r)
    return rows, len(jobs)


def cmd_dev(a):
    conds = [c for c in conditions(DROPS, (0.95,), (3.0,)) if c[4] in (0.0, 1.0)]
    t0, out = time.time(), {}
    L = ["# Part E development tuning (seeds 1500-1505; q 0.95, leak 3; f 0 / 0.05 / 0.15 x pi 0 / 1)", ""]
    for key, (name, grid) in GRIDS.items():
        scores = []
        for params in grid:
            rows, _ = execute({key: (name, params)}, conds, DEV_SEEDS, a.procs)
            scores.append((float(np.mean([r["loss"] for r in rows])), params))
            L.append(f"- {key} {params}: mean loss {scores[-1][0]:.2f}")
        best = min(scores, key=lambda x: x[0])
        out[key] = dict(name=name, params=best[1], dev_loss=best[0])
        L.append(f"  -> chosen {best[1]}")
    d = os.path.join("results", f"persist_dev_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(d, exist_ok=True)
    json.dump(out, open(os.path.join(d, "tuned.json"), "w"), indent=1)
    L.append(f"\n{time.time() - t0:.0f} s. Saved {d}/tuned.json")
    open(os.path.join(d, "report.md"), "w").write("\n".join(L)); print("\n".join(L))


def _p(x, y, alt):
    x, y = np.asarray(x), np.asarray(y)
    if np.allclose(x, y):
        return 1.0
    return float(wilcoxon(x, y, alternative=alt).pvalue)


def cmd_confirm(a):
    tuned_path = a.tuned or sorted(glob.glob("results/persist_dev_*/tuned.json"))[-1]
    tuned = json.load(open(tuned_path))
    strats = dict(FIXED)
    for key in GRIDS:
        strats[key] = (tuned[key]["name"], tuned[key]["params"])
    conds = conditions(DROPS, QS, LEAKS)
    t0 = time.time()
    rows, n_jobs = execute(strats, conds, TEST_SEEDS, a.procs)
    out = os.path.join("results", f"persist_confirm_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(dict(tuned=tuned, tuned_path=tuned_path), open(os.path.join(out, "config.json"), "w"), indent=1)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))

    K = lambda r: (r["drop"], r["q"], r["leak_mult"], r["seed"])
    by = {}
    for r in rows:
        by.setdefault((r["strategy"], r["f"], r["pi"]), {})[K(r)] = r
    keys = sorted(by[("always", 0.0, 1.0)])

    def loss(s, f, pi, field="loss"):
        return [by[(s, f, pi)][k][field] for k in keys]

    def delta(s, f, pi, field="loss"):          # cost of false alarms: same seeds, f vs f = 0
        return [by[(s, f, pi)][k][field] - by[(s, 0.0, 1.0)][k][field] for k in keys]

    def pooled(fn, s, pis, fs=FS, field="loss"):
        return sum((fn(s, f, pi, field) for f in fs for pi in pis), [])

    S = list(strats)
    L = ["# Part E: cost of persistent false alarms and baselines from the closest works (pre-registered)", "",
         f"Seeds 1400-1419; {len(rows)} rows ({n_jobs} runs, the rest copied where results cannot differ); "
         f"{time.time() - t0:.0f} s. Metric: total loss per task incl. one task cost per failed task.",
         f"Tuned baselines (dev seeds 1500-1505): {json.dumps({k: tuned[k]['params'] for k in GRIDS})}", "",
         "## Mean total loss by false-alarm rate f and persistence pi (pooled over drop, q, leak)", "",
         "| f | pi | " + " | ".join(S) + " |", "|---|---|" + "---|" * len(S)]
    L.append("| 0 | - | " + " | ".join(f"{np.mean(loss(s, 0.0, 1.0)):.1f}" for s in S) + " |")
    for f in FS:
        for pi in PIS:
            L.append(f"| {f:g} | {pi:g} | " + " | ".join(f"{np.mean(loss(s, f, pi)):.1f}" for s in S) + " |")

    L += ["", "## Cost of false alarms (loss at f minus loss at f = 0, same seeds), pooled over f = 0.05 and 0.15", "",
          "| Strategy | " + " | ".join(f"pi = {pi:g}" for pi in PIS) + " |", "|---|" + "---|" * len(PIS)]
    for s in S:
        L.append(f"| {s} | " + " | ".join(f"{np.mean(pooled(delta, s, [pi])):+.1f}" for pi in PIS) + " |")

    L += ["", "## Where the false-alarm cost goes (pooled over f > 0; per task)", "",
          "| Strategy | pi | failed-task cost | leak cost | tool + check spend | switch spend | tasks failed with a false alarm | false switches /1000 |",
          "|---|---|---|---|---|---|---|---|"]
    for s in ("always", "v4", "v4_ind", "b9_vrr"):
        for pi in (0.0, 1.0):
            L.append(f"| {s} | {pi:g} | {np.mean(pooled(delta, s, [pi], field='fail_cost')):+.1f} | "
                     f"{np.mean(pooled(delta, s, [pi], field='leak_cost')):+.1f} | {np.mean(pooled(delta, s, [pi], field='tool_check')):+.1f} | "
                     f"{np.mean(pooled(delta, s, [pi], field='switch_spend')):+.1f} | {np.mean(pooled(loss, s, [pi], field='fa_failed')):.1%} | "
                     f"{np.mean(pooled(delta, s, [pi], field='false_switches')):+.1f} |")

    R = ["", "## Pre-registered hypotheses"]
    # H-E1
    d1, d0 = pooled(delta, "always", [1.0]), pooled(delta, "always", [0.0])
    p1 = _p(d1, d0, "greater"); m1, m0 = np.mean(d1), np.mean(d0)
    he1 = p1 < 0.05 and m1 >= 3 * max(m0, 1e-9)
    mono = [np.mean(pooled(delta, "always", [pi])) for pi in PIS]
    R.append(f"- H-E1 always-check: false-alarm cost at pi = 1 ({m1:.1f}) > at pi = 0 ({m0:.1f}), ratio {m1 / max(m0, 1e-9):.1f} (need >= 3), "
             f"p = {p1:.2g} -> {'CONFIRMED' if he1 else 'NOT CONFIRMED'}. By pi (descriptive): " +
             ", ".join(f"{pi:g}: {v:.1f}" for pi, v in zip(PIS, mono)) + f"; monotone: {all(np.diff(mono) > 0)}")
    # H-E3
    a3, b3 = pooled(loss, "v4", [1.0]), pooled(loss, "v4_ind", [1.0])
    p3 = _p(a3, b3, "less"); he3 = p3 < 0.05 and np.mean(a3) <= 0.95 * np.mean(b3)
    R.append(f"- H-E3 at pi = 1, v4 < v4_ind by >= 5%: {np.mean(a3):.1f} vs {np.mean(b3):.1f} ({100 * (np.mean(a3) / np.mean(b3) - 1):+.1f}%), "
             f"p = {p3:.2g} -> {'CONFIRMED' if he3 else 'NOT CONFIRMED'}")
    # H-E4
    a4, b4 = pooled(loss, "v4_ind", [0.0]), pooled(loss, "v4", [0.0])
    p4 = _p(a4, b4, "less"); he4 = p4 < 0.05
    R.append(f"- H-E4 at pi = 0, v4_ind < v4: {np.mean(a4):.1f} vs {np.mean(b4):.1f} ({100 * (np.mean(a4) / np.mean(b4) - 1):+.1f}%), "
             f"p = {p4:.2g} -> {'CONFIRMED' if he4 else 'NOT CONFIRMED'}")
    # H-E5
    m5 = pooled(loss, "v4_match", [0.5, 0.8])
    p5a, p5b = _p(m5, pooled(loss, "v4", [0.5, 0.8]), "less"), _p(m5, pooled(loss, "v4_ind", [0.5, 0.8]), "less")
    he5 = p5a < 0.05 and p5b < 0.05
    R.append(f"- H-E5 at pi in {{0.5, 0.8}}, v4_match below v4 and v4_ind: {np.mean(m5):.1f} vs {np.mean(pooled(loss, 'v4', [0.5, 0.8])):.1f} "
             f"(p = {p5a:.2g}) and {np.mean(pooled(loss, 'v4_ind', [0.5, 0.8])):.1f} (p = {p5b:.2g}) -> {'CONFIRMED' if he5 else 'NOT CONFIRMED'}")
    # H-E6 (Holm over the three baselines)
    m6 = pooled(loss, "v4_match", PIS)
    ps = {b: _p(m6, pooled(loss, b, PIS), "less") for b in ("b9_vrr", "b10_pb", "b11_btm")}
    order = sorted(ps, key=ps.get); holm, ok6 = {}, True
    for i, b in enumerate(order):
        holm[b] = ps[b] < 0.05 / (3 - i)
        if not holm[b]:
            ok6 = False
            for b2 in order[i:]:
                holm[b2] = False
            break
    eff = {b: np.mean(m6) <= 0.95 * np.mean(pooled(loss, b, PIS)) for b in ps}
    he6 = all(holm.values()) and all(eff.values())
    R.append(f"- H-E6 f > 0, all pi: v4_match ({np.mean(m6):.1f}) below each literature baseline by >= 5% (Holm): " +
             "; ".join(f"{b} {np.mean(pooled(loss, b, PIS)):.1f} (p = {ps[b]:.2g}, Holm {'ok' if holm[b] else 'fail'}, 5% {'ok' if eff[b] else 'fail'})" for b in ps) +
             f" -> {'CONFIRMED' if he6 else 'NOT CONFIRMED'}")
    # H-E7
    z = np.mean(loss("v4_match", 0.0, 1.0)); zb = min(np.mean(loss(b, 0.0, 1.0)) for b in ps)
    he7 = z <= 1.02 * zb
    R.append(f"- H-E7 f = 0: v4_match {z:.1f} within 2% of the best literature baseline {zb:.1f} -> {'CONFIRMED' if he7 else 'NOT CONFIRMED'}")
    # H-E8
    a8, b8 = pooled(delta, "b9_vrr", [1.0]), pooled(delta, "always", [1.0])
    p8a = _p(a8, b8, "greater")
    c8, e8 = pooled(delta, "b9_vrr", [0.0]), pooled(delta, "always", [0.0])
    p8b = _p(c8, e8, "less")
    R.append(f"- H-E8a pi = 1: re-verification raises the false-alarm cost (B9 {np.mean(a8):.1f} vs always {np.mean(b8):.1f}), p = {p8a:.2g} -> "
             f"{'CONFIRMED' if p8a < 0.05 else 'NOT CONFIRMED'}")
    R.append(f"- H-E8b pi = 0: re-verification lowers the false-alarm cost (B9 {np.mean(c8):.1f} vs always {np.mean(e8):.1f}), p = {p8b:.2g} -> "
             f"{'CONFIRMED' if p8b < 0.05 else 'NOT CONFIRMED'}")

    L += R + ["", "## Per drop at f = 0.15 (mean loss)", "", "| drop | pi | " + " | ".join(S) + " |", "|---|---|" + "---|" * len(S)]
    for d in DROPS:
        for pi in (0.8, 1.0):
            ks = [k for k in keys if k[0] == d]
            L.append(f"| {int(d * 100)}% | {pi:g} | " + " | ".join(f"{np.mean([by[(s, 0.15, pi)][k]['loss'] for k in ks]):.1f}" for s in S) + " |")
    open(os.path.join(out, "report.md"), "w").write("\n".join(L)); print("\n".join(L)); print("Saved to", out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("dev", "confirm"))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--tuned", default=None)
    a = ap.parse_args(argv)
    {"dev": cmd_dev, "confirm": cmd_confirm}[a.cmd](a)


if __name__ == "__main__":
    main()
