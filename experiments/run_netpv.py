"""Net protection value test. See PREREGISTRATION_netpv.md.
Does correcting the check criterion (rule v5 -> v5_net) change the loss?
Usage:  python experiments/run_netpv.py dev        # development seeds 8000-8003
        python experiments/run_netpv.py confirm    # pre-registered test, seeds 8100-8119, run once
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import itertools, json, os, sys, time
from multiprocessing import Pool
import numpy as np
from ereplan import v5_exp
from ereplan.runner import run

SEEDS = {"dev": tuple(range(8000, 8004)), "confirm": tuple(range(8100, 8120))}
STRATS = {k: v5_exp.STRATS[k] for k in ("never", "v4", "v5_told", "v5")}
STRATS["v5_net"] = ("Rule_v5_net", dict(v5_exp.SESSION), "none")     # the corrected rule, no labels
NAMES = {"never": "never check", "v4": "retrying rule told q, f", "v5_told": "rule v5 told q, f (gross PV)",
         "v5": "rule v5 (gross PV, as evaluated so far)", "v5_net": "rule v5 with net PV (corrected)"}


def job(a):
    key, d, q, lm, f, pi, sd = a
    name, params, told = STRATS[key]
    r = run(name, dict(params), v5_exp.setting(q, lm, f, pi, told), f"drop_{d:.2f}", sd)
    return dict(strategy=key, drop=d, q=q, leak_mult=lm, f=f, pi=pi, seed=sd, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"])


def main(which):
    seeds = SEEDS[which]
    jobs = [(k, d, q, lm, f, pi, sd) for k in STRATS for d, q, lm, f, pi, sd in
            itertools.product(v5_exp.DROPS, v5_exp.QS, v5_exp.LEAKS, v5_exp.FS, v5_exp.PIS, seeds)]
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(job, jobs, chunksize=8)
    sm = lambda k, flt=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and flt(r)]) for sd in seeds])
    g = lambda k, fld: np.mean([r[fld] for r in rows if r["strategy"] == k])
    L = [f"# Net protection value test ({which})", "",
         f"Seeds {seeds[0]}-{seeds[-1]}; {len(jobs) // len(seeds) // len(STRATS)} conditions per seed; {len(rows)} runs; {time.time() - t0:.0f} s.", "",
         "| Strategy | total loss | wrong answers kept | failed tasks | checks/task |", "|---|---|---|---|---|"]
    for k in STRATS:
        L.append(f"| {NAMES[k]} | {sm(k).mean():.1f} | {g(k, 'leak_rate'):.1%} | {g(k, 'fail_rate'):.1%} | {g(k, 'checks'):.2f} |")
    L += ["", "## By wrong-answer cost and degradation level (total loss)", "",
          "| wrong-answer cost | tool A drops to | v5 (gross) | v5_net (corrected) | difference |", "|---|---|---|---|---|"]
    for lm, d in itertools.product(v5_exp.LEAKS, v5_exp.DROPS):
        flt = lambda r, lm=lm, d=d: r["leak_mult"] == lm and r["drop"] == d
        a, b = sm("v5", flt).mean(), sm("v5_net", flt).mean()
        L.append(f"| {lm:g}x task | {d:.0%} | {a:.1f} | {b:.1f} | {100 * (b / a - 1):+.1f}% |")
    net, v5, v4 = sm("v5_net"), sm("v5"), sm("v4")
    lo1, hi1 = v5_exp._boot_ci(net, v5); p2 = v5_exp._p(net, v5); lo3, hi3 = v5_exp._boot_ci(net, v4)
    pc = lambda x, y: 100 * (x.mean() / y.mean() - 1)
    L += ["", "## Pre-registered hypotheses", "",
          f"- H-P1 corrected rule not worse than the evaluated rule (upper bound of 95% CI <= +1%): {net.mean():.1f} vs {v5.mean():.1f} "
          f"({pc(net, v5):+.1f}%, 95% CI {lo1:+.1f}% to {hi1:+.1f}%) -> **{'CONFIRMED' if hi1 <= 1 else 'NOT CONFIRMED'}**",
          f"- H-P2 corrected rule lower than the evaluated rule: Wilcoxon p = {p2:.2g} over {len(seeds)} seeds "
          f"-> **{'CONFIRMED' if p2 < 0.05 else 'NOT CONFIRMED'}**",
          f"- H-P3 corrected rule within +3% of the retrying rule told q and f (upper bound of 95% CI <= +3%): {net.mean():.1f} vs {v4.mean():.1f} "
          f"({pc(net, v4):+.1f}%, 95% CI {lo3:+.1f}% to {hi3:+.1f}%) -> **{'CONFIRMED' if hi3 <= 3 else 'NOT CONFIRMED'}**"]
    out = os.path.join("results", f"netpv_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
