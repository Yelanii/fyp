import itertools, numpy as np
from multiprocessing import Pool
from ereplan import freshqa_real  # noqa (registers R_use_B)
from ereplan.runner import run
from ereplan.v5_exp import STRATS, setting, DROPS, QS, LEAKS, FS, PIS
S = {"never": STRATS["never"], "v5": STRATS["v5"], "use_B": ("R_use_B", dict(window=30), "true")}
def job(a):
    k, c, sd = a; d, q, lm, f, pi = c
    n, p, told = S[k]
    return k, d, lm, run(n, dict(p), setting(q, lm, f, pi, told), f"drop_{d:.2f}", sd)["total_loss_fail"]
jobs = [(k, c, sd) for k in S for c in itertools.product(DROPS, QS, LEAKS, FS, PIS) for sd in (2410, 2411, 2412)]
with Pool(2) as pool: R = pool.map(job, jobs, chunksize=8)
for k in S:
    print(k, "all %.1f" % np.mean([r[3] for r in R if r[0] == k]),
          " | ".join("drop %d%%: %.1f" % (100 * d, np.mean([r[3] for r in R if r[0] == k and r[1] == d])) for d in DROPS),
          " | leak1 %.1f leak3 %.1f" % tuple(np.mean([r[3] for r in R if r[0] == k and r[2] == l]) for l in (1.0, 3.0)))
