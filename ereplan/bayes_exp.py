"""Part B of PREREGISTRATION_v5.md: how close do the rules come to the Bayes-optimal policy (small instance)?

Usage:  python -m ereplan.bayes_exp confirm      # seeds 1800-1819
"""
import argparse, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon

from .config import Setting, Tool
from .runner import run
from . import bayes_opt  # noqa: F401 (registers B13_bayes)

TOOLS = (Tool("A_cheap", 20.0, 1.0, 0.95, 0.95), Tool("B_mid", 24.0, 1.0, 0.95, 0.95))
DROPS, QS, LEAKS, FS = (0.95, 0.85, 0.75, 0.60), (0.8, 0.95), (5.0, 15.0), (0.0, 0.05, 0.15)
TEST_SEEDS = tuple(range(1820, 1840))
SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
STRATS = {
    "never": ("B2_never", dict(window=30), "true"),
    "always": ("B1_always", dict(window=30), "true"),
    "cusum": ("B4_cusum", dict(h=6, p1=0.8), "true"),
    "v4": ("Rule_v4_fa", dict(SESSION, q_prior_strength=3.0), "true"),
    "oracle_heur": ("B6_oracle", dict(), "true"),        # sees the true state but uses a simple check rule
    "bayes": ("B13_bayes", dict(), "true"),              # Bayes-optimal: sees what the rules see, told the model
    "v5": ("Rule_v5_x", dict(SESSION), "none"),          # extra action (cross-check): reported separately
}
SAME_ACTIONS = ("never", "always", "cusum", "v4")


def setting(q, lm, f, told):
    s = Setting(tools=TOOLS, steps_per_task=1, n_tasks=600, r_max=0).with_(
        q_true=q, q_assumed=q, check_frac=0.15, leak_mult=lm, false_alarm=f, fa_persistence=1.0)
    if told == "none":
        s = s.with_(q_assumed=0.5, fa_assumed=0.0)
    return s


def _job(a):
    key, drop, q, lm, f, seed = a
    name, params, told = STRATS[key]
    params = dict(params)
    if key == "bayes":
        params["p1"] = drop
    r = run(name, params, setting(q, lm, f, told), f"drop_{drop:.2f}", seed)
    return dict(strategy=key, drop=drop, q=q, leak_mult=lm, f=f, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("confirm",))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args(argv)
    seeds = TEST_SEEDS
    jobs = [(k, d, q, lm, f, sd) for k in STRATS for d, q, lm, f, sd in itertools.product(DROPS, QS, LEAKS, FS, seeds)]
    t0 = time.time()
    with Pool(a.procs) as pool:
        rows = pool.map(_job, jobs, chunksize=8)
    out = os.path.join("results", f"bayes_{a.cmd}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    by = {}
    for r in rows:
        by.setdefault(r["strategy"], []).append(r)
    sm = lambda k, filt=lambda r: True: np.array([np.mean([r["loss"] for r in by[k] if r["seed"] == sd and filt(r)]) for sd in seeds])
    L = ["# Part B: distance to the Bayes-optimal policy (small instance; pre-registered)", "",
         f"Seeds {seeds[0]}-{seeds[-1]}; {len(rows)} runs; {time.time() - t0:.0f} s. Two tools, single-step tasks, no retries; "
         "48 conditions (drop x q x leak x f). Unit: the seed. Metric: total loss per task.", "",
         "| Strategy | mean loss | regret vs Bayes | leak rate | failed tasks | checks/task |", "|---|---|---|---|---|---|"]
    bay = sm("bayes")
    for k in STRATS:
        x = sm(k)
        L.append(f"| {k} | {x.mean():.2f} | {100 * (x.mean() / bay.mean() - 1):+.1f}% | {np.mean([r['leak_rate'] for r in by[k]]):.1%} | "
                 f"{np.mean([r['fail_rate'] for r in by[k]]):.1%} | {np.mean([r['checks'] for r in by[k]]):.2f} |")
    L += ["", "## Regret of rule v4 vs Bayes-optimal, by condition (mean loss)", "",
          "| drop | f | Bayes | v4 | regret | always | never |", "|---|---|---|---|---|---|---|"]
    for d in DROPS:
        for f in FS:
            g = lambda k: np.mean([r["loss"] for r in by[k] if r["drop"] == d and r["f"] == f])
            L.append(f"| {int(d * 100)}% | {f:g} | {g('bayes'):.2f} | {g('v4'):.2f} | {100 * (g('v4') / g('bayes') - 1):+.1f}% | {g('always'):.2f} | {g('never'):.2f} |")
    v4, nev = sm("v4"), sm("never")
    R = ["", "## Pre-registered hypotheses (PREREGISTRATION_v5.md, part B)"]
    ok1 = all(bay.mean() <= sm(k).mean() for k in SAME_ACTIONS)
    R.append(f"- H-B1 (sanity) Bayes has the lowest mean loss among never, always, cusum, v4: "
             + ", ".join(f"{k} {sm(k).mean():.2f}" for k in SAME_ACTIONS) + f" vs Bayes {bay.mean():.2f} -> {'CONFIRMED' if ok1 else 'NOT CONFIRMED'}")
    reg = 100 * (v4 / bay - 1)
    r_ = np.random.default_rng(0); idx = r_.integers(0, len(seeds), (10000, len(seeds)))
    boot = 100 * (v4[idx].mean(axis=1) / bay[idx].mean(axis=1) - 1)
    hi = float(np.percentile(boot, 97.5)); lo = float(np.percentile(boot, 2.5))
    reg_m = 100 * (v4.mean() / bay.mean() - 1)
    R.append(f"- H-B2 v4 within 5% of Bayes-optimal: regret {reg_m:+.1f}% (95% CI {lo:+.1f}% to {hi:+.1f}%) -> {'CONFIRMED' if reg_m <= 5.0 else 'NOT CONFIRMED'}")
    cap = (nev.mean() - v4.mean()) / max(nev.mean() - bay.mean(), 1e-9)
    R.append(f"- H-B3 v4 captures >= 80% of the achievable saving over never-check: {cap:.0%} -> {'CONFIRMED' if cap >= 0.8 else 'NOT CONFIRMED'}")
    p = float(wilcoxon(v4, bay, alternative="greater").pvalue)
    R.append(f"- Descriptive: v4 above Bayes on {int((v4 > bay).sum())} of {len(seeds)} seeds (p = {p:.2g}). v5 (extra cross-check action): "
             f"{sm('v5').mean():.2f}; here a failed task costs only one call (22), less than a cross-check call (24).")
    rep = "\n".join(L + R)
    open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main()
