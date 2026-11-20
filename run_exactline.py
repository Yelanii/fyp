"""Exact step-cost test. See PREREGISTRATION_exactline.md.
The evaluated rule prices a tool at c/p (+ wrong answers), as if a call were retried until it succeeds; in the
model only loud failures are retried. This run compares the evaluated rule with a variant that uses the exact step loss.
Usage:  python run_exactline.py dev        # development seeds 8000-8003
        python run_exactline.py confirm    # pre-registered test, seeds 9300-9319, run once
"""
import os
os.environ["EREPLAN_NETPV"] = "1"          # the evaluated rule is the corrected one (net protection value)
import itertools, json, sys, time
from multiprocessing import Pool
import numpy as np
from ereplan import v5_exp
from ereplan.runner import run

SEEDS = {"dev": tuple(range(8000, 8004)), "confirm": tuple(range(9300, 9320))}
STRATS = {k: v5_exp.STRATS[k] for k in ("never", "v4", "v5")}
STRATS["v5_exact"] = ("Rule_v5_exact", dict(v5_exp.SESSION), "none")
NAMES = {"never": "never check", "v4": "retrying rule told q, f", "v5": "rule as evaluated (c/p step cost)",
         "v5_exact": "rule with exact step cost"}


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
    same = np.mean([a["loss"] == b["loss"] for a, b in zip(sorted((r for r in rows if r["strategy"] == "v5"), key=lambda r: tuple(r[x] for x in ("drop", "q", "leak_mult", "f", "pi", "seed"))),
                                                             sorted((r for r in rows if r["strategy"] == "v5_exact"), key=lambda r: tuple(r[x] for x in ("drop", "q", "leak_mult", "f", "pi", "seed"))))])
    L = [f"# Exact step-cost test ({which})", "",
         f"Seeds {seeds[0]}-{seeds[-1]}; {len(jobs) // len(seeds) // len(STRATS)} conditions per seed; {len(rows)} runs; {time.time() - t0:.0f} s.",
         f"Runs in which the two rules gave exactly the same loss: {same:.1%}.", "",
         "| Strategy | total loss | wrong answers kept | failed tasks | checks/task |", "|---|---|---|---|---|"]
    for k in STRATS:
        L.append(f"| {NAMES[k]} | {sm(k).mean():.1f} | {g(k, 'leak_rate'):.1%} | {g(k, 'fail_rate'):.1%} | {g(k, 'checks'):.2f} |")
    L += ["", "## By wrong-answer cost and degradation level (total loss)", "",
          "| wrong-answer cost | tool A drops to | as evaluated | exact step cost | difference |", "|---|---|---|---|---|"]
    for lm, d in itertools.product(v5_exp.LEAKS, v5_exp.DROPS):
        flt = lambda r, lm=lm, d=d: r["leak_mult"] == lm and r["drop"] == d
        a, b = sm("v5", flt).mean(), sm("v5_exact", flt).mean()
        L.append(f"| {lm:g}x task | {d:.0%} | {a:.1f} | {b:.1f} | {100 * (b / a - 1):+.1f}% |")
    ex, v5, v4 = sm("v5_exact"), sm("v5"), sm("v4")
    lo1, hi1 = v5_exp._boot_ci(ex, v5); lo3, hi3 = v5_exp._boot_ci(ex, v4)
    p2 = v5_exp._p(ex, v5, "two-sided")
    pc = lambda x, y: 100 * (x.mean() / y.mean() - 1)
    L += ["", "## Pre-registered hypotheses", "",
          f"- H-E1 the approximation costs at most 1% (95% CI of exact vs evaluated within -1% to +1%): {ex.mean():.1f} vs {v5.mean():.1f} "
          f"({pc(ex, v5):+.2f}%, 95% CI {lo1:+.2f}% to {hi1:+.2f}%) -> **{'CONFIRMED' if lo1 >= -1 and hi1 <= 1 else 'NOT CONFIRMED'}**",
          f"- H-E2 (descriptive) two-sided Wilcoxon over {len(seeds)} seeds, exact vs evaluated: p = {p2:.2g}",
          f"- H-E3 the exact variant within +3% of the retrying rule told q and f (upper bound <= +3%): {ex.mean():.1f} vs {v4.mean():.1f} "
          f"({pc(ex, v4):+.1f}%, 95% CI {lo3:+.1f}% to {hi3:+.1f}%) -> **{'CONFIRMED' if hi3 <= 3 else 'NOT CONFIRMED'}**"]
    out = os.path.join("results", f"exactline_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
