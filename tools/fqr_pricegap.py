"""Exploratory (1 Nov 2026): when does monitoring beat simply buying the fresh tool? FreshQA, real Phi-4 Mini verdicts."""
import os, itertools, json, numpy as np
os.environ.setdefault("EREPLAN_FMAX", "0.95")
from multiprocessing import Pool
from ereplan import freshqa_real as fr
from ereplan.config import Tool
from ereplan.v5_exp import setting
from ereplan import runner
MODEL = "phi4-mini@plain"
cal = fr.measure(MODEL, quiet=True)
S = fr._strats(MODEL)
KEYS = ("never", "v4", "v5", "use_B")
def job(a):
    k, stream, pb, sd = a
    name, params, told = S[k]
    q, f = cal[stream[4:]]["q"], cal[stream[4:]]["f"]
    tools = (Tool("A_cheap", 20.0, 1.0, 0.95, 0.95), Tool("B_mid", pb, 1.0, 0.95, 0.95), Tool("C_premium", pb + 6, 1.0, 0.97, 0.95))
    st = setting(q, 3.0, min(f, 0.95), 1.0, told).with_(tools=tools)
    return k, stream, pb, runner.run(name, dict(params), st, f"{stream}|{MODEL}", sd)["total_loss_fail"]
jobs = [(k, st, pb, sd) for k in KEYS for st in ("fqr_news", "fqr_mixed") for pb in (24.0, 30.0, 40.0) for sd in range(2500, 2510)]
with Pool(2) as pool: R = pool.map(job, jobs, chunksize=4)
for st in ("fqr_news", "fqr_mixed"):
    for pb in (24.0, 30.0, 40.0):
        m = {k: np.mean([r[3] for r in R if r[0] == k and r[1] == st and r[2] == pb]) for k in KEYS}
        print(f"{st:10s} B price {pb:4.0f}: " + "  ".join(f"{k} {v:.1f}" for k, v in m.items()))
