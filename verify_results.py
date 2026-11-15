"""Re-run a random sample of the saved confirmatory runs on THIS machine and compare every number exactly.

    python verify_results.py          # 12 runs per experiment, a few minutes
    python verify_results.py --n 60   # a larger sample

If every line says IDENTICAL, your machine reproduces the reported results. No model is called.
"""
import argparse, glob, json, os, random, subprocess, sys
# The f grid (EREPLAN_FMAX) is fixed when the code is first imported: 0.5 for the simulator studies (FR20, FR21),
# 0.95 for the studies with real-checker rates (FR11, FreshQA). So each group is verified in its own process.
GROUPS = {"sim": ("0.5", (0, 1, 4, 5, 6, 7, 8, 9, 10, 11)), "real": ("0.95", (2, 3))}


def latest(pattern):
    d = sorted(glob.glob(os.path.join("results", pattern)))
    return json.load(open(os.path.join(d[-1], "rows.json"))), d[-1]


def main(n, group):
    if group is None:
        codes = [subprocess.call([sys.executable, __file__, "--n", str(n), "--group", g],
                                 env=dict(os.environ, EREPLAN_FMAX=GROUPS[g][0])) for g in GROUPS]
        print("\nThis machine reproduces the saved results." if not any(codes) else
              "\nSome runs differ. Note your Python, numpy and scipy versions (python check_local.py) and report it.")
        sys.exit(1 if any(codes) else 0)
    if group == "sim":                       # import only this group's drivers: each fixes its own f grid on import
        import run_ablation, run_rho, run_anytool, run_boundary
        from ereplan import v5_exp, costbench_v5, core2_exp, bayes_exp
    else:
        import run_fr11, run_freshqa_confirm as fq
    rnd, bad = random.Random(0), 0
    specs = [
        ("FR21 ablation", "ablation_confirm_*", lambda r: run_ablation._job((r["strategy"], r["drop"], r["q"], r["f"], r["pi"], r["seed"]))),
        ("FR20 learning rho", "rho_confirm_*", lambda r: run_rho._job((r["strategy"], r["group"], r["true_rho"], r["drop"], r["q"], r["f"], r["seed"]))),
        ("FR11 CostBench, real-checker rates", "fr11_confirm_*", lambda r: next(
            x for x in run_fr11.job((r["profile"], r["drop"], r["leak_mult"], r["gap"], r["check_frac"], r["seed"])) if x["strategy"] == r["strategy"])),
        ("FR16/17 FreshQA, real judges", "freshqa_confirm_*", lambda r: fq.job((r["strategy"], r["judge"], r["stream"], r["p_stale"], r["b_price"], r["seed"]))),
        ("FR18 any tool can degrade", "anytool_confirm_*", lambda r: run_anytool.job((r["strategy"], r["scenario"], r["q"], r["leak_mult"], r["seed"]))),
        ("Boundary map", "boundary_confirm_*", lambda r: run_boundary.job((r["strategy"], r["p_deg"], r["premium"], r["leak_mult"], r["seed"]))),
        # October experiments (added 13 Nov 2026)
        ("Rule v5, simulator (27 Oct)", "v5_confirm_*", lambda r: v5_exp._job((r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"], r["seed"]))),
        ("CostBench, check at 15% (28 Oct)", "costbench_v5_confirm_*", lambda r: next(
            x for x in costbench_v5._job((r["drop"], r["q"], r["f"], r["pi"], r["leak_mult"], r["gap"], r["seed"])) if x["strategy"] == r["strategy"])),
        ("CostBench, check at 5% (28 Oct)", "costbench_v5_cheap_*", lambda r: next(
            x for x in costbench_v5._job((r["drop"], r["q"], r["f"], r["pi"], r["leak_mult"], r["gap"], r["seed"], r["check_frac"])) if x["strategy"] == r["strategy"])),
        ("Published-method baselines (31 Oct)", "core2_confirm_*", lambda r: core2_exp._job(
            (r["strategy"], *core2_exp.strategies()[r["strategy"]], (r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"]), r["seed"]))),
        ("Rule v5 with unreliable comparisons (27 Oct)", "v5_stress_*", lambda r: v5_exp._job_stress((r["strategy"], r["drop"], r["leak_mult"], r["f"], r["e"], r["seed"]))),
        ("Bayes-optimal comparison (27 Oct)", "bayes_confirm_*", lambda r: bayes_exp._job((r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["seed"]))),
    ]
    for title, pat, redo in [specs[i] for i in GROUPS[group][1]]:
        rows, folder = latest(pat)
        diff = 0
        for r in rnd.sample(rows, min(n, len(rows))):
            new = redo(r)
            diff += any(new[k] != r[k] for k in ("loss", "leak_rate", "fail_rate", "checks") if k in r)
        bad += diff
        print(f"{'IDENTICAL' if diff == 0 else 'DIFFERENT'}  {title}: {min(n, len(rows)) - diff}/{min(n, len(rows))} sampled runs match {folder}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--group", choices=tuple(GROUPS), default=None)
    a = ap.parse_args(); main(a.n, a.group)
