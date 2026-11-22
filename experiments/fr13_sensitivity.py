"""FR13: the gradual-drift scenario, and sensitivity to cost weights.

This is DESCRIPTIVE sensitivity analysis, not a confirmatory hypothesis test -- no pre-registration is written
for it, consistent with how exploratory/descriptive sweeps are already labelled elsewhere in this repo (e.g.
H-A6 in PREREGISTRATION_ablation_v51.md, H-R3/H-R4 in PREREGISTRATION_rho.md). Nothing here is tuned against
these results: the rule (Rule_v5_1) and baselines were built and confirmed on other scenarios/grids before this
script existed.

Part A: does the headline rule (Rule_v5_1, FR19) still behave sensibly on a GRADUAL onset (S2_gradual, already
defined in ereplan/config.py/env.py, used only in unit tests until now), not just the sudden drops tested so far?
Part B: how sensitive is total loss to the two cost weights the proposal's own risk register flags (wrong-answer
cost leak_mult, and check price check_frac), reported across their whole range rather than at one setting.

Usage: python experiments/fr13_sensitivity.py
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import os as _os
_os.environ["EREPLAN_FMAX"] = "0.5"      # simulator studies use the default f grid; fixed here so a shell setting cannot change results
import itertools, json, os, time
from multiprocessing import Pool
import numpy as np

from ereplan.config import Setting
from ereplan.runner import run
from ereplan import rule_v5s, rule_rho, rule_v5_1  # noqa: F401

SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
SEEDS = tuple(range(1950, 1970))          # 20 seeds, same convention as the confirmatory tests
STRATS_A = {"never": ("B2_never", dict(window=30)), "always": ("B1_always", dict(window=30)),
            "cusum": ("B4_cusum", dict(h=6, p1=0.8)), "v4": ("Rule_v4_fa", dict(SESSION, q_prior_strength=3.0)),
            "v5": ("Rule_v5_x", dict(SESSION)), "v5_1": ("Rule_v5_1", dict(SESSION))}


def _s(**kw):
    base = dict(q_true=0.8, q_assumed=0.8, check_frac=0.15, leak_mult=1.0, false_alarm=0.1, fa_persistence=0.5,
                xc_shared=0.3, third_source_frac=0.3, audit_frac=0.05, n_tasks=200)
    return Setting().with_(**{**base, **kw})


def _job_a(a):
    key, seed = a
    name, params = STRATS_A[key]
    r = run(name, dict(params), _s(), "S2_gradual", seed)
    return dict(strategy=key, seed=seed, loss=r["total_loss_fail"], leak_rate=r["leak_rate"],
                fail_rate=r["fail_rate"], checks=r["checks_per_task"])


def part_a(procs):
    jobs = [(k, sd) for k in STRATS_A for sd in SEEDS]
    with Pool(procs) as pool:
        rows = pool.map(_job_a, jobs)
    by = {}
    for r in rows:
        by.setdefault(r["strategy"], []).append(r)
    L = ["## Part A: gradual-drift scenario (S2_gradual), 20 seeds, descriptive", "",
         "| Strategy | total loss | leak rate | failed tasks | checks/task |", "|---|---|---|---|---|"]
    for k in STRATS_A:
        rr = by[k]
        L.append(f"| {k} | {np.mean([r['loss'] for r in rr]):.1f} | {np.mean([r['leak_rate'] for r in rr]):.1%} | "
                 f"{np.mean([r['fail_rate'] for r in rr]):.1%} | {np.mean([r['checks'] for r in rr]):.2f} |")
    v51 = np.mean([r["loss"] for r in by["v5_1"]])
    best_baseline = min(np.mean([r["loss"] for r in by[k]]) for k in ("never", "always", "cusum", "v4", "v5"))
    L += ["", f"Observation (descriptive, not a hypothesis test): Rule_v5_1's mean loss ({v51:.1f}) vs. the best "
              f"of the simpler baselines on this scenario ({best_baseline:.1f}) -- "
              f"{'v5_1 is lower' if v51 < best_baseline else 'v5_1 is NOT the lowest here'}. Reported as observed, "
              f"whichever way it comes out."]
    return rows, "\n".join(L)


LEAK_MULTS = (0.5, 1.0, 2.0, 3.0, 5.0)
CHECK_FRACS = (0.05, 0.10, 0.15, 0.20, 0.30)


def _job_b(a):
    key, lm, cf, seed = a
    name, params = STRATS_A[key]
    s = _s(leak_mult=lm, check_frac=cf)
    r = run(name, dict(params), s, "S1_sudden", seed)
    return dict(strategy=key, leak_mult=lm, check_frac=cf, seed=seed, loss=r["total_loss_fail"])


def part_b(procs):
    keys = ("v4", "v5", "v5_1")
    jobs = [(k, lm, cf, sd) for k in keys for lm, cf, sd in itertools.product(LEAK_MULTS, CHECK_FRACS, SEEDS)]
    with Pool(procs) as pool:
        rows = pool.map(_job_b, jobs)
    by = {}
    for r in rows:
        by.setdefault((r["strategy"], r["leak_mult"], r["check_frac"]), []).append(r["loss"])
    L = ["", "## Part B: sensitivity to cost weights (leak_mult x check_frac), S1_sudden, 20 seeds, descriptive", "",
         "Total loss per task, mean over seeds. Rows: wrong-answer cost (leak_mult, in task-cost units). "
         "Columns: check price as a share of mean tool price (check_frac).", ""]
    for key in keys:
        L += [f"### {key}", "", "| leak_mult \\ check_frac | " + " | ".join(f"{c:.2f}" for c in CHECK_FRACS) + " |",
              "|---|" + "---|" * len(CHECK_FRACS)]
        for lm in LEAK_MULTS:
            row = [f"{np.mean(by[(key, lm, cf)]):.1f}" for cf in CHECK_FRACS]
            L.append(f"| {lm:.1f} | " + " | ".join(row) + " |")
        L.append("")
    # where does v5_1 stop beating v4? report the check_frac x leak_mult cells where v5_1 >= v4 (a limit, not hidden)
    worse = [(lm, cf) for lm, cf in itertools.product(LEAK_MULTS, CHECK_FRACS)
             if np.mean(by[("v5_1", lm, cf)]) >= np.mean(by[("v4", lm, cf)])]
    L += [f"Cells where v5_1's mean loss is NOT below v4's (reported as a limit, not omitted): "
          f"{worse if worse else 'none in this grid'}."]
    return rows, "\n".join(L)


def main():
    procs = os.cpu_count() or 2
    t0 = time.time()
    rows_a, rep_a = part_a(procs)
    rows_b, rep_b = part_b(procs)
    out = os.path.join("results", f"fr13_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump({"part_a": rows_a, "part_b": rows_b}, open(os.path.join(out, "rows.json"), "w"))
    rep = (f"# FR13: gradual drift and cost-weight sensitivity (descriptive, not confirmatory)\n\n"
           f"{time.time() - t0:.0f} s total.\n\n" + rep_a + "\n" + rep_b)
    open(os.path.join(out, "report.md"), "w").write(rep)
    print(rep); print("Saved to", out)


if __name__ == "__main__":
    main()
