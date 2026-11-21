"""D1-power: a high-power replication on the live model-backed tools. See PREREGISTRATION_d1power.md.

The earlier live-tool tests (D1, D1-cal, prior fix) used 20 seeds each. The differences between the checking policies
and never checking were about 1 to 3%, so 20 seeds could not separate some of them from chance. This test re-runs the
same live tools (cached answers in data/processed/d1_table.json, no model is called) on 200 new seeds, with the number
of seeds fixed in advance by a power analysis (see the pre-registration).

Usage:  python run_d1power.py dev       # seeds 7010-7014, pipeline check (not results)
        python run_d1power.py confirm   # seeds 7400-7599, run once
"""
import itertools, json, os, sys, time
import numpy as np
from multiprocessing import Pool
from scipy.stats import wilcoxon
from ereplan import agent_live as d
from ereplan.v5_exp import SESSION

# The label-light rule: the rule with the Study M labelled calibration (problems 1-200) as the prior of its checker
# memory, exactly as in run_d1cal.py ("v5_cal"); the rule with the corrected vague prior, exactly as in
# run_priorfix.py ("v5_fix").
d.STRATS["v5_cal"] = ("Rule_v5_x", dict(SESSION, q_prior_mean=d.TOLD_Q, q_prior_strength=151.0,
                                        f_prior_mean=d.TOLD_F, f_prior_strength=239.0), "true")
d.STRATS["v5_fix"] = ("Rule_v5_x", dict(SESSION, f_prior_matched=True), "none")
d.RNG_ALIAS.update({"v5_cal": "v5", "v5_fix": "v5"})
KEYS = ("never", "always", "cusum", "v4", "always_x", "v5_told", "v5", "v5_fix", "v5_cal", "fix_B")
SEEDS = {"dev": tuple(range(7010, 7015)), "confirm": tuple(range(7400, 7600))}
_TABLE = None


def _init(table=None):
    global _TABLE
    _TABLE = table if table is not None else json.load(open(d.TABLE))


def _job(a):
    k, sd, Lc, pb = a
    return d.run_one(_TABLE, k, sd, pb, Lc)


def _boot(x, y, n=10000, seed=0):
    idx = np.random.default_rng(seed).integers(0, len(x), (n, len(x)))
    m = 100 * (x[idx].mean(axis=1) / y[idx].mean(axis=1) - 1)
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def run(which, table=None, procs=None):
    seeds = SEEDS[which]
    jobs = [(k, sd, Lc, pb) for k, sd, (Lc, pb) in itertools.product(KEYS, seeds, d.CONDS)]
    t0 = time.time()
    if table is not None:                                   # tests: run in this process
        _init(table); rows = [_job(a) for a in jobs]
    else:
        with Pool(procs or max(1, (os.cpu_count() or 2) - 1), initializer=_init) as p:
            rows = p.map(_job, jobs, chunksize=8)
    sm = lambda k, f=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == s and f(r)]) for s in seeds])
    av = lambda k, field: np.mean([r[field] for r in rows if r["strategy"] == k])
    L = [f"# D1-power: live tools, high-power replication ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s; {len(seeds)} seeds x {len(d.CONDS)} conditions. Cached answers; no model called.", "",
         "| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task | median learned f |",
         "|---|---|---|---|---|---|---|"]
    for k in KEYS:
        fh = [r["f_hat"] for r in rows if r["strategy"] == k and r["f_hat"] is not None]
        L.append(f"| {k} | {sm(k).mean():.2f} | {100 * av(k, 'wrong_rate'):.1f}% | {100 * av(k, 'fail_rate'):.1f}% | "
                 f"{av(k, 'checks_per_task'):.2f} | {av(k, 'xchecks_per_task'):.2f} | " + (f"{np.median(fh):.3f} |" if fh else "- |"))
    L += ["", "| B price | wrong-answer cost | " + " | ".join(KEYS) + " |", "|---|---|" + "---|" * len(KEYS)]
    for Lc, pb in d.CONDS:
        L.append(f"| {pb:g} | {Lc:g} | " + " | ".join(f"{sm(k, lambda r: r['price_b'] == pb and r['L'] == Lc).mean():.1f}" for k in KEYS) + " |")
    tests = {"H-P1 the label-light rule (calibrated prior) below never checking": ("v5_cal", "never"),
             "H-P2 the label-light rule below the retrying rule told q and f": ("v5_cal", "v4"),
             "H-P3 cross-checking every call below never checking": ("always_x", "never"),
             "H-P4 cross-checking every call below the retrying rule told q and f": ("always_x", "v4")}
    ps = {h: (1.0 if np.allclose(sm(a), sm(b)) else float(wilcoxon(sm(a), sm(b), alternative="less").pvalue)) for h, (a, b) in tests.items()}
    order = sorted(ps, key=ps.get); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and ps[h] < 0.05 / (len(order) - j); stop = stop or not holm[h]
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_d1power.md; one-sided Wilcoxon over seeds, Holm across H-P1 to H-P4)", ""]
    for h, (a, b) in tests.items():
        x, y = sm(a), sm(b); lo, hi = _boot(x, y)
        L.append(f"- {h}: {x.mean():.2f} vs {y.mean():.2f} ({100 * (x.mean() / y.mean() - 1):+.2f}%, 95% CI {lo:+.2f}% to {hi:+.2f}%), "
                 f"p = {ps[h]:.2g}, Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    L += ["", "## Reported regardless of outcome (each against never checking)", ""]
    for k in ("v5", "v5_fix", "v5_told", "cusum", "always", "fix_B"):
        x, y = sm(k), sm("never"); lo, hi = _boot(x, y)
        L.append(f"- {k} vs never: {x.mean():.2f} vs {y.mean():.2f} ({100 * (x.mean() / y.mean() - 1):+.2f}%, 95% CI {lo:+.2f}% to {hi:+.2f}%)")
    x, y = sm("v5_cal"), sm("always_x"); lo, hi = _boot(x, y)
    L.append(f"- v5_cal vs always_x: {x.mean():.2f} vs {y.mean():.2f} ({100 * (x.mean() / y.mean() - 1):+.2f}%, 95% CI {lo:+.2f}% to {hi:+.2f}%)")
    L.append(f"- Per-seed standard deviation of the loss: " + ", ".join(f"{k} {sm(k).std(ddof=1):.2f}" for k in ("never", "v5_cal", "always_x", "v4")))
    out = os.path.join("results", f"d1power_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", out)
    return rows


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "dev")
