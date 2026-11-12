"""FR11 (10 Nov 2026): CostBench with checker error rates taken from real checkers.
See PREREGISTRATION_fr11_realcheckers.md.   Usage: python3 run_fr11.py dev | confirm"""
import os, sys, itertools, json, time
os.environ.setdefault("EREPLAN_FMAX", "0.95")
from multiprocessing import Pool
import numpy as np
from ereplan import costbench_v5 as cb

PROFILES = {"qwen2.5:1.5b": (0.981, 0.143, 1.0), "qwen2.5:3b": (0.990, 0.050, 1.0),
            "phi4-mini": (0.807, 0.556, 1.0), "llama3.1:8b": (0.759, 0.516, 1.0)}
DROPS, LEAKS, GAPS, FRACS = (0.95, 0.85, 0.75, 0.60), (1.0, 3.0), (0.0, 0.20), (0.05, 0.15)
SEEDS = {"dev": (1990, 1991), "confirm": tuple(range(2800, 2818))}


def job(a):
    prof, drop, lm, gap, cf, seed = a
    q, f, pi = PROFILES[prof]
    return [dict(r, profile=prof, check_frac=cf) for r in cb._job((drop, q, f, pi, lm, gap, seed, cf))]


def main(which):
    seeds = SEEDS[which]
    keys = list(itertools.product(PROFILES, DROPS, LEAKS, GAPS, FRACS, seeds))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = [r for rs in pool.imap_unordered(job, keys, chunksize=4) for r in rs]
    S = list(cb.STRATS)
    sm = lambda k, filt=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and filt(r)]) for sd in seeds])
    L = [f"# FR11: CostBench with real-checker error rates ({which})", "",
         f"Seeds {seeds[0]}-{seeds[-1]}; {len(keys) // len(seeds)} conditions per seed; {len(rows)} runs; {time.time() - t0:.0f} s.", "",
         "## Mean total loss per task, by checker profile", "", "| Strategy | all | " + " | ".join(PROFILES) + " | failed tasks | checks/task |",
         "|---|---|" + "---|" * (len(PROFILES) + 2)]
    for k in S:
        g = lambda f: np.mean([r[f] for r in rows if r["strategy"] == k])
        L.append(f"| {k} | {sm(k).mean():.1f} | " + " | ".join(f"{sm(k, lambda r, p=p: r['profile'] == p).mean():.1f}" for p in PROFILES)
                 + f" | {g('fail_rate'):.1%} | {g('checks'):.2f} |")
    L += ["", "## By check price", "", "| Strategy | 5% | 15% |", "|---|---|---|"]
    for k in S:
        L.append(f"| {k} | {sm(k, lambda r: r['check_frac'] == 0.05).mean():.1f} | {sm(k, lambda r: r['check_frac'] == 0.15).mean():.1f} |")
    v5 = sm("v5"); prim = {}
    for hid, b in (("H-RC1", "v4_nocal"), ("H-RC3", "always_x")):
        y = sm(b); prim[hid] = (cb._p(v5, y), b, y.mean()) + cb._boot_ci(v5, y)
    order = sorted(prim, key=lambda h: prim[h][0]); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and prim[h][0] < 0.05 / (len(order) - j); stop = stop or not holm[h]
    L += ["", "## Pre-registered hypotheses", ""]
    for h in ("H-RC1", "H-RC3"):
        p, b, ym, lo, hi = prim[h]
        L.append(f"- {h} v5 below {b}: {v5.mean():.1f} vs {ym:.1f} ({100 * (v5.mean() / ym - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%), "
                 f"Wilcoxon p = {p:.2g} over {len(seeds)} seeds, Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    v4 = sm("v4"); lo, hi = cb._boot_ci(v5, v4)
    L.append(f"- H-RC2 v5 equivalent to v4 told q and f, within +/-3%: {v5.mean():.1f} vs {v4.mean():.1f} ({100 * (v5.mean() / v4.mean() - 1):+.1f}%, "
             f"95% CI {lo:+.1f}% to {hi:+.1f}%) -> **{'CONFIRMED' if -3 <= lo and hi <= 3 else 'NOT CONFIRMED'}**")
    L += ["", "## Descriptive: v5 per profile", "", "| Profile | v5 vs never | v5 vs v4 told | median abs error of learned f | of learned q |", "|---|---|---|---|---|"]
    for p in PROFILES:
        fl = lambda r, p=p: r["profile"] == p
        a, n, t = sm("v5", fl).mean(), sm("never", fl).mean(), sm("v4", fl).mean()
        rr = [r for r in rows if r["strategy"] == "v5" and r["profile"] == p]
        L.append(f"| {p} | {100 * (a / n - 1):+.1f}% | {100 * (a / t - 1):+.1f}% | {np.median([abs(r['f_hat'] - r['f']) for r in rr]):.3f} | "
                 f"{np.median([abs(r['q_hat'] - r['q']) for r in rr]):.3f} |")
    out = os.path.join("results", f"fr11_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
