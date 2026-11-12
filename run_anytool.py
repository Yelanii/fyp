"""FR18 (10 Nov 2026): any tool can degrade; rule v6. See PREREGISTRATION_anytool.md.
Usage: python run_anytool.py dev | confirm"""
import os as _os
_os.environ["EREPLAN_FMAX"] = "0.5"
import sys, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon
from ereplan import runner
from ereplan.v5_exp import STRATS as V5, setting, SESSION

SCEN, QS, LEAKS, F, PI = ("any_one", "any_two", "any_recover"), (0.8, 0.95), (1.0, 3.0), 0.15, 1.0
SEEDS = {"dev": tuple(range(4900, 4906)), "confirm": tuple(range(5200, 5220))}
STRATS = {"fix_A": ("R_fix_A", dict(window=30), "true"), "fix_B": ("R_fix_B", dict(window=30), "true"),
          "fix_C": ("R_fix_C", dict(window=30), "true"), "never": V5["never"], "cusum": V5["cusum"],
          "always_x": V5["always_x"], "v4": V5["v4"], "v5": V5["v5"], "v6": ("Rule_v6", dict(SESSION), "none")}


def job(a):
    key, sc, q, lm, seed = a
    name, params, told = STRATS[key]
    r = runner.run(name, dict(params), setting(q, lm, F, PI, told), sc, seed)
    return dict(strategy=key, scenario=sc, q=q, leak_mult=lm, seed=seed, loss=r["total_loss_fail"], leak_rate=r["leak_rate"],
                fail_rate=r["fail_rate"], checks=r["checks_per_task"], switches=r["switches"], retests=r.get("retests"))


def _p(x, y):
    return 1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative="less").pvalue)


def _ci(x, y, n=10000):
    idx = np.random.default_rng(0).integers(0, len(x), (n, len(x)))
    d = 100 * (x[idx].mean(axis=1) / y[idx].mean(axis=1) - 1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main(which):
    seeds = SEEDS[which]
    jobs = list(itertools.product(STRATS, SCEN, QS, LEAKS, seeds))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(job, jobs, chunksize=4)
    sm = lambda k, filt=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and filt(r)]) for sd in seeds])
    L = [f"# FR18: any tool can degrade ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. 12 conditions per seed. Metric: total loss per task.", "",
         "| Strategy | all | " + " | ".join(SCEN) + " | wrong kept | failed | checks/task | switches/run |", "|---|---|" + "---|" * (len(SCEN) + 4)]
    for k in STRATS:
        g = lambda f: np.mean([r[f] for r in rows if r["strategy"] == k])
        L.append(f"| {k} | {sm(k).mean():.1f} | " + " | ".join(f"{sm(k, lambda r, sc=sc: r['scenario'] == sc).mean():.1f}" for sc in SCEN)
                 + f" | {g('leak_rate'):.1%} | {g('fail_rate'):.1%} | {g('checks'):.2f} | {g('switches'):.2f} |")
    v6 = sm("v6"); rec = lambda r: r["scenario"] == "any_recover"
    tests = {"H-N1a v6 below fixed tool A": (v6, sm("fix_A")), "H-N1b v6 below fixed tool B": (v6, sm("fix_B")),
             "H-N1c v6 below fixed tool C": (v6, sm("fix_C")), "H-N2 v6 below never checking": (v6, sm("never")),
             "H-N3 on any_recover, v6 below v5": (sm("v6", rec), sm("v5", rec))}
    ps = {h: _p(x, y) for h, (x, y) in tests.items()}
    order = sorted(ps, key=ps.get); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and ps[h] < 0.05 / (len(order) - j); stop = stop or not holm[h]
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_anytool.md)", ""]
    for h, (x, y) in tests.items():
        lo, hi = _ci(x, y)
        L.append(f"- {h}: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%), "
                 f"Wilcoxon p = {ps[h]:.2g} over {len(seeds)} seeds, Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    v5 = sm("v5"); lo, hi = _ci(v6, v5)
    hind = np.mean([min(sm(k, lambda r, sc=sc: r["scenario"] == sc).mean() for k in ("fix_A", "fix_B", "fix_C")) for sc in SCEN])
    L += ["", f"- Secondary: v6 vs v5 over all scenarios: {v6.mean():.1f} vs {v5.mean():.1f} ({100 * (v6.mean() / v5.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%)",
          f"- Descriptive: best fixed tool chosen in hindsight per scenario, mean {hind:.1f}; v6 {v6.mean():.1f}",
          f"- Descriptive: v6 re-tests per run {np.mean([r['retests'] for r in rows if r['strategy'] == 'v6']):.2f}"]
    out = os.path.join("results", f"anytool_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
