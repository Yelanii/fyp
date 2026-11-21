"""Prior-fix test, part 3: CostBench routes with the error rates of the four real checkers. See PREREGISTRATION_priorfix.md.

Same design as FR11 (run_fr11.py: CostBench task routes and prices, verdicts drawn at the measured rates of four real
checkers, f grid [0, 0.95]), with four strategies: the rule as evaluated (v5), the rule with the matched f prior
(v5_fix), the same rule told q and f, and the retrying rule told q and f (v4). On this grid the default prior's mean
for f is 0.33 instead of the stated 0.1.

Usage:  python run_priorfix_cb.py dev       # seeds 1990-1991 (pipeline check, not results)
        python run_priorfix_cb.py confirm   # seeds 9500-9517, run once
"""
import os, sys
os.environ["EREPLAN_NETPV"] = "1"
os.environ["EREPLAN_FMAX"] = "0.95"          # as in FR11: the grid must reach the FreshQA judges' f > 0.5
import itertools, json, time
import numpy as np
from multiprocessing import Pool
from scipy.stats import wilcoxon
from ereplan import costbench_v5 as cb
from ereplan.crosscheck import CheckerMemory, FMAX

PROFILES = {"qwen2.5:1.5b": (0.981, 0.143, 1.0), "qwen2.5:3b": (0.990, 0.050, 1.0),
            "phi4-mini": (0.807, 0.556, 1.0), "llama3.1:8b": (0.759, 0.516, 1.0)}     # as in run_fr11.py
DROPS, LEAKS, GAPS, FRACS = (0.95, 0.85, 0.75, 0.60), (1.0, 3.0), (0.0, 0.20), (0.05, 0.15)
SEEDS = {"dev": (1990, 1991), "confirm": tuple(range(9500, 9518))}


class RuleV5FixCB(cb.RuleV5CB):
    """The rule as evaluated on CostBench, with a weak f prior whose mean really is 0.1."""
    def __init__(self, world, seed):
        super().__init__(world, seed)
        self.cm = CheckerMemory(cb.RHO, f_ab=(1.0, FMAX / 0.1 - 1.0))
        self.est = cb.JointEstimatorV5(self.window, cb.RHO, cb.P_OK, 20.0, self.cm)


cb.STRATS = {"v5": cb.RuleV5CB, "v5_fix": RuleV5FixCB, "v5_told": cb.RuleV5ToldCB, "v4": cb.RuleV4CB}


def job(a):
    prof, drop, lm, gap, cf, seed = a
    q, f, pi = PROFILES[prof]
    return [dict(r, profile=prof, check_frac=cf) for r in cb._job((drop, q, f, pi, lm, gap, seed, cf))]


def _boot(x, y, n=10000, seed=0):
    idx = np.random.default_rng(seed).integers(0, len(x), (n, len(x)))
    d = 100 * (x[idx].mean(axis=1) / y[idx].mean(axis=1) - 1)
    return np.percentile(d, 2.5), np.percentile(d, 97.5)


def main(which):
    seeds = SEEDS[which]
    keys = list(itertools.product(PROFILES, DROPS, LEAKS, GAPS, FRACS, seeds))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = [r for rs in pool.imap_unordered(job, keys, chunksize=4) for r in rs]
    sm = lambda k: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == s]) for s in seeds])
    fh = lambda r: r.get("f_hat")
    LOW, HIGH = ("qwen2.5:1.5b", "qwen2.5:3b"), ("phi4-mini", "llama3.1:8b")
    bias = lambda k, grp: np.array([np.mean([abs(np.median([fh(r) - r["f"] for r in rows if r["strategy"] == k and r["seed"] == s
                                                             and r["profile"] == pr and fh(r) is not None])) for pr in grp]) for s in seeds])
    L = [f"# Prior-fix test, CostBench with real-checker rates ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(keys) // len(seeds)} conditions per seed; {len(rows)} runs; {time.time() - t0:.0f} s. f grid [0, {FMAX}].", "",
         "| Strategy | total loss | checks/task | median learned f - true f, by checker profile |", "|---|---|---|---|"]
    for k in cb.STRATS:
        R = [r for r in rows if r["strategy"] == k]
        per = "; ".join(f"{p}: {np.median([fh(r) - r['f'] for r in R if r['profile'] == p and fh(r) is not None]):+.3f}"
                        for p in PROFILES) if any(fh(r) is not None for r in R) else "-"
        L.append(f"| {k} | {sm(k).mean():.1f} | {np.mean([r['checks'] for r in R]):.2f} | {per} |")
    wl = lambda x, y, alt: 1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative=alt).pvalue)
    pa = wl(bias("v5_fix", LOW), bias("v5", LOW), "less")
    pb = wl(bias("v5_fix", HIGH), bias("v5", HIGH), "greater")
    lo, hi = _boot(sm("v5_fix"), sm("v5"))
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_priorfix.md)", "",
          f"- H-F6a checkers with low f (Qwen): the fixed prior LOWERS the bias of the learned f: {bias('v5_fix', LOW).mean():.3f} vs "
          f"{bias('v5', LOW).mean():.3f}, one-sided Wilcoxon p = {pa:.2g} -> **{'CONFIRMED' if pa < 0.05 else 'NOT CONFIRMED'}**",
          f"- H-F6b judges with high f (Phi-4 Mini, Llama 3.1 8B): the fixed prior RAISES the bias of the learned f (shrinkage towards "
          f"the prior mean): {bias('v5_fix', HIGH).mean():.3f} vs {bias('v5', HIGH).mean():.3f}, one-sided Wilcoxon p = {pb:.2g} -> "
          f"**{'CONFIRMED' if pb < 0.05 else 'NOT CONFIRMED'}**",
          f"- H-F7 the fixed prior costs at most 1% loss: {sm('v5_fix').mean():.1f} vs {sm('v5').mean():.1f} "
          f"({100 * (sm('v5_fix').mean() / sm('v5').mean() - 1):+.2f}%, 95% CI {lo:+.2f}% to {hi:+.2f}%) -> **{'CONFIRMED' if hi <= 1 else 'NOT CONFIRMED'}**"]
    for k in ("v5_told", "v4"):
        lo, hi = _boot(sm("v5_fix"), sm(k))
        L.append(f"- Descriptive: v5_fix vs {k}: {sm('v5_fix').mean():.1f} vs {sm(k).mean():.1f} ({100 * (sm('v5_fix').mean() / sm(k).mean() - 1):+.2f}%, 95% CI {lo:+.2f}% to {hi:+.2f}%)")
    out = os.path.join("results", f"priorfix_cb_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
