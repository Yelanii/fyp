"""Study F: is it the model family or the accuracy of the second tool? See PREREGISTRATION_family.md.

Studies M and M2 found that, for a flagged qwen2.5:1.5b answer, phi4-mini (another family) was the better guess on
disagreement but qwen2.5:3b (same family) was not reliably so. phi4-mini is also far more accurate (0.86 vs 0.69), so
family and accuracy are confounded. This study adds llama3.2:3b, a different family with accuracy close to
qwen2.5:3b, on the same 300 problems (201-500 of the subset-seed-11 shuffle), and compares the alternatives by their
ERROR LIFT, which does not depend on accuracy:

    lift(X) = P(X wrong | qwen2.5:1.5b wrong) / P(X wrong)

A lift of 1 means X's mistakes are unrelated to qwen2.5:1.5b's; above 1 means they tend to fail on the same problems.

Usage:  python measure_family.py dev       # 10 problems: checks the pipeline (not results)
        python measure_family.py confirm   # the pre-registered measurement
Needs `ollama pull llama3.2:3b`. The other models' answers are read from Study M2 (results/assumptions_ext_confirm_*).
"""
import glob, json, os, sys, time
import numpy as np
from scipy.stats import binomtest
from ereplan.tools_live import SolverService, load_gsm8k, same_number
from measure_assumptions import SUBSET_SEED, wilson, fmt

NEW = ("llama3.2", "llama3.2:3b")
FIRST, N = 200, 300
SIZES = {"dev": 10, "confirm": N}
BOOT, BOOT_SEED = 10000, 7


def lift(rows, base, alt):
    valid = [r for r in rows if not r[base]["loud"] and not r[alt]["loud"]]
    bw = np.array([not r[base]["correct"] for r in valid])
    aw = np.array([not r[alt]["correct"] for r in valid])
    return (aw[bw].mean() / aw.mean()) if aw.mean() > 0 and bw.any() else float("nan"), bw, aw


def boot_lift_diff(rows, base, a1, a2):
    """Problem-level paired bootstrap of lift(a1) - lift(a2) over problems valid for all three models."""
    valid = [r for r in rows if not r[base]["loud"] and not r[a1]["loud"] and not r[a2]["loud"]]
    bw = np.array([not r[base]["correct"] for r in valid]); w1 = np.array([not r[a1]["correct"] for r in valid])
    w2 = np.array([not r[a2]["correct"] for r in valid])
    rng = np.random.default_rng(BOOT_SEED); d = []
    for _ in range(BOOT):
        ix = rng.integers(0, len(valid), len(valid)); b, x, y = bw[ix], w1[ix], w2[ix]
        if b.any() and x.mean() > 0 and y.mean() > 0:
            d.append(x[b].mean() / x.mean() - y[b].mean() / y.mean())
    est = (w1[bw].mean() / w1.mean()) - (w2[bw].mean() / w2.mean())
    return est, np.percentile(d, 2.5), np.percentile(d, 97.5), len(valid)


def a2(rows, base, alt):
    dis = [r for r in rows if not r[base]["loud"] and not r[alt]["loud"] and r[base].get("flag")
           and not same_number(r[base]["value"], r[alt]["value"])]
    k = sum(r[alt]["correct"] for r in dis)
    return k, len(dis), (binomtest(k, len(dis), 0.5, alternative="greater").pvalue if dis else float("nan"))


def main(which):
    n = SIZES[which]
    prev = sorted(glob.glob(os.path.join("results", "assumptions_ext_confirm_*", "rows.json")))
    if not prev:
        sys.exit("Study M2 rows not found (results/assumptions_ext_confirm_*/rows.json).")
    m2 = json.load(open(prev[-1]))["new"][:n]
    out = os.path.join("results", f"family_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    logf = open(os.path.join(out, "progress.log"), "w")

    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    tasks = load_gsm8k(FIRST + n, seed=SUBSET_SEED)[FIRST:]
    assert [t["id"] for t in tasks] == [r["id"] for r in m2], "problem order differs from Study M2"
    llms, t0 = {}, time.time()
    svc = SolverService(NEW[0], 0, NEW[1], llms=llms)
    for i, task in enumerate(tasks):
        o = svc(task)
        m2[i][NEW[0]] = {"value": o["value"], "correct": o["correct"], "loud": o["loud"]}
        if (i + 1) % 10 == 0:
            for l in llms.values():
                l.save()
            log(f"  {NEW[1]}: {i + 1}/{n} problems ({time.time() - t0:.0f} s)")
    for l in llms.values():
        l.save()
    json.dump(dict(rows=m2, study_m2_rows=prev[-1]), open(os.path.join(out, "rows.json"), "w"), indent=1)
    alts = {"qwen3b": "qwen2.5:3b (same family)", NEW[0]: f"{NEW[1]} (other family)", "phi4": "phi4-mini (other family)"}
    L = [f"# Study F: model family or accuracy? ({which})", "", f"{n} problems (201-{FIRST + n}); temperature 0; {time.time() - t0:.0f} s.", "",
         "| Alternative to qwen2.5:1.5b | accuracy | P(wrong given 1.5B wrong) | P(wrong) | error lift | A2: right on flagged disagreements |",
         "|---|---|---|---|---|---|"]
    for k, name in alts.items():
        lf, bw, aw = lift(m2, "qwen1.5b", k)
        acc = np.mean([r[k]["correct"] for r in m2])
        kk, nn, p = a2(m2, "qwen1.5b", k)
        L.append(f"| {name} | {acc:.3f} | {aw[bw].mean():.3f} | {aw.mean():.3f} | {lf:.2f} | {fmt(kk, nn)}, p = {p:.2g} |")
    est, lo, hi, nv = boot_lift_diff(m2, "qwen1.5b", "qwen3b", NEW[0])
    L += ["", f"Lift(qwen2.5:3b) - lift({NEW[1]}): {est:+.2f} (95% bootstrap CI {lo:+.2f} to {hi:+.2f}; {nv} problems valid for all three)."]
    if which == "confirm":
        L += ["", "## Pre-registered decisions (PREREGISTRATION_family.md)",
              f"- H-F1 same-family errors are more related: lift(qwen2.5:3b) - lift({NEW[1]}) > 0 with the 95% CI above 0 -> "
              f"**{'CONFIRMED' if lo > 0 else 'NOT CONFIRMED'}**"]
        kk, nn, p = a2(m2, "qwen1.5b", NEW[0])
        L.append(f"- H-F2 {NEW[1]} is the better guess on flagged disagreements: {kk}/{nn}, one-sided binomial p = {p:.2g} -> "
                 f"**{'CONFIRMED' if nn and p < 0.05 else 'NOT CONFIRMED'}**")
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
