"""N1 detectability test: does the boundary between monitoring and buying move with how detectable
degradation is? See PREREGISTRATION_detect.md.

The paper conjectures (Discussion, "Why the testbeds disagree") that the rule beats buying the reliable tool on the
simulator but not on FreshQA because degradation there is less detectable: the checker separates right from wrong
answers weakly (q - f about 0.25) and stale answers are never loud (rho = 0). This test varies exactly those two
things on the boundary-map design and nothing else.

Usage: python experiments/run_detect.py dev | confirm
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import os as _os
_os.environ["EREPLAN_FMAX"] = "0.95"     # the f grid must reach f = 0.55; set for every condition, so all are alike
_os.environ["EREPLAN_NETPV"] = "1"       # the corrected check criterion, as in every result for the rule
import sys, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon
from ereplan import runner
from ereplan.config import Setting, Tool
from ereplan.v5_exp import setting, SESSION

# detectability levels: (catch rate q, false-alarm rate f); q - f = 0.80, 0.50, 0.25
DET = {"high": (0.95, 0.15), "mid": (0.85, 0.35), "low": (0.80, 0.55)}
RHOS = (0.5, 0.0)                        # share of failures that are loud
PS, PREMIUMS, LEAKS = (25, 50, 100), (10, 20, 35, 50, 100), (1.0, 3.0)
SEEDS = {"dev": (4960, 4961), "confirm": tuple(range(9200, 9220))}
STRATS = {"v6": ("Rule_v6", dict(SESSION), "none"), "fix_B": ("R_fix_B", dict(window=30), "true")}
BASE_MEAN = Setting().mean_price


def make_setting(det, rho, prem, lm, told):
    q, f = DET[det]
    pb = 20.0 * (1 + prem / 100.0)
    tools = (Tool("A_cheap", 20.0, 1.0, 0.95, 0.95), Tool("B_mid", pb, 1.0, 0.95, 0.95), Tool("C_premium", pb + 6, 1.0, 0.97, 0.95))
    s = setting(q, lm, f, 1.0, told).with_(tools=tools, rho=rho)
    k = BASE_MEAN / s.mean_price                    # same absolute wrong-answer cost and check price as run_boundary.py
    return s.with_(leak_mult=lm * k, check_frac=0.15 * k)


def job(a):
    key, det, rho, P, prem, lm, seed = a
    name, params, told = STRATS[key]
    r = runner.run(name, dict(params), make_setting(det, rho, prem, lm, told), f"pdrop_0.60@p{P}", seed)
    return dict(strategy=key, det=det, rho=rho, p_deg=P, premium=prem, leak_mult=lm, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"], switches=r["switches"])


def main(which):
    seeds = SEEDS[which]
    jobs = list(itertools.product(STRATS, DET, RHOS, PS, PREMIUMS, LEAKS, seeds))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(job, jobs, chunksize=4)

    def mean_loss(k, sd, **kw):
        return np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and all(r[a] == b for a, b in kw.items())])

    def gap(det, rho):
        """Per seed: rule vs buying B, in %, over all degradation shares, premiums and wrong-answer costs."""
        return np.array([100 * (mean_loss("v6", sd, det=det, rho=rho) / mean_loss("fix_B", sd, det=det, rho=rho) - 1) for sd in seeds])

    def cell(det, rho, P, prem):
        return 100 * (np.mean([mean_loss("v6", sd, det=det, rho=rho, p_deg=P, premium=prem) for sd in seeds]) /
                      np.mean([mean_loss("fix_B", sd, det=det, rho=rho, p_deg=P, premium=prem) for sd in seeds]) - 1)

    L = [f"# N1 detectability test ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. Gap = (rule - buy B) / buy B; negative = the rule is cheaper.", "",
         "## Mean gap over the grid", "", "| detectability (q, f) | q - f | rho = 0.5 | rho = 0 |", "|---|---|---|---|"]
    for d, (q, f) in DET.items():
        L.append(f"| {d} ({q}, {f}) | {q - f:.2f} | {gap(d, 0.5).mean():+.1f}% | {gap(d, 0.0).mean():+.1f}% |")
    L += ["", "## Break-even premium of tool B (rule cheaper above it)", "",
          "| detectability | rho | " + " | ".join(f"A degrades in {P}%" for P in PS) + " |", "|---|---|" + "---|" * len(PS)]
    for d in DET:
        for rho in RHOS:
            out = []
            for P in PS:
                g = [cell(d, rho, P, pr) for pr in PREMIUMS]
                be = "rule always cheaper" if max(g) < 0 else "buying always cheaper" if min(g) > 0 else "mixed"
                for i in range(len(g) - 1):
                    if g[i] > 0 >= g[i + 1]:
                        be = f"about +{PREMIUMS[i] + (PREMIUMS[i + 1] - PREMIUMS[i]) * g[i] / (g[i] - g[i + 1]):.0f}%"
                out.append(be)
            L.append(f"| {d} | {rho} | " + " | ".join(out) + " |")
    L += ["", "## Gap by cell", "", "| detectability | rho | A degrades in | " + " | ".join(f"B +{p}%" for p in PREMIUMS) + " |",
          "|---|---|---|" + "---|" * len(PREMIUMS)]
    for d in DET:
        for rho in RHOS:
            for P in PS:
                L.append(f"| {d} | {rho} | {P}% | " + " | ".join(f"{cell(d, rho, P, pr):+.1f}%" for pr in PREMIUMS) + " |")

    tests = {
        "N1-1 at rho = 0.5, the gap is larger (worse for the rule) at low than at high detectability": (gap("low", 0.5), gap("high", 0.5)),
        "N1-2 at rho = 0, the gap is larger at low than at high detectability": (gap("low", 0.0), gap("high", 0.0)),
        "N1-3 at high detectability, the gap is larger with no loud failures (rho = 0) than with rho = 0.5": (gap("high", 0.0), gap("high", 0.5)),
    }
    ps = {h: (1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative="greater").pvalue)) for h, (x, y) in tests.items()}
    order = sorted(ps, key=ps.get); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and ps[h] < 0.05 / (len(order) - j); stop = stop or not holm[h]
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_detect.md)", ""]
    for h, (x, y) in tests.items():
        L.append(f"- {h}: {x.mean():+.1f}% vs {y.mean():+.1f}% (difference {x.mean() - y.mean():+.1f} points), one-sided Wilcoxon "
                 f"p = {ps[h]:.2g} over {len(seeds)} seeds, Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    for rho in RHOS:
        g = [gap(d, rho).mean() for d in DET]
        L.append(f"- N1-4 (descriptive) rho = {rho}: gap high {g[0]:+.1f}%, mid {g[1]:+.1f}%, low {g[2]:+.1f}% -> "
                 f"{'increases with falling detectability' if g[0] < g[1] < g[2] else 'not monotone'}")
    out = os.path.join("results", f"detect_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w", encoding="utf-8").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
