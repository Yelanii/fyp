import numpy as np
from ereplan import freshqa_real as fr
from ereplan.v5_exp import setting
from ereplan import runner
M = "phi4-mini@plain"; cal = fr.measure(M, quiet=True); S = fr._strats(M)
q, f = cal["mixed"]["q"], cal["mixed"]["f"]
for k in ("never", "v4", "v5", "use_B"):
    rs = [runner.run(S[k][0], dict(S[k][1]), setting(q, 3.0, f, 1.0, S[k][2]), f"fqr_mixed@p0|{M}", sd, record=True) for sd in range(2500, 2505)]
    tr = rs[0]["trace"]
    sw = [x["t"] for x in tr if x.get("action") == "switch"]
    tools = [x["tool"] for x in tr]
    print(k, "loss %.1f" % np.mean([r["total_loss_fail"] for r in rs]), "leak %.3f fail %.3f checks %.2f xc %.2f switches %.1f" % tuple(np.mean([r[x] for r in rs]) for x in ("leak_rate", "fail_rate", "checks_per_task", "crosschecks_per_task", "switches")),
          "| seed0 first switch at", sw[:5], "share of calls on A %.2f" % np.mean([t == 0 for t in tools]))
