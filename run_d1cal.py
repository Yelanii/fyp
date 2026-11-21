"""D1-cal: the rule on live model-backed tools with a labelled calibration prior. See PREREGISTRATION_d1cal.md.

In D1 the rule learned the checker's false-alarm rate without labels and over-estimated it (median 0.125 against 0.046
calibrated), so it checked rarely and did not beat never checking. The rule already needs a one-off labelled sample
(to check assumption A2). This test gives the rule the labelled calibration of Study M (problems 1-200, disjoint from
D1's problems) as the PRIOR of its checker memory, instead of a vague prior; the rule then keeps learning from its own
cross-checks as before. Nothing else changes: same answers (data/processed/d1_table.json), same conditions, same loss.

Usage:  python run_d1cal.py dev       # seeds 7010-7014, pipeline check (not results)
        python run_d1cal.py confirm   # seeds 7200-7219, the pre-registered test (run once)
Needs the cached D1 answers (python -m ereplan.agent_live prepare). No model is called.
"""
import itertools, json, os, sys, time
import numpy as np
from scipy.stats import wilcoxon
from ereplan import agent_live as d
from ereplan.v5_exp import SESSION

# Study M labelled calibration (llama3.1:8b on the Qwen solvers): caught 68 of 151 wrong, flagged 11 of 239 right.
Q_CAL, Q_N = d.TOLD_Q, 151
F_CAL, F_N = d.TOLD_F, 239
d.STRATS["v5_cal"] = ("Rule_v5_x", dict(SESSION, q_prior_mean=Q_CAL, q_prior_strength=float(Q_N),
                                        f_prior_mean=F_CAL, f_prior_strength=float(F_N)), "true")
d.STRATS["v5_cal_small"] = ("Rule_v5_x", dict(SESSION, q_prior_mean=Q_CAL, q_prior_strength=Q_N / 5,
                                              f_prior_mean=F_CAL, f_prior_strength=F_N / 5), "true")
d.RNG_ALIAS.update({"v5_cal": "v5", "v5_cal_small": "v5"})
KEYS = ("never", "cusum", "v4", "always_x", "v5_told", "v5", "v5_cal", "v5_cal_small", "fix_B")
SEEDS = {"dev": tuple(range(7010, 7015)), "confirm": tuple(range(7200, 7220))}


def run(which, table=None):
    table = table or json.load(open(d.TABLE))
    seeds = SEEDS[which]
    t0 = time.time()
    rows = [d.run_one(table, k, sd, pb, Lc) for k, sd, (Lc, pb) in itertools.product(KEYS, seeds, d.CONDS)]
    sm = lambda k, f=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and f(r)]) for sd in seeds])
    av = lambda k, field: np.mean([r[field] for r in rows if r["strategy"] == k and r[field] is not None])
    L = [f"# D1-cal: the rule with a labelled calibration prior on live tools ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. Prior from Study M: q {Q_CAL:.3f} (n={Q_N}), f {F_CAL:.3f} (n={F_N}); "
         f"v5_cal_small uses one fifth of that weight.", "",
         "| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task | median learned f |",
         "|---|---|---|---|---|---|---|"]
    for k in KEYS:
        fh = [r["f_hat"] for r in rows if r["strategy"] == k and r["f_hat"] is not None]
        L.append(f"| {k} | {sm(k).mean():.1f} | {100 * av(k, 'wrong_rate'):.1f}% | {100 * av(k, 'fail_rate'):.1f}% | "
                 f"{av(k, 'checks_per_task'):.2f} | {av(k, 'xchecks_per_task'):.2f} | {np.median(fh):.3f} |" if fh else
                 f"| {k} | {sm(k).mean():.1f} | {100 * av(k, 'wrong_rate'):.1f}% | {100 * av(k, 'fail_rate'):.1f}% | "
                 f"{av(k, 'checks_per_task'):.2f} | {av(k, 'xchecks_per_task'):.2f} | - |")
    L += ["", "| B price | wrong-answer cost | " + " | ".join(KEYS) + " |", "|---|---|" + "---|" * len(KEYS)]
    for Lc, pb in d.CONDS:
        L.append(f"| {pb:g} | {Lc:g} | " + " | ".join(f"{sm(k, lambda r: r['price_b'] == pb and r['L'] == Lc).mean():.1f}" for k in KEYS) + " |")
    tests = {"H-C1 the calibrated rule below never checking": ("v5_cal", "never"),
             "H-C2 the calibrated rule below the retrying rule told q and f": ("v5_cal", "v4")}
    ps = {h: (1.0 if np.allclose(sm(a), sm(b)) else float(wilcoxon(sm(a), sm(b), alternative="less").pvalue)) for h, (a, b) in tests.items()}
    order = sorted(ps, key=ps.get); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and ps[h] < 0.05 / (len(order) - j); stop = stop or not holm[h]
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_d1cal.md)", ""]
    for h, (a, b) in tests.items():
        x, y = sm(a), sm(b); lo, hi = d._boot(x, y)
        L.append(f"- {h}: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%), "
                 f"one-sided Wilcoxon p = {ps[h]:.2g}, Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    for k in ("v5", "v5_told", "always_x", "cusum", "fix_B", "v5_cal_small"):
        x, y = sm("v5_cal"), sm(k); lo, hi = d._boot(x, y)
        L.append(f"- Descriptive: calibrated rule vs {k}: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%)")
    x, y = sm("v5_cal_small"), sm("never"); lo, hi = d._boot(x, y)
    L.append(f"- Descriptive: v5_cal_small vs never: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%)")
    outdir = os.path.join("results", f"d1cal_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(outdir, exist_ok=True)
    json.dump(rows, open(os.path.join(outdir, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(outdir, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", outdir)
    return rows


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "dev")
