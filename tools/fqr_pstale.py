"""Exploratory (1 Nov 2026): FreshQA, real judge verdicts; tool A goes stale in only a share of runs."""
import os, numpy as np
from multiprocessing import Pool
from ereplan import freshqa_real as fr
from ereplan.v5_exp import setting
from ereplan import runner
import sys
MODEL = sys.argv[1] if len(sys.argv) > 1 else "phi4-mini@plain"
cal = fr.measure(MODEL, quiet=True); S = fr._strats(MODEL)
KEYS = ("never", "always_x", "v4", "v5", "use_B", "rdecusum")
def job(a):
    k, st, ps, sd = a
    name, params, told = S[k]; q, f = cal[st[4:]]["q"], cal[st[4:]]["f"]
    return k, st, ps, runner.run(name, dict(params), setting(q, 3.0, min(f, .95), 1.0, told), f"{st}@p{ps}|{MODEL}", sd)["total_loss_fail"]
jobs = [(k, st, ps, sd) for k in KEYS for st in ("fqr_news", "fqr_mixed") for ps in (100, 50, 25) for sd in range(2500, 2520)]
with Pool(2) as pool: R = pool.map(job, jobs, chunksize=4)
for st in ("fqr_news", "fqr_mixed"):
    for ps in (100, 50, 25):
        m = {k: np.mean([r[3] for r in R if r[:3] == (k, st, ps)]) for k in KEYS}
        print(f"{st:9s} stale in {ps:3d}% of runs: " + "  ".join(f"{k} {v:.1f}" for k, v in m.items()))
