"""Rule v5 pilot (27 October 2026): learning the checker without labels, and cross-checking flagged steps.
See PREREGISTRATION_v5.md.

Usage:  python -m ereplan.v5_exp dev        # smoke test on development seeds 1600-1605 (no tuning)
        python -m ereplan.v5_exp confirm    # pre-registered test, seeds 1700-1719
"""
import argparse, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon

from .config import Setting
from .runner import run
from . import rule_rho  # noqa: F401  (registers Rule_v5_rho)

DROPS, QS, LEAKS, FS, PIS = (0.95, 0.85, 0.75, 0.60), (0.8, 0.95), (1.0, 3.0), (0.05, 0.15), (0.0, 1.0)
TEST_SEEDS, DEV_SEEDS = tuple(range(1700, 1720)), tuple(range(1600, 1606))
SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
V4 = dict(SESSION, q_prior_strength=3.0)
# name, params, what the strategy is TOLD: "true" (labelled calibration), "none" (no calibration), "wrong"
STRATS = {
    "never": ("B2_never", dict(window=30), "true"),
    "always": ("B1_always", dict(window=30), "true"),
    "cusum": ("B4_cusum", dict(h=6, p1=0.8), "true"),
    "v4": ("Rule_v4_fa", dict(V4), "true"),            # pre-registered rule v4: told q and f, retries a flagged step
    "v4_nocal": ("Rule_v4_fa", dict(V4), "none"),      # rule v4 without calibration: assumes f = 0, q prior mean 0.5
    "v4_miscal": ("Rule_v4_fa", dict(V4), "wrong"),    # rule v4 told wrong values: q - 0.15, f / 2
    "always_x": ("B12_always_x", dict(window=30), "true"),   # reviewers' cross-check baseline
    "v5_told": ("Rule_v5_told", dict(SESSION), "true"),       # ablation: cross-check, but told q and f
    "v5": ("Rule_v5_x", dict(SESSION), "none"),               # rule v5: cross-check, learns q and f, no labels
    "v5_rho": ("Rule_v5_rho", dict(SESSION), "none"),         # rule v4+rho (31 Oct, renamed 6 Nov): cross-check that also learns the loud share rho (FR20)
    "v5_rho_noaudit": ("Rule_v5_rho_noaudit", dict(SESSION), "none"),  # development variant: learns rho, no extra audits
}


def setting(q, lm, f, pi, told):
    s = Setting().with_(q_true=q, q_assumed=q, check_frac=0.15, leak_mult=lm, false_alarm=f, fa_persistence=pi)
    if told == "none":
        s = s.with_(q_assumed=0.5, fa_assumed=0.0)
    elif told == "wrong":
        s = s.with_(q_assumed=q - 0.15, fa_assumed=f / 2)
    return s


def _job(a):
    key, drop, q, lm, f, pi, seed = a
    name, params, told = STRATS[key]
    r = run(name, dict(params), setting(q, lm, f, pi, told), f"drop_{drop:.2f}", seed)
    return dict(strategy=key, drop=drop, q=q, leak_mult=lm, f=f, pi=pi, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"],
                crosschecks=r["crosschecks_per_task"], fa_resolved=r["fa_resolved_per_task"],
                leak_cost=r["leak_cost_per_task"], fail_cost=r["fail_cost_per_task"],
                spend=r["tool_check_spend_per_task"] + r["switch_spend_per_task"],
                f_hat=r.get("f_hat"), q_hat=r.get("q_hat_cm"))


def jobs_for(seeds, keys=None):
    keys = keys or list(STRATS)
    return [(k, d, q, lm, f, pi, sd) for k in keys
            for d, q, lm, f, pi, sd in itertools.product(DROPS, QS, LEAKS, FS, PIS, seeds)]


def execute(seeds, procs):
    with Pool(procs) as pool:
        return pool.map(_job, jobs_for(seeds), chunksize=8)


def _p(x, y, alt="less"):
    x, y = np.asarray(x), np.asarray(y)
    if np.allclose(x, y):
        return 1.0
    return float(wilcoxon(x, y, alternative=alt).pvalue)


def _boot_ci(x, y, n=10000, seed=0):
    """95% bootstrap CI of 100 * (mean(x) / mean(y) - 1) over seeds (paired)."""
    x, y = np.asarray(x), np.asarray(y)
    r = np.random.default_rng(seed)
    idx = r.integers(0, len(x), (n, len(x)))
    d = 100 * (x[idx].mean(axis=1) / y[idx].mean(axis=1) - 1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def report(rows, seeds, title, secs):
    S = list(STRATS)
    by = {}
    for r in rows:
        by.setdefault(r["strategy"], []).append(r)

    def seed_means(k, field="loss", filt=lambda r: True):
        out = []
        for sd in seeds:
            v = [r[field] for r in by[k] if r["seed"] == sd and filt(r)]
            out.append(float(np.mean(v)))
        return np.array(out)

    L = [f"# {title}", "", f"Seeds {seeds[0]}-{seeds[-1]}; {len(rows)} runs; {secs:.0f} s. "
         "Unit of analysis: the seed (mean over the 64 conditions of drop x q x leak x f x pi). "
         "Metric: total loss per task (spend + leak loss x leaks + one task cost x failed tasks).", "",
         "## Mean outcomes per strategy", "",
         "| Strategy | told | total loss | spend | leak rate | failed tasks | checks/task | cross-checks/task |",
         "|---|---|---|---|---|---|---|---|"]
    for k in S:
        rr = by[k]
        L.append(f"| {k} | {STRATS[k][2]} | {np.mean([r['loss'] for r in rr]):.1f} | {np.mean([r['spend'] for r in rr]):.1f} | "
                 f"{np.mean([r['leak_rate'] for r in rr]):.1%} | {np.mean([r['fail_rate'] for r in rr]):.1%} | "
                 f"{np.mean([r['checks'] for r in rr]):.2f} | {np.mean([r['crosschecks'] for r in rr]):.2f} |")
    L += ["", "## By wrong-answer cost (leak weight) and persistence (mean total loss)", "",
          "| Strategy | leak 1 | leak 3 | pi = 0 | pi = 1 |", "|---|---|---|---|---|"]
    for k in S:
        g = lambda fn: np.mean([r["loss"] for r in by[k] if fn(r)])
        L.append(f"| {k} | {g(lambda r: r['leak_mult'] == 1.0):.1f} | {g(lambda r: r['leak_mult'] == 3.0):.1f} | "
                 f"{g(lambda r: r['pi'] == 0.0):.1f} | {g(lambda r: r['pi'] == 1.0):.1f} |")
    L += ["", "## By degradation level (mean total loss)", "", "| Strategy | " + " | ".join(f"{int(d * 100)}%" for d in DROPS) + " |",
          "|---|" + "---|" * len(DROPS)]
    for k in S:
        L.append(f"| {k} | " + " | ".join(f"{np.mean([r['loss'] for r in by[k] if r['drop'] == d]):.1f}" for d in DROPS) + " |")

    v5 = seed_means("v5")
    R = ["", "## Pre-registered hypotheses (PREREGISTRATION_v5.md)"]
    prim = {}
    for hid, other, margin in (("H-V1", "v4", 0.03), ("H-V2", "v4_nocal", 0.05), ("H-V3", "always_x", 0.0)):
        o = seed_means(other)
        p = _p(v5, o)
        lo, hi = _boot_ci(v5, o)
        eff = v5.mean() <= (1 - margin) * o.mean()
        prim[hid] = (p, eff, other, o.mean(), lo, hi, margin)
    order = sorted(prim, key=lambda h: prim[h][0]); holm = {}
    stop = False
    for i, h in enumerate(order):
        holm[h] = (not stop) and prim[h][0] < 0.05 / (3 - i)
        stop = stop or not holm[h]
    for h in ("H-V1", "H-V2", "H-V3"):
        p, eff, other, om, lo, hi, margin = prim[h]
        ok = holm[h] and eff
        R.append(f"- {h} v5 below {other} by >= {margin:.0%}: {v5.mean():.1f} vs {om:.1f} ({100 * (v5.mean() / om - 1):+.1f}%, "
                 f"95% CI {lo:+.1f}% to {hi:+.1f}%), Wilcoxon p = {p:.2g} over {len(seeds)} seeds, Holm {'ok' if holm[h] else 'fail'} "
                 f"-> {'CONFIRMED' if ok else 'NOT CONFIRMED'}")
    told = seed_means("v5_told")
    lo, hi = _boot_ci(v5, told)
    R.append(f"- H-V4 v5 (no labels) within 3% of v5_told (told q and f): {v5.mean():.1f} vs {told.mean():.1f} "
             f"({100 * (v5.mean() / told.mean() - 1):+.1f}%, 95% CI upper {hi:+.1f}%) -> {'CONFIRMED' if hi <= 3.0 else 'NOT CONFIRMED'}")
    d5 = seed_means("v5", filt=lambda r: r["pi"] == 1.0) - seed_means("v5", filt=lambda r: r["pi"] == 0.0)
    d4 = seed_means("v4", filt=lambda r: r["pi"] == 1.0) - seed_means("v4", filt=lambda r: r["pi"] == 0.0)
    rel5 = 100 * abs(d5.mean()) / v5.mean()
    p6 = _p(d5, d4)
    R.append(f"- H-V5 persistence barely matters for v5: loss(pi = 1) - loss(pi = 0) = {d5.mean():+.2f} ({rel5:.1f}% of its loss; need <= 2%), "
             f"vs v4 {d4.mean():+.2f} (v5 smaller: p = {p6:.2g}) -> {'CONFIRMED' if rel5 <= 2.0 and p6 < 0.05 else 'NOT CONFIRMED'}")
    fe = [abs(r["f_hat"] - r["f"]) for r in by["v5"] if r["f_hat"] is not None]
    qe = [abs(r["q_hat"] - r["q"]) for r in by["v5"] if r["q_hat"] is not None]
    R.append(f"- H-V6 v5 learns f without labels: median |f_hat - f| at the end of a run = {np.median(fe):.3f} (need <= 0.03) -> "
             f"{'CONFIRMED' if np.median(fe) <= 0.03 else 'NOT CONFIRMED'}. Descriptive: median |q_hat - q| = {np.median(qe):.3f}")
    mis = seed_means("v4_miscal")
    p7 = _p(v5, mis)
    R.append(f"- H-V7 v5 below v4 told wrong values: {v5.mean():.1f} vs {mis.mean():.1f} ({100 * (v5.mean() / mis.mean() - 1):+.1f}%), "
             f"p = {p7:.2g} -> {'CONFIRMED' if p7 < 0.05 else 'NOT CONFIRMED'}")
    # descriptive decomposition
    R += ["", "## Where the difference comes from (descriptive)",
          f"- Cross-check policy (v5_told vs v4, both told q and f): {told.mean():.1f} vs {seed_means('v4').mean():.1f}",
          f"- Learning instead of being told (v5 vs v5_told): {v5.mean():.1f} vs {told.mean():.1f}"]
    return "\n".join(L + R)


STRESS_SEEDS, NOISES = tuple(range(1720, 1730)), (0.0, 0.1, 0.2)


def _job_stress(a):
    key, drop, lm, f, e, seed = a
    name, params, told = STRATS[key]
    s = setting(0.95, lm, f, 1.0, told).with_(xc_noise=e)
    r = run(name, dict(params), s, f"drop_{drop:.2f}", seed)
    return dict(strategy=key, drop=drop, leak_mult=lm, f=f, e=e, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], f_hat=r.get("f_hat"))


def stress(procs):
    """Part C: the cross-check comparison itself is wrong with probability e (fuzzy answers)."""
    keys = ("v4", "always_x", "v5")
    jobs = [(k, d, lm, f, e, sd) for k in keys for d, lm, f, e, sd in
            itertools.product((0.85, 0.75), (1.0, 3.0), FS, NOISES, STRESS_SEEDS) if not (k == "v4" and e > 0)]
    t0 = time.time()
    with Pool(procs) as pool:
        rows = pool.map(_job_stress, jobs, chunksize=4)
    extra = []
    for r in rows:                                     # v4 never cross-checks: its result does not depend on e
        if r["strategy"] == "v4":
            for e in NOISES[1:]:
                extra.append(dict(r, e=e, copied=True))
    rows += extra
    sm = lambda k, e: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["e"] == e and r["seed"] == sd])
                                for sd in STRESS_SEEDS])
    L = ["# Part C: cross-check comparisons that are sometimes wrong (pre-registered stress test)", "",
         f"Seeds {STRESS_SEEDS[0]}-{STRESS_SEEDS[-1]}; q 0.95, pi 1, drop {{85, 75}}%, leak {{1, 3}}, f {{0.05, 0.15}}; {time.time() - t0:.0f} s.", "",
         "| e (comparison error) | v4 | always_x | v5 | v5 vs v4 | v5 median learned f |", "|---|---|---|---|---|---|"]
    for e in NOISES:
        v5, v4, ax = sm("v5", e), sm("v4", e), sm("always_x", e)
        fh = np.median([r["f_hat"] for r in rows if r["strategy"] == "v5" and r["e"] == e])
        L.append(f"| {e:g} | {v4.mean():.1f} | {ax.mean():.1f} | {v5.mean():.1f} | {100 * (v5.mean() / v4.mean() - 1):+.1f}% | {fh:.3f} |")
    v5, v4 = sm("v5", 0.1), sm("v4", 0.1)
    p = _p(v5, v4)
    L += ["", f"- H-C1 at e = 0.1, v5 below v4: {v5.mean():.1f} vs {v4.mean():.1f}, p = {p:.2g} over 10 seeds -> "
          f"{'CONFIRMED' if p < 0.05 else 'NOT CONFIRMED'}"]
    out = os.path.join("results", f"v5_stress_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L)); print("\n".join(L)); print("Saved to", out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("dev", "confirm", "stress"))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args(argv)
    if a.cmd == "stress":
        return stress(a.procs)
    seeds = DEV_SEEDS if a.cmd == "dev" else TEST_SEEDS
    t0 = time.time()
    rows = execute(seeds, a.procs)
    out = os.path.join("results", f"v5_{a.cmd}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    title = ("Rule v5 pilot: development smoke test (not a test of the hypotheses)" if a.cmd == "dev"
             else "Rule v5 pilot: pre-registered test")
    rep = report(rows, list(seeds), title, time.time() - t0)
    open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main()
