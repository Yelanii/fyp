"""Study M2: the cross-check assumptions A1 and A2 on 300 MORE GSM8K problems.
See PREREGISTRATION_assumptions_ext.md.

Why: Study M (measure_assumptions.py, 200 problems) met all its checks, but its samples were small
(15-16 problems where both tools were wrong; 29-35 flagged disagreements). This adds problems 201-500 of the SAME
fixed shuffle (subset seed 11), with the same models, prompts, checker and analysis.

- The confirmatory decisions use the 300 NEW problems only (never seen before this run).
- The pooled 500 problems are reported as descriptive, because the first 200 have already been seen.
- One model at a time over all problems, so Ollama loads each model once (temperature 0, cached; the order does not
  change any answer).

Usage:  python experiments/measure_assumptions_ext.py dev       # 5 new problems: checks the pipeline (not results)
        python experiments/measure_assumptions_ext.py confirm   # the pre-registered run (overnight)
Interrupted? Run the same command again: every model answer is cached in data/processed/d1_cache_*.json.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import glob, json, os, sys, time
from scipy.stats import binomtest
from ereplan.tools_live import SolverService, Checker, load_gsm8k, same_number
from measure_assumptions import SOLVERS, CHECKER, PAIRS, SUBSET_SEED, wilson, fmt

FIRST = 200                                  # problems 0-199 were Study M
SIZES = {"dev": 5, "confirm": 300}


def run_new(n_new, llms, log):
    tasks = load_gsm8k(FIRST + n_new, seed=SUBSET_SEED)[FIRST:]
    tools = {k: SolverService(k, 0, m, llms=llms) for k, m in SOLVERS.items()}
    chk = Checker(CHECKER, price=0, llms=llms)
    rows = [{"id": t["id"], "truth": t["truth"]} for t in tasks]
    outs, t0 = {}, time.time()

    def save():
        for l in llms.values():
            l.save()

    for k, tool in tools.items():
        for i, task in enumerate(tasks):
            out = tool(task); outs[(k, i)] = out
            rows[i][k] = {"value": out["value"], "correct": out["correct"], "loud": out["loud"], "s": out["seconds"]}
            if (i + 1) % 10 == 0:
                save(); log(f"  solver {SOLVERS[k]}: {i + 1}/{n_new} problems ({time.time() - t0:.0f} s)")
        save()
    for k in ("qwen1.5b", "qwen3b"):
        for i, task in enumerate(tasks):
            if not outs[(k, i)]["loud"]:
                rows[i][k]["flag"] = chk(task, outs[(k, i)], "maths")["flag"]
            if (i + 1) % 10 == 0:
                save(); log(f"  checker {CHECKER} on {SOLVERS[k]}: {i + 1}/{n_new} ({time.time() - t0:.0f} s)")
        save()
    return rows


def pair_stats(rows, a, b):
    valid = [r for r in rows if not r[a]["loud"] and not r[b]["loud"]]
    both_wrong = [r for r in valid if not r[a]["correct"] and not r[b]["correct"]]
    agree_wrong = sum(same_number(r[a]["value"], r[b]["value"]) for r in both_wrong)
    disf = [r for r in valid if not same_number(r[a]["value"], r[b]["value"]) and r[a].get("flag")]
    alt_right = sum(r[b]["correct"] for r in disf)
    p = binomtest(alt_right, len(disf), 0.5, alternative="greater").pvalue if disf else float("nan")
    return (agree_wrong, len(both_wrong)), (alt_right, len(disf), p)


def table(rows, title):
    L = [f"### {title} ({len(rows)} problems)", "",
         "| Model | accuracy | loud |", "|---|---|---|"]
    for k in SOLVERS:
        L.append(f"| {SOLVERS[k]} | {sum(r[k]['correct'] for r in rows) / len(rows):.3f} | "
                 f"{sum(r[k]['loud'] for r in rows) / len(rows):.3f} |")
    L += ["", "| Flagged tool | catch rate q | false-alarm rate f |", "|---|---|---|"]
    for a in ("qwen1.5b", "qwen3b"):
        w = [r[a] for r in rows if not r[a]["loud"] and not r[a]["correct"]]
        c = [r[a] for r in rows if not r[a]["loud"] and r[a]["correct"]]
        L.append(f"| {SOLVERS[a]} | {fmt(sum(o['flag'] for o in w), len(w))} | {fmt(sum(o['flag'] for o in c), len(c))} |")
    L += ["", "| Pair (flagged, alternative) | A1: sigma | A2: alternative right, flagged disagreements |", "|---|---|---|"]
    res = {}
    for a, b in PAIRS:
        (k1, n1), (k2, n2, p) = pair_stats(rows, a, b); res[(a, b)] = ((k1, n1), (k2, n2, p))
        L.append(f"| {SOLVERS[a]} -> {SOLVERS[b]} | {fmt(k1, n1)} | {fmt(k2, n2)}, one-sided binomial p = {p:.2g} |")
    return L, res


def main(which):
    n_new = SIZES[which]
    out = os.path.join("results", f"assumptions_ext_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    logf = open(os.path.join(out, "progress.log"), "w")

    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    prev = sorted(glob.glob(os.path.join("results", "assumptions_confirm_*", "rows.json")))
    if not prev:
        sys.exit("Study M rows not found (results/assumptions_confirm_*/rows.json).")
    old = json.load(open(prev[-1]))["part1"]
    log(f"Study M2: problems {FIRST + 1}-{FIRST + n_new} (subset seed {SUBSET_SEED}); earlier rows from {prev[-1]}")
    t0 = time.time()
    new = run_new(n_new, {}, log)
    json.dump(dict(new=new, solvers=SOLVERS, checker=CHECKER, subset_seed=SUBSET_SEED, first=FIRST, study_m_rows=prev[-1]),
              open(os.path.join(out, "rows.json"), "w"), indent=1)
    Ln, rn = table(new, "New problems only (confirmatory)")
    Lp, rp = table(old + new, "Study M and M2 pooled (descriptive)")
    L = [f"# Cross-check assumptions on real tools, extension ({which})", "",
         f"Problems {FIRST + 1}-{FIRST + n_new} of the subset-seed-{SUBSET_SEED} shuffle; temperature 0; {time.time() - t0:.0f} s.", ""] + Ln + [""] + Lp
    if which == "confirm":
        L += ["", "## Pre-registered decisions (PREREGISTRATION_assumptions_ext.md), new problems only"]
        for a, b in PAIRS[:2]:
            (k, n), (k2, n2, p) = rn[(a, b)]
            hi = wilson(k, n)[1]
            L.append(f"- M2-A1 {SOLVERS[a]} -> {SOLVERS[b]}: sigma upper 95% bound {hi:.3f} -> "
                     f"**{'COVERED (<= 0.9)' if hi <= 0.9 else 'NOT COVERED (> 0.9)'}**")
            L.append(f"- M2-A2 {SOLVERS[a]} -> {SOLVERS[b]}: alternative right in {k2}/{n2} flagged disagreements, p = {p:.2g} -> "
                     f"**{'CONFIRMED' if n2 and p < 0.05 else 'NOT CONFIRMED'}**")
        (k, n), (k2, n2, p) = rn[("qwen1.5b", "qwen3b")]
        L.append(f"- Descriptive, same-family pair: sigma {fmt(k, n)}; A2 {fmt(k2, n2)}, p = {p:.2g}")
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
