"""Core 2x: the three published baselines given the rule's cross-check. See preregistration/PREREGISTRATION_core2x.md.

Same simulator design, conditions and tuned baseline parameters as Core 2 (ereplan/core2_exp.py, re-run with the
corrected criterion as experiment 'core2' of run_corrected_suite.py), on fresh seeds.

Usage:  python experiments/run_core2x.py dev       # seeds 9690-9691, pipeline check (not results)
        python experiments/run_core2x.py confirm   # seeds 9700-9719, run once
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import os
os.environ["EREPLAN_NETPV"] = "1"                         # the corrected check criterion, as in every reported result
import argparse, json, time
import numpy as np
from multiprocessing import Pool
from ereplan import crosscheck, outside_xcheck  # noqa: F401  (registers B13x-B15x)
from ereplan import core2_exp as c2
from ereplan.v5_exp import STRATS as V5_STRATS, _p, _boot_ci

SEEDS = {"dev": tuple(range(9690, 9692)), "confirm": tuple(range(9700, 9720))}
BASE = {"ssv": "B13_ssv", "rdecusum": "B14_rdecusum", "glrklucb": "B15_glrklucb"}
XNAME = {"ssv": "B13x_ssv", "rdecusum": "B14x_rdecusum", "glrklucb": "B15x_glrklucb"}


def strategies():
    tuned = json.load(open(c2.TUNED_FILE))
    S = {"v5": V5_STRATS["v5"]}
    for b in BASE:
        S[b] = (BASE[b], tuned[b], "true")
        S[b + "_x"] = (XNAME[b], tuned[b], "true")
    return S


def holm(ps):
    order = sorted(ps, key=ps.get); ok, stop = {}, False
    for i, h in enumerate(order):
        ok[h] = (not stop) and ps[h] < 0.05 / (len(order) - i); stop = stop or not ok[h]
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=tuple(SEEDS))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    assert crosscheck.NETPV, "the corrected criterion is not switched on"
    seeds, S = SEEDS[a.mode], strategies()
    jobs = [(k, *S[k], c, sd) for k in S for c in c2._conds() for sd in seeds]
    t0 = time.time()
    with Pool(a.procs) as pool:
        rows = pool.map(c2._job, jobs, chunksize=8)
    by = {}
    for r in rows:
        by.setdefault(r["strategy"], []).append(r)
    sm = lambda k: np.array([np.mean([r["loss"] for r in by[k] if r["seed"] == sd]) for sd in seeds])
    g = lambda k, fld: float(np.mean([r[fld] for r in by[k]]))
    L = [f"# Core 2x: published baselines with the cross-check ({a.mode}; PREREGISTRATION_core2x.md)", "",
         f"Seeds {seeds[0]}-{seeds[-1]}; {len(rows)} runs; {time.time() - t0:.0f} s. Unit: the seed (mean over 64 conditions). "
         "EREPLAN_NETPV=1.", "",
         "| Strategy | total loss | spend | wrong kept | failed tasks | checks/task | cross-checks/task | switches/run |",
         "|---|---|---|---|---|---|---|---|"]
    for k in S:
        L.append(f"| {k} | {g(k, 'loss'):.1f} | {g(k, 'spend'):.1f} | {g(k, 'leak_rate'):.1%} | {g(k, 'fail_rate'):.1%} | "
                 f"{g(k, 'checks'):.2f} | {g(k, 'crosschecks'):.2f} | {g(k, 'switches'):.1f} |")

    def line(h, x, y, xn, yn, p, ok):
        lo, hi = _boot_ci(x, y)
        return (f"- {h} {xn} < {yn}: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%, 95% CI "
                f"{lo:+.1f}% to {hi:+.1f}%), Wilcoxon p = {p:.2g}" + ("" if ok is None else
                f", Holm {'ok' if ok else 'fail'} -> {'CONFIRMED' if ok else 'NOT CONFIRMED'}"))

    hyp = {f"H-X{i}": ("v5", b + "_x") for i, b in enumerate(BASE, 1)}
    ps = {h: _p(sm(x), sm(y)) for h, (x, y) in hyp.items()}
    ok = holm(ps)
    L += ["", "## Pre-registered hypotheses (one-sided Wilcoxon over seeds, Holm across H-X1 to H-X3)", ""]
    L += [line(h, sm(x), sm(y), x, y, ps[h], ok[h]) for h, (x, y) in hyp.items()]
    L += ["", "## Descriptive: what the cross-check changes for each baseline", ""]
    L += [line(f"D{i}", sm(b + "_x"), sm(b), b + "_x", b, _p(sm(b + "_x"), sm(b)), None) for i, b in enumerate(BASE, 1)]
    L += [line(f"D{i + 3}", sm("v5"), sm(b), "v5", b, _p(sm("v5"), sm(b)), None) for i, b in enumerate(BASE, 1)]
    out = os.path.join("results", f"core2x_{a.mode}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L)); print("Saved to", out)


if __name__ == "__main__":
    main()
