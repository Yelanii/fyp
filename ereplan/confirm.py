"""Confirmatory tests.
  python -m ereplan.confirm leak     H-leak:   rule v2 vs CUSUM,        seeds 300-319 (PREREGISTRATION_confirm_leak.md)
  python -m ereplan.confirm always   H-always: rule v2 vs always-check, seeds 400-419 (PREREGISTRATION_confirm_always.md)
"""
import itertools, json, os, sys, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon
from .checkmap import STRATEGIES, DROPS, QS, PRICES, _job

TESTS = {
    "leak": (("Decision rule v2", "Change alarm, CUSUM (B4)"), tuple(range(300, 320))),
    "always": (("Decision rule v2", "Always check (B1)"), tuple(range(400, 420))),
}


def main(name="leak"):
    PAIR, SEEDS = TESTS[name]
    jobs = [(lb, *STRATEGIES[lb], d, q, cf, 3.0, sd)
            for lb in PAIR for d, q, cf, sd in itertools.product(DROPS, QS, PRICES, SEEDS)]
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(_job, jobs, chunksize=16)
    key = lambda r: (r["drop"], r["q"], r["check_frac"], r["seed"])
    R = {key(r): r["total_loss"] for r in rows if r["strategy"] == PAIR[0]}
    C = {key(r): r["total_loss"] for r in rows if r["strategy"] == PAIR[1]}
    ks = sorted(R)
    a, b = np.array([R[k] for k in ks]), np.array([C[k] for k in ks])
    p_all = wilcoxon(a, b, alternative="less").pvalue
    rel = float(np.mean(a / b - 1))
    conds = sorted({k[:3] for k in ks})
    wins = sum(np.median([R[c + (s,)] for s in SEEDS]) < np.median([C[c + (s,)] for s in SEEDS]) for c in conds)
    ps = [np.mean([R[c + (s,)] for c in conds]) for s in SEEDS]
    pc = [np.mean([C[c + (s,)] for c in conds]) for s in SEEDS]
    p_seed = wilcoxon(ps, pc, alternative="less").pvalue
    ok = (p_all < 0.01) and (rel <= -0.05) and (wins >= 2 * len(conds) / 3) and (p_seed < 0.05)
    lost = [dict(drop=c[0], q=c[1], check_frac=c[2]) for c in conds
            if np.median([R[c + (s,)] for s in SEEDS]) >= np.median([C[c + (s,)] for s in SEEDS])]
    res = dict(test=name, compared=list(PAIR), seeds=[SEEDS[0], SEEDS[-1]], pairs=len(ks), p_all=float(p_all), mean_relative_difference=rel,
               conditions_won=int(wins), conditions=len(conds), p_per_seed=float(p_seed),
               rule_mean_total_loss=float(a.mean()), cusum_mean_total_loss=float(b.mean()),
               decision="CONFIRMED" if ok else "NOT CONFIRMED", conditions_rule_did_not_win=lost)
    out = os.path.join("results", f"confirm_{name}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "result.json"), "w"), indent=1)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "leak")
