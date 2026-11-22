"""Measure the cross-check assumptions A1-A3 on REAL tool pairs. See PREREGISTRATION_realtools.md (Study M).

Why: the rule treats "the flagged answer and a second tool's answer agree" as evidence of a false alarm. That needs
  A1  two wrong answers rarely agree (sigma small),
  A2  when the answers disagree, the second tool is more likely right,
  A3  the comparison of two answers is itself reliable (e small).
Until now these were only varied in simulation. Here they are measured on real models.

Part 1 (GSM8K, real solver services from tools_live.py): three solver models answer the same problems; a fourth model
         (the checker) judges the cheap solvers' answers. Numbers are compared exactly, so A3 holds by construction.
Part 2 (FreshQA): an LLM comparator says whether the old and the new knowledge-base entry give the same answer;
         its errors against the dataset's own change labels estimate e (A3).

Usage:  python experiments/measure_assumptions.py dev        # 10 problems, 20 FreshQA pairs: checks the pipeline (not results)
        python experiments/measure_assumptions.py confirm    # the pre-registered measurement (overnight)
Every model answer is cached (data/processed/d1_cache_*.json), so an interrupted run can simply be started again.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import json, math, os, sys, time
from scipy.stats import binomtest
from ereplan.tools_live import SolverService, Checker, Comparator, load_gsm8k, load_freshqa, same_number, LLM

SOLVERS = {"qwen1.5b": "qwen2.5:1.5b", "qwen3b": "qwen2.5:3b", "phi4": "phi4-mini"}
CHECKER = "llama3.1:8b"
COMPARATOR = "phi4-mini"
PAIRS = [("qwen1.5b", "phi4"), ("qwen3b", "phi4"), ("qwen1.5b", "qwen3b")]   # (flagged tool, alternative)
SIZES = {"dev": (10, 20), "confirm": (200, None)}
SUBSET_SEED = 11          # which GSM8K problems: a fixed shuffle, different from the smoke test (seed 0)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k / n:.3f} (95% CI {lo:.3f} to {hi:.3f})" if n else "0/0 (undefined)"


def part1(n, llms, log):
    tasks = load_gsm8k(n, seed=SUBSET_SEED)
    tools = {k: SolverService(k, 0, m, llms=llms) for k, m in SOLVERS.items()}
    chk = Checker(CHECKER, price=0, llms=llms)
    rows, t0 = [], time.time()
    for i, task in enumerate(tasks):
        r = {"id": task["id"], "truth": task["truth"]}
        for k, tool in tools.items():
            out = tool(task)
            r[k] = {"value": out["value"], "correct": out["correct"], "loud": out["loud"], "s": out["seconds"]}
            if k in ("qwen1.5b", "qwen3b") and not out["loud"]:
                r[k]["flag"] = chk(task, out, "maths")["flag"]
        rows.append(r)
        if (i + 1) % 10 == 0:
            for l in llms.values():
                l.save()
            log(f"  GSM8K {i + 1}/{n} problems ({time.time() - t0:.0f} s)")
    for l in llms.values():
        l.save()
    return rows


def part1_report(rows):
    L = ["## Part 1: GSM8K solver pairs (exact numeric comparison, so e = 0 by construction)", "",
         "| Model | accuracy | loud (no number) |", "|---|---|---|"]
    for k in SOLVERS:
        ok = [r[k] for r in rows]
        L.append(f"| {SOLVERS[k]} | {sum(o['correct'] for o in ok) / len(ok):.3f} | {sum(o['loud'] for o in ok) / len(ok):.3f} |")
    L += ["", f"Checker {CHECKER} on the cheap solvers' answers (not loud):", "", "| Flagged tool | catch rate q | false-alarm rate f |", "|---|---|---|"]
    for a in ("qwen1.5b", "qwen3b"):
        w = [r[a] for r in rows if not r[a]["loud"] and not r[a]["correct"]]
        c = [r[a] for r in rows if not r[a]["loud"] and r[a]["correct"]]
        L.append(f"| {SOLVERS[a]} | {fmt(sum(o['flag'] for o in w), len(w))} | {fmt(sum(o['flag'] for o in c), len(c))} |")
    L += ["", "| Pair (flagged, alternative) | A1: both wrong and agree (sigma) | A2: alternative right when they disagree, all | A2: same, only when the checker flagged |",
          "|---|---|---|---|"]
    res = {}
    for a, b in PAIRS:
        valid = [r for r in rows if not r[a]["loud"] and not r[b]["loud"]]
        both_wrong = [r for r in valid if not r[a]["correct"] and not r[b]["correct"]]
        agree_wrong = sum(same_number(r[a]["value"], r[b]["value"]) for r in both_wrong)
        dis = [r for r in valid if not same_number(r[a]["value"], r[b]["value"])]
        dis_alt_right = sum(r[b]["correct"] for r in dis)
        disf = [r for r in dis if r[a].get("flag")]
        disf_alt_right = sum(r[b]["correct"] for r in disf)
        p2 = binomtest(disf_alt_right, len(disf), 0.5, alternative="greater").pvalue if disf else float("nan")
        res[(a, b)] = dict(sig=(agree_wrong, len(both_wrong)), a2=(disf_alt_right, len(disf), p2))
        L.append(f"| {SOLVERS[a]} -> {SOLVERS[b]} | {fmt(agree_wrong, len(both_wrong))} | {fmt(dis_alt_right, len(dis))} | "
                 f"{fmt(disf_alt_right, len(disf))}, one-sided binomial p = {p2:.2g} |")
    return L, res


def part2(m, llms, log):
    rows = load_freshqa()
    rows = rows if m is None else [r for r in rows if r["changed"]][: m // 2] + [r for r in rows if not r["changed"]][: m - m // 2]
    cmp_, out, t0 = Comparator(COMPARATOR, llms=llms), [], time.time()
    for i, t in enumerate(rows):
        same = cmp_(t, {"text": t["old"]}, {"text": t["new"]}, "questions")
        out.append({"id": t["id"], "changed": t["changed"], "comparator_same": same})
        if (i + 1) % 50 == 0:
            for l in llms.values():
                l.save()
            log(f"  FreshQA {i + 1}/{len(rows)} pairs ({time.time() - t0:.0f} s)")
    for l in llms.values():
        l.save()
    return out


def part2_report(rows):
    ch = [r for r in rows if r["changed"]]; un = [r for r in rows if not r["changed"]]
    e1 = sum(r["comparator_same"] for r in ch); e2 = sum(not r["comparator_same"] for r in un)
    L = ["", f"## Part 2: FreshQA comparator ({COMPARATOR}) against the dataset's change labels", "",
         "| Case | comparator wrong |", "|---|---|",
         f"| answer changed, comparator says 'same' | {fmt(e1, len(ch))} |",
         f"| answer unchanged, comparator says 'different' | {fmt(e2, len(un))} |",
         f"| all pairs (e) | {fmt(e1 + e2, len(rows))} |", "",
         "Caveat: the change labels are not hand-checked; at least one changed-labelled pair (fq42) has entries with the same "
         "meaning, which would count as a comparator error here although the comparator is right."]
    return L, (e1 + e2, len(rows))


def main(which):
    n, m = SIZES[which]
    out = os.path.join("results", f"assumptions_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    logf = open(os.path.join(out, "progress.log"), "w")
    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()
    llms = {}
    t0 = time.time()
    log(f"Part 1: {n} GSM8K problems x {len(SOLVERS)} solvers + checker {CHECKER}")
    r1 = part1(n, llms, log)
    log(f"Part 2: FreshQA comparator {COMPARATOR}")
    r2 = part2(m, llms, log)
    json.dump(dict(part1=r1, part2=r2, solvers=SOLVERS, checker=CHECKER, comparator=COMPARATOR, subset_seed=SUBSET_SEED),
              open(os.path.join(out, "rows.json"), "w"), indent=1)
    L1, res = part1_report(r1); L2, (ek, en) = part2_report(r2)
    L = [f"# Cross-check assumptions measured on real tools ({which})", "",
         f"{n} GSM8K problems (subset seed {SUBSET_SEED}); {len(r2)} FreshQA pairs; temperature 0; {time.time() - t0:.0f} s.", ""] + L1 + L2
    if which == "confirm":
        L += ["", "## Pre-registered decisions (PREREGISTRATION_realtools.md, Study M)"]
        for a, b in PAIRS[:2]:
            k, nn = res[(a, b)]["sig"]; hi = wilson(k, nn)[1]
            L.append(f"- M-A1 {SOLVERS[a]} -> {SOLVERS[b]}: sigma upper 95% bound {hi:.3f} -> "
                     f"**{'COVERED by the robustness test (<= 0.9)' if hi <= 0.9 else 'NOT COVERED (> 0.9)'}**")
        for a, b in PAIRS[:2]:
            k, nn, p = res[(a, b)]["a2"]
            L.append(f"- M-A2 {SOLVERS[a]} -> {SOLVERS[b]}: alternative right in {k}/{nn} flagged disagreements, p = {p:.2g} -> "
                     f"**{'CONFIRMED' if nn and p < 0.05 else 'NOT CONFIRMED'}**")
        hi = wilson(ek, en)[1]
        L.append(f"- M-A3 FreshQA comparator error: upper 95% bound {hi:.3f} -> "
                 f"**{'COVERED by the robustness test (<= 0.2)' if hi <= 0.2 else 'NOT COVERED (> 0.2)'}**")
        k, nn = res[("qwen1.5b", "qwen3b")]["sig"]
        L.append(f"- Descriptive, same-family pair qwen2.5:1.5b -> qwen2.5:3b: sigma {fmt(k, nn)}")
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
