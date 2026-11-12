"""False alarms: check-worth map (A) and confirmatory test of rule v4 (B). See PREREGISTRATION_falsealarm.md.

Usage:  python -m ereplan.falsealarm_exp map
        python -m ereplan.falsealarm_exp confirm
"""
import argparse, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon

from .config import Setting
from .runner import run

SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
STRATS = {
    "never": ("B2_never", dict(window=30)),
    "always": ("B1_always", dict(window=30)),
    "cusum": ("B4_cusum", dict(h=6, p1=0.8)),
    "v2": ("Rule_leakaware", dict(SESSION)),
    "v3": ("Rule_v3_selfcal", dict(SESSION, q_prior_strength=3.0)),
    "v4": ("Rule_v4_fa", dict(SESSION, q_prior_strength=3.0)),
}
FS = (0.0, 0.05, 0.15)


def _job(a):
    key, drop, q, lm, f, seed = a
    name, params = STRATS[key]
    s = Setting().with_(q_true=q, q_assumed=q, check_frac=0.15, leak_mult=lm, false_alarm=f)
    r = run(name, params, s, f"drop_{drop:.2f}", seed)
    return dict(strategy=key, drop=drop, q=q, leak_mult=lm, f=f, seed=seed, loss=r["total_loss_fail"],
                fail_rate=r["fail_rate"], leak_rate=r["leak_rate"], checks=r["checks_per_task"])


def _run(jobs, procs):
    with Pool(procs) as pool:
        return pool.map(_job, jobs, chunksize=8)


def cmd_map(a):
    drops, keys = (0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.60), ("never", "always", "cusum", "v2", "v4")
    jobs = [(k, d, q, lm, f, sd) for k in keys for d, q, lm, f, sd in
            itertools.product(drops, (0.8, 0.95), (1.0, 3.0), FS, range(1300, 1310))]
    t0 = time.time(); rows = _run(jobs, a.procs)
    out = os.path.join("results", f"famap_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    mean = lambda **kw: float(np.mean([r["loss"] for r in rows if all(r[k] == v for k, v in kw.items())]))
    sav = {}
    for d, q, lm, f in itertools.product(drops, (0.8, 0.95), (1.0, 3.0), FS):
        nv = mean(strategy="never", drop=d, q=q, leak_mult=lm, f=f)
        best = min(mean(strategy=k, drop=d, q=q, leak_mult=lm, f=f) for k in keys if k != "never")
        sav[(d, q, lm, f)] = 100 * (nv - best) / nv
    med = lambda d, lm, f: float(np.median([sav[(d, q, lm, f)] for q in (0.8, 0.95)]))
    L = ["# Check-worth map with false alarms (pre-registered A)", "",
         f"Seeds 1300-1309; {len(rows)} runs; {time.time() - t0:.0f} s. Metric: total loss incl. one task cost per failed task.",
         "Median saving of the best checking strategy vs never checking (%), by drop:", "",
         "| Leak | f | " + " | ".join(f"{int(d*100)}%" for d in drops) + " |", "|---|---|" + "---|" * len(drops)]
    for lm in (1.0, 3.0):
        for f in FS:
            L.append(f"| {lm:g} | {f:g} | " + " | ".join(f"{med(d, lm, f):+.1f}" for d in drops) + " |")
    # H-FA1
    m = {d: med(d, 3.0, 0.05) for d in drops}
    peak = max(m, key=m.get)
    h1 = peak in (0.80, 0.75, 0.70) and m[peak] > m[0.95] and m[peak] > m[0.60]
    # H-FA2
    h2 = all(np.median([sav[(d, q, lm, 0.15)] for d in drops for q in (0.8, 0.95)]) <
             np.median([sav[(d, q, lm, 0.0)] for d in drops for q in (0.8, 0.95)]) for lm in (1.0, 3.0))
    L += ["", "## Pre-registered hypotheses",
          f"- H-FA1 hump survives at f = 0.05, leak 3: peak at {int(peak*100)}% ({m[peak]:+.1f}%), "
          f"95% {m[0.95]:+.1f}%, 60% {m[0.60]:+.1f}% -> {'CONFIRMED' if h1 else 'NOT CONFIRMED'}",
          f"- H-FA2 false alarms shrink the value of checking (f = 0.15 vs 0, both leak levels) -> {'CONFIRMED' if h2 else 'NOT CONFIRMED'}",
          "", "Which strategy is cheapest per cell (count):", ""]
    for f in FS:
        win = {}
        for d, q, lm in itertools.product(drops, (0.8, 0.95), (1.0, 3.0)):
            w = min(keys, key=lambda k: mean(strategy=k, drop=d, q=q, leak_mult=lm, f=f)); win[w] = win.get(w, 0) + 1
        L.append(f"- f = {f:g}: " + ", ".join(f"{k} {v}" for k, v in sorted(win.items(), key=lambda kv: -kv[1])))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L)); print("\n".join(L)); print("Saved to", out)


def cmd_confirm(a):
    drops = (0.95, 0.85, 0.75, 0.60)
    jobs = [(k, d, q, lm, f, sd) for k in STRATS for d, q, lm, f, sd in
            itertools.product(drops, (0.8, 0.95), (1.0, 3.0), FS, range(1200, 1220))]
    t0 = time.time(); rows = _run(jobs, a.procs)
    out = os.path.join("results", f"confirm_fa_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    key = lambda r: (r["drop"], r["q"], r["leak_mult"], r["f"], r["seed"])
    by = {k: {key(r): r["loss"] for r in rows if r["strategy"] == k} for k in STRATS}
    pos = sorted(k for k in by["v4"] if k[3] > 0); zero = sorted(k for k in by["v4"] if k[3] == 0)
    mean = lambda s, ks: float(np.mean([by[s][k] for k in ks]))
    pval = lambda s, ks: float(wilcoxon([by["v4"][k] for k in ks], [by[s][k] for k in ks], alternative="less").pvalue)
    L = ["# Confirmatory test of rule v4 (pre-registered B)", "",
         f"Seeds 1200-1219; {len(rows)} runs; {time.time() - t0:.0f} s. Metric: total loss incl. one task cost per failed task.", "",
         "| f | Leak | " + " | ".join(STRATS) + " |", "|---|---|" + "---|" * len(STRATS)]
    for f in FS:
        for lm in (1.0, 3.0):
            ks = [k for k in by["v4"] if k[3] == f and k[2] == lm]
            L.append(f"| {f:g} | {lm:g} | " + " | ".join(f"{mean(s, ks):.1f}" for s in STRATS) + " |")
    m4, m3 = mean("v4", pos), mean("v3", pos)
    p3 = pval("v3", pos)
    ha = p3 < 0.05 and m4 <= 0.95 * m3
    hb_parts = {s: (mean(s, pos), pval(s, pos)) for s in ("never", "always", "cusum")}
    hb = all(m4 < m and p < 0.05 for m, p in hb_parts.values())
    z4, z3 = mean("v4", zero), mean("v3", zero)
    hc = abs(z4 - z3) <= 0.01 * z3
    L += ["", "## Pre-registered hypotheses",
          f"- H-v4a (f > 0) v4 < v3 by >= 5%: {m4:.1f} vs {m3:.1f} ({100*(m4/m3-1):+.1f}%), p = {p3:.2g} -> {'CONFIRMED' if ha else 'NOT CONFIRMED'}",
          "- H-v4b (f > 0) v4 below never, always and CUSUM: " +
          "; ".join(f"{s} {m:.1f} (p = {p:.2g})" for s, (m, p) in hb_parts.items()) + f" vs v4 {m4:.1f} -> {'CONFIRMED' if hb else 'NOT CONFIRMED'}",
          f"- H-v4c (f = 0) v4 within 1% of v3: {z4:.1f} vs {z3:.1f} ({100*(z4/z3-1):+.1f}%) -> {'CONFIRMED' if hc else 'NOT CONFIRMED'}",
          "", "Per condition with f > 0 (v4 minus best of never/always/CUSUM, %):", ""]
    for d, lm in itertools.product(drops, (1.0, 3.0)):
        ks = [k for k in pos if k[0] == d and k[2] == lm]
        b = min(("never", "always", "cusum"), key=lambda s: mean(s, ks))
        L.append(f"- drop {int(d*100)}%, leak {lm:g}: v4 {mean('v4', ks):.1f} vs best baseline {b} {mean(b, ks):.1f} ({100*(mean('v4', ks)/mean(b, ks)-1):+.1f}%)")
    open(os.path.join(out, "report.md"), "w").write("\n".join(L)); print("\n".join(L)); print("Saved to", out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("map", "confirm"))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args(argv)
    {"map": cmd_map, "confirm": cmd_confirm}[a.cmd](a)


if __name__ == "__main__":
    main()
