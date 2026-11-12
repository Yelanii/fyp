import itertools, numpy as np
from multiprocessing import Pool
from ereplan.runner import run
from ereplan import rule_v5s  # noqa
from ereplan.v5_exp import STRATS, setting, SESSION
S = {"never": STRATS["never"], "v4": STRATS["v4"], "always_x": STRATS["always_x"], "v5": STRATS["v5"],
     "v5_s": ("Rule_v5_s", dict(SESSION), "none")}
def job(a):
    k, sc, sg, f, sd = a
    name, p, told = S[k]
    st = setting(0.95, 3.0, f, 1.0, told).with_(xc_shared=sg)
    r = run(name, dict(p), st, sc, sd)
    return k, sc, sg, r["total_loss_fail"], r["leak_rate"], r.get("f_hat")
jobs = [(k, sc, sg, f, sd) for k in S for sc in ("alt_S1_only_A", "alt_S4_common") for sg in (0.0, 0.6) for f in (0.05, 0.15) for sd in range(2650, 2656)]
with Pool(2) as pool: rows = pool.map(job, jobs, chunksize=4)
for sc in ("alt_S1_only_A", "alt_S4_common"):
    print(sc)
    for k in S:
        out = []
        for sg in (0.0, 0.6):
            rr = [r for r in rows if r[0] == k and r[1] == sc and r[2] == sg]
            fh = [r[5] for r in rr if r[5] is not None]
            out.append(f"sigma {sg}: loss {np.mean([r[3] for r in rr]):.1f} leak {np.mean([r[4] for r in rr]):.3f} f_hat {np.mean(fh) if fh else float('nan'):.3f}")
        print(f"  {k:9s} " + " | ".join(out))
