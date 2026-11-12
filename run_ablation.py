"""FR21/C5 ablation of rule v5.1 (9 November 2026). See PREREGISTRATION_ablation_v51.md.

Usage:  python -m run_ablation dev        # smoke test, development seeds 1750-1755 (no tuning)
        python -m run_ablation confirm    # pre-registered test, seeds 1800-1819
"""
import os as _os
_os.environ["EREPLAN_FMAX"] = "0.5"      # simulator studies use the default f grid; fixed here so a shell setting cannot change results
import argparse, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon

from ereplan.config import Setting
from ereplan.runner import run
from ereplan import ablation_v51  # noqa: F401  (registers the four ablation classes)

DROPS, QS, FS, PIS = (0.95, 0.85, 0.75, 0.60), (0.8, 0.95), (0.05, 0.15), (0.0, 1.0)
TEST_SEEDS, DEV_SEEDS = tuple(range(1800, 1820)), tuple(range(1750, 1756))
SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
FIXED = dict(check_frac=0.15, leak_mult=1.0, xc_shared=0.4, third_source_frac=0.3, audit_frac=0.05, n_tasks=200)

STRATS = {
    "full": ("Rule_v5_1", dict(SESSION)),
    "nofa": ("Rule_v5_1_nofa", dict(SESSION)),
    "noxc": ("Rule_v5_1_noxc", dict(SESSION)),
    "noswitch": ("Rule_v5_1_noswitch", dict(SESSION)),
    "told": ("Rule_v5_1_told", dict(SESSION)),
    "nowindow": ("Rule_v5_1", dict(SESSION, window=1_000_000)),
}
ABLATED = ("nofa", "noxc", "noswitch", "told", "nowindow")
HYPS = {"nofa": "H-A1", "noxc": "H-A2", "noswitch": "H-A3", "told": "H-A4", "nowindow": "H-A5"}


def setting(q, f, pi):
    return Setting().with_(q_true=q, q_assumed=q, false_alarm=f, fa_persistence=pi, **FIXED)


def _job(a):
    key, drop, q, f, pi, seed = a
    name, params = STRATS[key]
    r = run(name, dict(params), setting(q, f, pi), f"drop_{drop:.2f}", seed)
    return dict(strategy=key, drop=drop, q=q, f=f, pi=pi, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"],
                crosschecks=r["crosschecks_per_task"], switches=r.get("switches", 0))


def jobs_for(seeds, keys=None):
    keys = keys or list(STRATS)
    return [(k, d, q, f, pi, sd) for k in keys for d, q, f, pi, sd in itertools.product(DROPS, QS, FS, PIS, seeds)]


def execute(seeds, procs):
    with Pool(procs) as pool:
        return pool.map(_job, jobs_for(seeds), chunksize=8)


def _p(x, y, alt="less"):
    x, y = np.asarray(x), np.asarray(y)
    if np.allclose(x, y):
        return 1.0
    return float(wilcoxon(x, y, alternative=alt).pvalue)


def _boot_ci(x, y, n=10000, seed=0):
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

    def seed_means(k, field="loss"):
        return np.array([float(np.mean([r[field] for r in by[k] if r["seed"] == sd])) for sd in seeds])

    L = [f"# {title}", "", f"Seeds {seeds[0]}-{seeds[-1]}; {len(rows)} runs; {secs:.0f} s. "
         "Unit of analysis: the seed (mean over the 32 conditions of drop x q x f x pi). "
         "Metric: total loss per task.", "",
         "## Mean outcomes per strategy", "",
         "| Strategy | total loss | leak rate | failed tasks | checks/task | cross-checks/task | switches |",
         "|---|---|---|---|---|---|---|"]
    for k in S:
        rr = by[k]
        L.append(f"| {k} | {np.mean([r['loss'] for r in rr]):.1f} | {np.mean([r['leak_rate'] for r in rr]):.1%} | "
                 f"{np.mean([r['fail_rate'] for r in rr]):.1%} | {np.mean([r['checks'] for r in rr]):.2f} | "
                 f"{np.mean([r['crosschecks'] for r in rr]):.2f} | {np.mean([r['switches'] for r in rr]):.2f} |")

    full = seed_means("full")
    R = ["", "## Pre-registered hypotheses (PREREGISTRATION_ablation_v51.md)"]
    prim = {}
    for key in ABLATED:
        o = seed_means(key)
        p = _p(full, o)
        lo, hi = _boot_ci(full, o)
        prim[key] = (p, o, lo, hi)
    order = sorted(prim, key=lambda k: prim[k][0]); holm = {}
    stop = False
    for i, k in enumerate(order):
        holm[k] = (not stop) and prim[k][0] < 0.05 / (5 - i)
        stop = stop or not holm[k]
    increases = {}
    for key in ABLATED:
        p, o, lo, hi = prim[key]
        hid = HYPS[key]
        pct = 100 * (o.mean() / full.mean() - 1)
        increases[key] = pct
        ok = holm[key] and o.mean() > full.mean()
        R.append(f"- {hid} full below {key}: {full.mean():.1f} vs {o.mean():.1f} ({pct:+.1f}%, "
                 f"95% CI {lo:+.1f}% to {hi:+.1f}%), Wilcoxon p = {p:.2g} over {len(seeds)} seeds, "
                 f"Holm {'ok' if holm[key] else 'fail'} -> {'CONFIRMED' if ok else 'NOT CONFIRMED'}")
    ranked = sorted(increases, key=lambda k: -increases[k])
    R += ["", "## H-A6 (descriptive, not confirmatory): ranked loss increase from removing each ingredient", ""]
    for k in ranked:
        R.append(f"- {k}: {increases[k]:+.1f}%")
    return "\n".join(L + R)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("dev", "confirm"))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args(argv)
    seeds = DEV_SEEDS if a.cmd == "dev" else TEST_SEEDS
    t0 = time.time()
    rows = execute(seeds, a.procs)
    out = os.path.join("results", f"ablation_{a.cmd}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    title = ("FR21 ablation: development smoke test (not a test of the hypotheses)" if a.cmd == "dev"
              else "FR21 ablation: pre-registered test")
    rep = report(rows, list(seeds), title, time.time() - t0)
    open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main()
