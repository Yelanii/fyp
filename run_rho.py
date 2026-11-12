"""FR20 confirmatory test: learning the loud-failure share rho vs. a fixed, wrong assumption (9 Nov 2026).
See PREREGISTRATION_rho.md.

Usage:  python -m run_rho dev        # smoke test, development seeds 1850-1855 (no tuning)
        python -m run_rho confirm    # pre-registered test, seeds 1900-1919
"""
import os as _os
_os.environ["EREPLAN_FMAX"] = "0.5"      # simulator studies use the default f grid; fixed here so a shell setting cannot change results
import argparse, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon

from ereplan.config import Setting
from ereplan.runner import run
from ereplan import rule_rho  # noqa: F401  (registers Rule_v5_rho and its variants)

DROPS, QS, FS = (0.95, 0.85, 0.75, 0.60), (0.8, 0.95), (0.05, 0.15)
PRIMARY_RHOS, SANITY_RHOS = (0.0, 0.1, 0.3), (0.5,)
TEST_SEEDS, DEV_SEEDS = tuple(range(1900, 1920)), tuple(range(1850, 1856))
SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
WRONG = dict(SESSION, rho_belief=0.5)

STRATS = {
    "fixed": ("Rule_v5_x", dict(WRONG)),
    "told": ("Rule_v5_x", dict(SESSION)),                       # rho_belief=None -> true rho (oracle)
    "rho_cap": ("Rule_v5_rho", dict(WRONG)),
    "rho_mean": ("Rule_v5_rho_mean", dict(WRONG)),
    "rho_lcb": ("Rule_v5_rho_lcb", dict(WRONG)),
    "rho_noaudit": ("Rule_v5_rho_noaudit", dict(WRONG)),
}


def setting(true_rho, drop, q, f):
    return Setting().with_(q_true=q, q_assumed=q, false_alarm=f, rho=true_rho, check_frac=0.15, leak_mult=1.0,
                           xc_shared=0.0, n_tasks=200)


def _job(a):
    key, group, true_rho, drop, q, f, seed = a
    name, params = STRATS[key]
    r = run(name, dict(params), setting(true_rho, drop, q, f), f"drop_{drop:.2f}", seed)
    return dict(strategy=key, group=group, true_rho=true_rho, drop=drop, q=q, f=f, seed=seed,
                loss=r["total_loss_fail"], leak_rate=r["leak_rate"], fail_rate=r["fail_rate"],
                checks=r["checks_per_task"], rho_hat=r.get("rho_hat"))


def jobs_for(seeds):
    out = []
    for group, rhos in (("primary", PRIMARY_RHOS), ("sanity", SANITY_RHOS)):
        for k in STRATS:
            out += [(k, group, rho, d, q, f, sd) for rho, d, q, f, sd in
                    itertools.product(rhos, DROPS, QS, FS, seeds)]
    return out


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
    by = {}
    for r in rows:
        by.setdefault((r["strategy"], r["group"]), []).append(r)

    def seed_means(k, group, field="loss"):
        rr = [r for r in by[(k, group)]]
        return np.array([float(np.mean([r[field] for r in rr if r["seed"] == sd])) for sd in seeds])

    L = [f"# {title}", "", f"Seeds {seeds[0]}-{seeds[-1]}; {len(rows)} runs; {secs:.0f} s. "
         "Unit of analysis: the seed. Metric: total loss per task.", "",
         "## Primary conditions (true rho in {0.0, 0.1, 0.3}; old fixed belief = 0.5, wrong)", "",
         "| Strategy | total loss | leak rate | checks/task |", "|---|---|---|---|"]
    for k in STRATS:
        rr = by[(k, "primary")]
        L.append(f"| {k} | {np.mean([r['loss'] for r in rr]):.1f} | {np.mean([r['leak_rate'] for r in rr]):.1%} | "
                 f"{np.mean([r['checks'] for r in rr]):.2f} |")
    L += ["", "## Sanity conditions (true rho = 0.5; the old belief happened to be right) -- descriptive only", "",
          "| Strategy | total loss |", "|---|---|"]
    for k in STRATS:
        rr = by[(k, "sanity")]
        L.append(f"| {k} | {np.mean([r['loss'] for r in rr]):.1f} |")

    cap, fixed, told = seed_means("rho_cap", "primary"), seed_means("fixed", "primary"), seed_means("told", "primary")
    R = ["", "## Pre-registered hypotheses (PREREGISTRATION_rho.md)"]
    p1 = _p(cap, fixed)
    lo1, hi1 = _boot_ci(cap, fixed)
    p2 = _p(cap, told)
    lo2, hi2 = _boot_ci(cap, told)
    prim = {"H-R1": p1, "H-R2": 1.0}  # H-R2 isn't a "lower" test; Holm applied to the two p-values we do have
    order = sorted(prim, key=lambda h: prim[h]); holm = {}
    stop = False
    for i, h in enumerate(order):
        holm[h] = (not stop) and prim[h] < 0.05 / (2 - i)
        stop = stop or not holm[h]
    ok1 = holm["H-R1"] and cap.mean() < fixed.mean()
    R.append(f"- H-R1 rho_cap below fixed (wrong, constant 0.5): {cap.mean():.1f} vs {fixed.mean():.1f} "
             f"({100 * (cap.mean() / fixed.mean() - 1):+.1f}%, 95% CI {lo1:+.1f}% to {hi1:+.1f}%), "
             f"Wilcoxon p = {p1:.2g} over {len(seeds)} seeds, Holm {'ok' if holm['H-R1'] else 'fail'} -> "
             f"{'CONFIRMED' if ok1 else 'NOT CONFIRMED'}")
    ok2 = hi2 <= 5.0
    R.append(f"- H-R2 rho_cap within 5% of told (oracle): {cap.mean():.1f} vs {told.mean():.1f} "
             f"({100 * (cap.mean() / told.mean() - 1):+.1f}%, 95% CI upper {hi2:+.1f}%) -> "
             f"{'CONFIRMED' if ok2 else 'NOT CONFIRMED'}")

    R += ["", "## H-R3 (descriptive): ranked mean loss of the four rho-learning modes, primary conditions"]
    modes = ("rho_cap", "rho_mean", "rho_lcb", "rho_noaudit")
    means = {m: seed_means(m, "primary").mean() for m in modes}
    for m in sorted(means, key=lambda k: means[k]):
        R.append(f"- {m}: {means[m]:.1f}")

    rh = [r["rho_hat"] for r in by[("rho_cap", "primary")] if r["rho_hat"] is not None]
    tr = [r["true_rho"] for r in by[("rho_cap", "primary")] if r["rho_hat"] is not None]
    err = np.abs(np.array(rh) - np.array(tr))
    R += ["", f"## H-R4 (descriptive): rho_cap's learned rho_hat, median |rho_hat - true rho| = {np.median(err):.3f}"]

    cap_s, fixed_s = seed_means("rho_cap", "sanity"), seed_means("fixed", "sanity")
    rel = 100 * abs(cap_s.mean() - fixed_s.mean()) / fixed_s.mean()
    R += ["", f"## Sanity check: at true rho = 0.5 (old belief correct), rho_cap vs fixed differ by {rel:.1f}% "
              f"of fixed's loss ({cap_s.mean():.1f} vs {fixed_s.mean():.1f}) -- expected small, descriptive only"]
    return "\n".join(L + R)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("dev", "confirm"))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args(argv)
    seeds = DEV_SEEDS if a.cmd == "dev" else TEST_SEEDS
    t0 = time.time()
    rows = execute(seeds, a.procs)
    out = os.path.join("results", f"rho_{a.cmd}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    title = ("FR20 confirmatory test: development smoke test (not a test of the hypotheses)" if a.cmd == "dev"
              else "FR20 confirmatory test: pre-registered test")
    rep = report(rows, list(seeds), title, time.time() - t0)
    open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main()
