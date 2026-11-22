"""Prior-fix test: does the false-alarm bias of the label-free rule come from its prior? See PREREGISTRATION_priorfix.md.

The rule's checker memory states a weak prior with mean 0.1 for the false-alarm rate f, but each Beta parameter is
floored at 1, which moves the prior mean to about 0.19 on the f grid [0, 0.5] and 0.33 on [0, 0.95]. With few
checks the posterior stays near the prior, which would explain why the learned f was too high on every testbed.
The variant v5_fix uses a weak prior whose mean really is 0.1 (Beta(1, FMAX/0.1 - 1) on f/FMAX). Nothing else changes.

Usage:  python experiments/run_priorfix.py sim dev | sim confirm     # simulator, seeds 1600-1601 | 9400-9419
        python experiments/run_priorfix.py live dev | live confirm   # cached D1 answers, seeds 7010-7014 | 7300-7319 (no model calls)
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import os, sys
os.environ["EREPLAN_NETPV"] = "1"          # the corrected check criterion, as in every result for the rule
os.environ["EREPLAN_FMAX"] = "0.5"         # the default f grid, as in the simulator studies and D1
import itertools, json, time
import numpy as np
from multiprocessing import Pool
from scipy.stats import wilcoxon

SIM_SEEDS = {"dev": (1600, 1601), "confirm": tuple(range(9400, 9420))}
LIVE_SEEDS = {"dev": tuple(range(7010, 7015)), "confirm": tuple(range(7300, 7320))}


def _boot(x, y, n=10000, seed=0):
    r = np.random.default_rng(seed)
    m = [100 * (x[ix].mean() / y[ix].mean() - 1) for ix in r.integers(0, len(x), (n, len(x)))]
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def _holm(ps):
    order = sorted(ps, key=ps.get); ok, stop = {}, False
    for j, h in enumerate(order):
        ok[h] = (not stop) and ps[h] < 0.05 / (len(order) - j); stop = stop or not ok[h]
    return ok


def _wil(x, y):
    return 1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative="less").pvalue)


# ----------------------------------------------------------------------------- simulator
def _sim_setup():
    from ereplan import v5_exp as v
    v.STRATS["v5_fix"] = ("Rule_v5_x", dict(v.SESSION, f_prior_matched=True), "none")
    return v


def _sim_job(a):
    return _sim_setup()._job(a)


def sim(which, procs=None):
    v = _sim_setup()
    seeds = SIM_SEEDS[which]; keys = ["v5", "v5_fix", "v5_told", "v4"]
    t0 = time.time()
    with Pool(procs or max(1, os.cpu_count() - 1)) as p:
        rows = p.map(_sim_job, v.jobs_for(seeds, keys), chunksize=4)
    sm = lambda k: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == s]) for s in seeds])
    fe = lambda k: np.array([abs(np.median([r["f_hat"] - r["f"] for r in rows if r["strategy"] == k and r["seed"] == s])) for s in seeds])
    L = [f"# Prior-fix test, simulator ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. 64 conditions per seed (label-free-rule grid).", "",
         "| Strategy | total loss | checks/task | wrong kept | median learned f - true f | median abs error of f |", "|---|---|---|---|---|---|"]
    for k in keys:
        R = [r for r in rows if r["strategy"] == k]
        e = [r["f_hat"] - r["f"] for r in R if r["f_hat"] is not None]
        L.append(f"| {k} | {sm(k).mean():.1f} | {np.mean([r['checks'] for r in R]):.2f} | {100 * np.mean([r['leak_rate'] for r in R]):.1f}% | "
                 + (f"{np.median(e):+.3f} | {np.median(np.abs(e)):.3f} |" if e else "- | - |"))
    lo, hi = _boot(sm("v5_fix"), sm("v5"))
    p1 = _wil(fe("v5_fix"), fe("v5"))
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_priorfix.md)", "",
          f"- H-F1 the fixed prior lowers the bias of the learned f (|median of learned f - true f| per seed): {fe('v5_fix').mean():.3f} vs {fe('v5').mean():.3f}, "
          f"one-sided Wilcoxon p = {p1:.2g} -> **{'CONFIRMED' if p1 < 0.05 else 'NOT CONFIRMED'}**",
          f"- H-F2 the fixed prior costs at most 1% loss: {sm('v5_fix').mean():.1f} vs {sm('v5').mean():.1f} "
          f"({100 * (sm('v5_fix').mean() / sm('v5').mean() - 1):+.2f}%, 95% CI {lo:+.2f}% to {hi:+.2f}%) -> **{'CONFIRMED' if hi <= 1 else 'NOT CONFIRMED'}**"]
    for k in ("v5_told", "v4"):
        lo, hi = _boot(sm("v5_fix"), sm(k))
        L.append(f"- Descriptive: v5_fix vs {k}: {sm('v5_fix').mean():.1f} vs {sm(k).mean():.1f} ({100 * (sm('v5_fix').mean() / sm(k).mean() - 1):+.2f}%, 95% CI {lo:+.2f}% to {hi:+.2f}%)")
    _save(f"priorfix_sim_{which}", rows, L)


# ----------------------------------------------------------------------------- live tools (cached D1 answers)
def live(which, table=None):
    from ereplan import agent_live as d
    from ereplan.v5_exp import SESSION
    d.STRATS["v5_fix"] = ("Rule_v5_x", dict(SESSION, f_prior_matched=True), "none")
    d.RNG_ALIAS["v5_fix"] = "v5"
    table = table or json.load(open(d.TABLE))
    seeds = LIVE_SEEDS[which]; keys = ["never", "cusum", "v4", "always_x", "v5_told", "v5", "v5_fix", "fix_B"]
    t0 = time.time()
    rows = [d.run_one(table, k, sd, pb, Lc) for k, sd, (Lc, pb) in itertools.product(keys, seeds, d.CONDS)]
    sm = lambda k: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == s]) for s in seeds])
    fe = lambda k: np.array([abs(np.median([r["f_hat"] - d.TOLD_F for r in rows if r["strategy"] == k and r["seed"] == s])) for s in seeds])
    L = [f"# Prior-fix test, live tools ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. Calibrated f (Study M) = {d.TOLD_F:.3f}.", "",
         "| Strategy | total loss | wrong kept | failed | checks/task | median learned f |", "|---|---|---|---|---|---|"]
    for k in keys:
        R = [r for r in rows if r["strategy"] == k]
        fh = [r["f_hat"] for r in R if r["f_hat"] is not None]
        L.append(f"| {k} | {sm(k).mean():.1f} | {100 * np.mean([r['wrong_rate'] for r in R]):.1f}% | {100 * np.mean([r['fail_rate'] for r in R]):.1f}% | "
                 f"{np.mean([r['checks_per_task'] for r in R]):.2f} | " + (f"{np.median(fh):.3f} |" if fh else "- |"))
    tests = {"H-F3 the fixed prior lowers the bias of the learned f (vs calibrated 0.046)": (fe("v5_fix"), fe("v5")),
             "H-F4 the fixed rule below the rule as evaluated": (sm("v5_fix"), sm("v5")),
             "H-F5 the fixed rule below never checking": (sm("v5_fix"), sm("never"))}
    ps = {h: _wil(x, y) for h, (x, y) in tests.items()}; ok = _holm(ps)
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_priorfix.md; Holm across H-F3 to H-F5)", ""]
    for h, (x, y) in tests.items():
        extra = "" if h.startswith("H-F3") else " (%+.1f%%, 95%% CI %+.1f%% to %+.1f%%)" % ((100 * (x.mean() / y.mean() - 1),) + _boot(x, y))
        L.append(f"- {h}: {x.mean():.3f} vs {y.mean():.3f}{extra}, one-sided Wilcoxon p = {ps[h]:.2g}, Holm {'ok' if ok[h] else 'fail'} "
                 f"-> **{'CONFIRMED' if ok[h] else 'NOT CONFIRMED'}**")
    for k in ("v5_told", "v4", "always_x", "cusum", "fix_B"):
        lo, hi = _boot(sm("v5_fix"), sm(k))
        L.append(f"- Descriptive: v5_fix vs {k}: {sm('v5_fix').mean():.1f} vs {sm(k).mean():.1f} ({100 * (sm('v5_fix').mean() / sm(k).mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%)")
    _save(f"priorfix_live_{which}", rows, L)


def _save(name, rows, L):
    out = os.path.join("results", f"{name}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", out)


if __name__ == "__main__":
    part, which = (sys.argv[1:3] + ["dev"])[:2] if len(sys.argv) > 1 else ("sim", "dev")
    sim(which) if part == "sim" else live(which)
