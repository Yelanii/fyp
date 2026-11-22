"""Core 2: rules v4 and v5 against three recent outside methods (ereplan/outside_baselines.py).
See PREREGISTRATION_core2.md.

Usage:  python -m ereplan.core2_exp tune      # tune the outside baselines on development seeds 2400-2403
        python -m ereplan.core2_exp confirm   # pre-registered test on seeds 2410-2429 (uses the tuned choice)
"""
import argparse, itertools, json, os, sys, time
from multiprocessing import Pool
import numpy as np

from .runner import run
from . import outside_baselines  # noqa: F401  (registers B13-B15)
from .v5_exp import STRATS as V5_STRATS, setting, DROPS, QS, LEAKS, FS, PIS, _p, _boot_ci

DEV_SEEDS, TEST_SEEDS = tuple(range(2400, 2404)), tuple(range(2410, 2430))
TUNED_FILE = os.path.join("data", "processed", "core2_tuned.json")

GRIDS = {
    "ssv": ("B13_ssv", [dict(alpha=a, beta=b, qx=x, eta=0.05) for a, b, x in
                        itertools.product((0.02, 0.05, 0.1, 0.2), (0.02, 0.05, 0.1, 0.2), (0.02, 0.05, 0.1))]),
    "rdecusum": ("B14_rdecusum", [dict(A=A, mu=m, h=h, p1=p1) for A, m, h, p1 in
                                  itertools.product((3.0, 4.0, 6.0, 8.0), (0.02, 0.05, 0.1, 0.2, 0.5), (1.0, 2.0, 4.0),
                                                    (0.75, 0.85))]),
    "glrklucb": ("B15_glrklucb", [dict(alpha0=a, check_rate=c) for a, c in
                                  itertools.product((0.1, 0.3, 1.0), (0.05, 0.1, 0.2, 0.4))]),
}
# Round 2 (added after round 1, before any test seed): several round-1 choices sat at the edge of their grid, so
# the grids are extended past those edges. The final choice is the best of both rounds on the same dev seeds.
GRIDS2 = {
    "ssv": [dict(alpha=a, beta=0.1, qx=x, eta=e) for a, x, e in
            itertools.product((0.02, 0.2, 0.4), (0.0025, 0.005, 0.01, 0.02), (0.05, 0.2))],
    "rdecusum": [dict(A=A, mu=m, h=1.0, p1=p1) for A, m, p1 in
                 itertools.product((1.5, 2.0, 3.0), (0.0025, 0.005, 0.01, 0.02), (0.65, 0.75))],
    "glrklucb": [dict(alpha0=a, check_rate=c) for a, c in itertools.product((0.01, 0.03, 0.1), (0.4, 0.6, 0.8, 1.0))],
}
OURS = ("never", "always", "cusum", "v4", "v4_nocal", "always_x", "v5")
OUTSIDE = ("ssv", "rdecusum", "glrklucb")


def _conds():
    return list(itertools.product(DROPS, QS, LEAKS, FS, PIS))


def _job(a):
    key, name, params, told, cond, seed = a
    drop, q, lm, f, pi = cond
    r = run(name, dict(params), setting(q, lm, f, pi, told), f"drop_{drop:.2f}", seed)
    return dict(strategy=key, drop=drop, q=q, leak_mult=lm, f=f, pi=pi, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"],
                crosschecks=r["crosschecks_per_task"], switches=r["switches"],
                spend=r["tool_check_spend_per_task"] + r["switch_spend_per_task"])


def tune(procs):
    jobs = []
    for b, (name, grid) in GRIDS.items():
        for i, params in enumerate(grid):
            jobs += [(f"{b}#{i}", name, params, "true", c, sd) for c in _conds() for sd in DEV_SEEDS]
    jobs += [(k, *V5_STRATS[k], c, sd) for k in ("v4", "v5", "never") for c in _conds() for sd in DEV_SEEDS]
    t0 = time.time()
    with Pool(procs) as pool:
        rows = pool.map(_job, jobs, chunksize=16)
    mean = lambda k: float(np.mean([r["loss"] for r in rows if r["strategy"] == k]))
    tuned, L = {}, ["# Core 2 tuning of the outside baselines (development seeds 2400-2403)", "",
                    f"{len(rows)} runs; {time.time() - t0:.0f} s. Choice = lowest mean total loss over all 64 conditions.", ""]
    for b, (name, grid) in GRIDS.items():
        scores = sorted(((mean(f"{b}#{i}"), i) for i in range(len(grid))))
        best = scores[0][1]
        tuned[b] = grid[best]
        L += [f"## {name} ({len(grid)} settings)", "", "| rank | setting | mean loss |", "|---|---|---|"]
        L += [f"| {r + 1} | {grid[i]} | {m:.1f} |" for r, (m, i) in enumerate(scores[:5])]
        L += [f"| worst | {grid[scores[-1][1]]} | {scores[-1][0]:.1f} |", ""]
    L += ["## Reference on the same seeds (rules not tuned)", ""] + [f"- {k}: {mean(k):.1f}" for k in ("never", "v4", "v5")]
    os.makedirs(os.path.dirname(TUNED_FILE), exist_ok=True)
    json.dump(tuned, open(TUNED_FILE, "w"), indent=1)
    out = os.path.join("results", f"core2_tune_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out, "and", TUNED_FILE)


def tune2(procs):
    prev = json.load(open(TUNED_FILE))
    jobs = []
    for b, grid in GRIDS2.items():
        name = GRIDS[b][0]
        for i, params in enumerate(grid):
            jobs += [(f"{b}#{i}", name, params, "true", c, sd) for c in _conds() for sd in DEV_SEEDS]
        jobs += [(f"{b}#prev", name, prev[b], "true", c, sd) for c in _conds() for sd in DEV_SEEDS]
    t0 = time.time()
    with Pool(procs) as pool:
        rows = pool.map(_job, jobs, chunksize=16)
    mean = lambda k: float(np.mean([r["loss"] for r in rows if r["strategy"] == k]))
    L = ["# Core 2 tuning, round 2 (grids extended past round-1 edges; same development seeds)", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s.", ""]
    tuned = {}
    for b, grid in GRIDS2.items():
        scores = sorted([(mean(f"{b}#{i}"), i) for i in range(len(grid))])
        m_prev = mean(f"{b}#prev")
        if scores[0][0] < m_prev:
            tuned[b] = grid[scores[0][1]]
        else:
            tuned[b] = prev[b]
        L += [f"## {GRIDS[b][0]}", "", f"- round-1 choice {prev[b]}: {m_prev:.1f}",
              f"- best round-2 setting {grid[scores[0][1]]}: {scores[0][0]:.1f}",
              f"- worst round-2 setting {grid[scores[-1][1]]}: {scores[-1][0]:.1f}", f"- FINAL: {tuned[b]}", ""]
    json.dump(tuned, open(TUNED_FILE, "w"), indent=1)
    out = os.path.join("results", f"core2_tune2_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out, "and", TUNED_FILE)


def strategies():
    tuned = json.load(open(TUNED_FILE))
    S = {k: V5_STRATS[k] for k in OURS}
    for b in OUTSIDE:
        S[b] = (GRIDS[b][0], tuned[b], "true")
    return S


def confirm(procs):
    S = strategies()
    jobs = [(k, *S[k], c, sd) for k in S for c in _conds() for sd in TEST_SEEDS]
    t0 = time.time()
    with Pool(procs) as pool:
        rows = pool.map(_job, jobs, chunksize=8)
    secs = time.time() - t0
    by = {}
    for r in rows:
        by.setdefault(r["strategy"], []).append(r)
    sm = lambda k: np.array([np.mean([r["loss"] for r in by[k] if r["seed"] == sd]) for sd in TEST_SEEDS])
    g = lambda k, fld, fn=lambda r: True: float(np.mean([r[fld] for r in by[k] if fn(r)]))
    L = ["# Core 2: rules v4 and v5 against outside methods (confirmatory, PREREGISTRATION_core2.md)", "",
         f"Seeds {TEST_SEEDS[0]}-{TEST_SEEDS[-1]}; {len(rows)} runs; {secs:.0f} s. Unit: the seed (mean over 64 conditions).", "",
         "| Strategy | told | total loss | spend | leak rate | failed tasks | checks/task | cross-checks/task | switches/run |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k in S:
        L.append(f"| {k} | {S[k][2]} | {g(k, 'loss'):.1f} | {g(k, 'spend'):.1f} | {g(k, 'leak_rate'):.1%} | "
                 f"{g(k, 'fail_rate'):.1%} | {g(k, 'checks'):.2f} | {g(k, 'crosschecks'):.2f} | {g(k, 'switches'):.1f} |")
    L += ["", "| Strategy | pi = 0 | pi = 1 | f 0.05 | f 0.15 | leak 1 | leak 3 | " + " | ".join(f"drop {int(d * 100)}%" for d in DROPS) + " |",
          "|---|" + "---|" * (6 + len(DROPS))]
    for k in S:
        cells = [g(k, "loss", lambda r: r["pi"] == 0.0), g(k, "loss", lambda r: r["pi"] == 1.0),
                 g(k, "loss", lambda r: r["f"] == 0.05), g(k, "loss", lambda r: r["f"] == 0.15),
                 g(k, "loss", lambda r: r["leak_mult"] == 1.0), g(k, "loss", lambda r: r["leak_mult"] == 3.0)]
        cells += [g(k, "loss", lambda r, d=d: r["drop"] == d) for d in DROPS]
        L.append(f"| {k} | " + " | ".join(f"{c:.1f}" for c in cells) + " |")

    def test(ours, others, label):
        x = sm(ours)
        res = {}
        for o in others:
            y = sm(o)
            res[o] = (_p(x, y), *_boot_ci(x, y), x.mean(), y.mean())
        order = sorted(res, key=lambda o: res[o][0]); holm, stop = {}, False
        for i, o in enumerate(order):
            holm[o] = (not stop) and res[o][0] < 0.05 / (len(order) - i)
            stop = stop or not holm[o]
        out = []
        for n, o in enumerate(others, 1):
            p, lo, hi, xm, ym = res[o]
            out.append(f"- {label}{n} {ours} < {o}: {xm:.1f} vs {ym:.1f} ({100 * (xm / ym - 1):+.1f}%, 95% CI {lo:+.1f}% to "
                       f"{hi:+.1f}%), Wilcoxon p = {p:.2g}, Holm {'ok' if holm[o] else 'fail'} -> "
                       f"{'CONFIRMED' if holm[o] else 'NOT CONFIRMED'}")
        return out

    L += ["", "## Pre-registered hypotheses", ""] + test("v5", OUTSIDE, "H-O") + test("v4", OUTSIDE, "H-O4.")
    out = os.path.join("results", f"core2_confirm_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("tune", "tune2", "confirm"))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    {"tune": tune, "tune2": tune2, "confirm": confirm}[a.mode](a.procs)
