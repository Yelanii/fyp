"""S1 (13 Nov 2026): the cross-check when its assumptions fail. See PREREGISTRATION_robustness.md.
Usage: python run_robustness.py dev | confirm"""
import os as _os
_os.environ["EREPLAN_FMAX"] = "0.5"
import sys, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon
from ereplan import runner
from ereplan.v5_exp import STRATS as V5, setting

SIGMAS, ES, SCENS, QS, LEAKS, F, PI = (0.0, 0.5, 0.9), (0.0, 0.1, 0.2), ("drop_0.75", "alt_S3_indep", "alt_S4_common"), (0.8, 0.95), (1.0, 3.0), 0.15, 1.0
TWO = ("alt_S3_indep", "alt_S4_common")
SEEDS = {"dev": (6000, 6001), "confirm": tuple(range(6100, 6120))}
KEYS = ("never", "v4", "v4_nocal", "always_x", "v5")


def job(a):
    key, sg, e, sc, q, lm, seed = a
    name, params, told = V5[key]
    s = setting(q, lm, F, PI, told).with_(xc_shared=sg, xc_noise=e)
    r = runner.run(name, dict(params), s, sc, seed)
    return dict(strategy=key, sigma=sg, e=e, scenario=sc, q=q, leak_mult=lm, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"], f_hat=r.get("f_hat"))


def _p(x, y):
    return 1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative="less").pvalue)


def _ci(x, y, n=10000):
    idx = np.random.default_rng(0).integers(0, len(x), (n, len(x)))
    d = 100 * (x[idx].mean(axis=1) / y[idx].mean(axis=1) - 1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main(which):
    seeds = SEEDS[which]
    jobs = list(itertools.product(KEYS, SIGMAS, ES, SCENS, QS, LEAKS, seeds))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(job, jobs, chunksize=4)
    sm = lambda k, fn=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and fn(r)]) for sd in seeds])
    cell = lambda sg, e, scs=TWO: (lambda r: r["sigma"] == sg and r["e"] == e and r["scenario"] in scs)
    L = [f"# S1 robustness: cross-check assumptions broken ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. Cell = mean total loss per task of v5 / change vs v4 without labels / change vs v4 told."]
    for scs, title in ((("drop_0.75",), "only A degrades (reference)"), (("alt_S3_indep",), "A and B degrade independently"),
                       (("alt_S4_common",), "A and B degrade together (shared cause)")):
        L += ["", f"### {title}", "", "| sigma \\ e | " + " | ".join(f"e = {e}" for e in ES) + " |", "|---|" + "---|" * len(ES)]
        for sg in SIGMAS:
            cs = []
            for e in ES:
                c = cell(sg, e, scs)
                v5, nc, tv = sm("v5", c).mean(), sm("v4_nocal", c).mean(), sm("v4", c).mean()
                cs.append(f"{v5:.1f} / {100 * (v5 / nc - 1):+.1f}% / {100 * (v5 / tv - 1):+.1f}%")
            L.append(f"| {sg} | " + " | ".join(cs) + " |")
    L += ["", "Loss of cross-check every call (always_x), two-tool scenarios, by sigma at e = 0: " +
          ", ".join(f"sigma {sg}: {sm('always_x', cell(sg, 0.0)).mean():.1f}" for sg in SIGMAS)]
    L += ["", "Median learned f, two-tool scenarios (true f = 0.15):", "", "| sigma \\ e | " + " | ".join(f"e = {e}" for e in ES) + " |", "|---|" + "---|" * len(ES)]
    for sg in SIGMAS:
        L.append(f"| {sg} | " + " | ".join(f"{np.median([r['f_hat'] for r in rows if r['strategy'] == 'v5' and cell(sg, e)(r)]):.3f}" for e in ES) + " |")
    L += ["", "| Strategy | all cells |", "|---|---|"] + [f"| {k} | {sm(k).mean():.1f} |" for k in KEYS]
    a0, a9 = sm("v5", cell(0.0, 0.0)), sm("v5", cell(0.9, 0.0))
    lo, hi = _ci(a9, a0)
    worst = cell(0.9, 0.2)
    w5, wn, wt = sm("v5", worst), sm("v4_nocal", worst), sm("v4", worst)
    p2 = _p(w5, wn)
    lo2, hi2 = _ci(w5, wn); lo3, hi3 = _ci(w5, wt)
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_robustness.md)", "",
          f"- H-S1 v5 at sigma 0.9 within +2% of sigma 0 (e = 0): {a9.mean():.1f} vs {a0.mean():.1f} ({100 * (a9.mean() / a0.mean() - 1):+.1f}%, "
          f"95% CI {lo:+.1f}% to {hi:+.1f}%) -> **{'CONFIRMED' if hi <= 2 else 'NOT CONFIRMED'}**",
          f"- H-S2 worst cell, v5 below v4 without labels: {w5.mean():.1f} vs {wn.mean():.1f} ({100 * (w5.mean() / wn.mean() - 1):+.1f}%, "
          f"95% CI {lo2:+.1f}% to {hi2:+.1f}%), p = {p2:.2g}",
          f"- H-S3 worst cell, v5 within +3% of v4 told: {w5.mean():.1f} vs {wt.mean():.1f} ({100 * (w5.mean() / wt.mean() - 1):+.1f}%, "
          f"95% CI {lo3:+.1f}% to {hi3:+.1f}%)"]
    s2, s3 = p2 < 0.05, hi3 <= 3
    L[-2] += f" -> **{'CONFIRMED' if s2 else 'NOT CONFIRMED'}**"
    L[-1] += f" -> **{'CONFIRMED' if s3 else 'NOT CONFIRMED'}**"
    out = os.path.join("results", f"robustness_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
