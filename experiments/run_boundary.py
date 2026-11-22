"""Boundary map: when does monitoring beat buying the better tool? See PREREGISTRATION_boundary.md.
Usage: python experiments/run_boundary.py dev | confirm"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import os as _os
_os.environ["EREPLAN_FMAX"] = "0.5"
import sys, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon
from ereplan import runner
from ereplan.config import Setting, Tool
from ereplan.v5_exp import STRATS as V5, setting, SESSION

PS, PREMIUMS, LEAKS = (0, 25, 50, 75, 100), (10, 20, 35, 50, 100), (1.0, 3.0)
SEEDS = {"dev": (4950, 4951), "confirm": tuple(range(5100, 5120))}
STRATS = {"v6": ("Rule_v6", dict(SESSION), "none"), "fix_B": ("R_fix_B", dict(window=30), "true"), "never": V5["never"]}
BASE_MEAN = Setting().mean_price


def make_setting(prem, lm, told):
    pb = 20.0 * (1 + prem / 100.0)
    tools = (Tool("A_cheap", 20.0, 1.0, 0.95, 0.95), Tool("B_mid", pb, 1.0, 0.95, 0.95), Tool("C_premium", pb + 6, 1.0, 0.97, 0.95))
    s = setting(0.95, lm, 0.15, 1.0, told).with_(tools=tools)
    k = BASE_MEAN / s.mean_price                    # keep the wrong-answer cost and the check price at their standard values
    return s.with_(leak_mult=lm * k, check_frac=0.15 * k)


def job(a):
    key, P, prem, lm, seed = a
    name, params, told = STRATS[key]
    r = runner.run(name, dict(params), make_setting(prem, lm, told), f"pdrop_0.60@p{P}", seed)
    # every strategy is scored with the same absolute costs; total_loss_fail already uses the setting's own values
    return dict(strategy=key, p_deg=P, premium=prem, leak_mult=lm, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"], switches=r["switches"])


def _p(x, y):
    return 1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative="less").pvalue)


def main(which):
    seeds = SEEDS[which]
    jobs = list(itertools.product(STRATS, PS, PREMIUMS, LEAKS, seeds))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(job, jobs, chunksize=4)
    sm = lambda k, filt=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and filt(r)]) for sd in seeds])
    cell = lambda k, P, prem: sm(k, lambda r: r["p_deg"] == P and r["premium"] == prem).mean()
    L = [f"# Boundary map: monitoring vs buying the better tool ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. Cell = (v6 - fixed B) / fixed B; negative = the rule is cheaper.", "",
         "| A degrades in | " + " | ".join(f"B +{p}%" for p in PREMIUMS) + " | break-even premium |", "|---|" + "---|" * (len(PREMIUMS) + 1)]
    for P in PS:
        d = [100 * (cell("v6", P, pr) / cell("fix_B", P, pr) - 1) for pr in PREMIUMS]
        be = "rule always cheaper" if max(d) < 0 else "buying always cheaper" if min(d) > 0 else "none"
        for i in range(len(d) - 1):
            if d[i] > 0 >= d[i + 1]:
                be = f"about +{PREMIUMS[i] + (PREMIUMS[i + 1] - PREMIUMS[i]) * d[i] / (d[i] - d[i + 1]):.0f}%"
        L.append(f"| {P}% of runs | " + " | ".join(f"{x:+.1f}%" for x in d) + f" | {be} |")
    L += ["", "| A degrades in | " + " | ".join(f"never vs v6, B +{p}%" for p in PREMIUMS) + " |", "|---|" + "---|" * len(PREMIUMS)]
    for P in PS:
        L.append(f"| {P}% | " + " | ".join(f"{100 * (cell('never', P, pr) / cell('v6', P, pr) - 1):+.1f}%" for pr in PREMIUMS) + " |")
    mon = lambda r: r["premium"] >= 50 and r["p_deg"] <= 50
    buy = lambda r: r["premium"] <= 20 and r["p_deg"] >= 75
    t = {"H-B1 monitoring region (B +50% or more, A degrades in 50% of runs or fewer): v6 below fixed B": (sm("v6", mon), sm("fix_B", mon)),
         "H-B2 buying region (B +20% or less, A degrades in 75% of runs or more): fixed B below v6": (sm("fix_B", buy), sm("v6", buy))}
    ps = {h: _p(x, y) for h, (x, y) in t.items()}
    order = sorted(ps, key=ps.get); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and ps[h] < 0.05 / (len(order) - j); stop = stop or not holm[h]
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_boundary.md)", ""]
    for h, (x, y) in t.items():
        L.append(f"- {h}: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%), Wilcoxon p = {ps[h]:.2g} over {len(seeds)} seeds, "
                 f"Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    out = os.path.join("results", f"boundary_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
