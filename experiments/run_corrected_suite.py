"""Corrected-rule suite. See PREREGISTRATION_corrected_suite.md.

Re-runs every confirmatory experiment that involves the proposed rule, with the corrected check criterion
(net protection value, EREPLAN_NETPV=1), on fresh seeds, with the same designs, hypotheses and analysis code as
the original pre-registrations. Nothing else is changed.

Usage (from the repository root):
    python experiments/run_corrected_suite.py list           # show the experiments, their seeds and rough run times
    python experiments/run_corrected_suite.py all            # run everything, one after another (overnight)
    python experiments/run_corrected_suite.py one fr11       # run one experiment
    python experiments/run_corrected_suite.py some sim core2 fr11

Each experiment runs in its own Python process, because the simulator studies and the real-checker studies need
different settings of EREPLAN_FMAX. Results are saved as results/<name>_confirm_<time>_netpv, and the hypothesis
lines of all reports are collected in results/corrected_suite_summary_<time>.md.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import importlib, os, subprocess, sys, time

R = lambda a, n: tuple(range(a, a + n))
# name: (module, attribute holding the confirmatory seeds, new seeds, how to start it, rough minutes on a 2-core machine)
SUITE = {
    "sim":      ("ereplan.v5_exp",       "TEST_SEEDS",   R(8200, 20), ("main", ["confirm"]), 67),
    "stress":   ("ereplan.v5_exp",       "STRESS_SEEDS", R(8220, 10), ("main", ["stress"]),   4),
    "bayes":    ("ereplan.bayes_exp",    "TEST_SEEDS",   R(8240, 20), ("main", ["confirm"]), 18),
    "core2":    ("ereplan.core2_exp",    "TEST_SEEDS",   R(8300, 20), ("confirm", None),     56),
    "cb15":     ("ereplan.costbench_v5", "TEST_SEEDS",   R(8340, 18), ("main", ["confirm"]), 11),
    "cb5":      ("ereplan.costbench_v5", "CHEAP_SEEDS",  R(8360, 18), ("main", ["cheap"]),   23),
    "fr11":     ("run_fr11",             "SEEDS",        R(8400, 18), ("main", "confirm"),   16),
    "robust":   ("run_robustness",       "SEEDS",        R(8500, 20), ("main", "confirm"),   75),
    "freshqa":  ("run_freshqa_confirm",  "SEEDS",        R(8600, 20), ("main", "confirm"),   17),
    "anytool":  ("run_anytool",          "SEEDS",        R(8700, 20), ("main", "confirm"),    7),
    "boundary": ("run_boundary",         "SEEDS",        R(8800, 20), ("main", "confirm"),    9),
    "ablation": ("run_ablation",         "TEST_SEEDS",   R(8900, 20), ("main", ["confirm"]), 45),
    "rho":      ("run_rho",              "TEST_SEEDS",   R(9000, 20), ("main", ["confirm"]), 107),
}


def run_one(name, seeds=None):
    """Runs inside its own process: switch the corrected criterion on, swap in the fresh seeds, start the experiment."""
    os.environ["EREPLAN_NETPV"] = "1"                       # must be set before the rule code is imported
    mod_name, attr, new_seeds, (fn, arg), _ = SUITE[name]
    new_seeds = tuple(seeds) if seeds else new_seeds
    mod = importlib.import_module(mod_name)
    from ereplan import crosscheck
    assert crosscheck.NETPV, "the corrected criterion is not switched on"
    if isinstance(getattr(mod, attr), dict):
        getattr(mod, attr)["confirm"] = new_seeds
    else:
        setattr(mod, attr, new_seeds)
    before = set(os.listdir("results"))
    f = getattr(mod, fn)
    if arg is None:
        f(os.cpu_count() or 2)
    else:
        f(arg)
    for d in sorted(set(os.listdir("results")) - before):   # mark the new result folder
        if not os.path.isdir(os.path.join("results", d)) or d.endswith("_netpv"):
            continue
        os.rename(os.path.join("results", d), os.path.join("results", d + "_netpv"))
        with open(os.path.join("results", d + "_netpv", "NETPV.txt"), "w") as fh:
            fh.write(f"Run by run_corrected_suite.py ({name}) with EREPLAN_NETPV=1 (corrected check criterion).\n"
                     f"Seeds {new_seeds[0]}-{new_seeds[-1]}. See PREREGISTRATION_corrected_suite.md.\n")
        print("Saved to", os.path.join("results", d + "_netpv"))


def summary(names, t_start):
    L = ["# Corrected-rule suite: hypothesis lines from every report", "",
         "All runs used EREPLAN_NETPV=1 (corrected check criterion) and fresh seeds. In these reports, `v5` (and every",
         "rule built on it) is the corrected rule.", ""]
    for name in names:
        folders = sorted(d for d in os.listdir("results") if d.endswith("_netpv")
                         and os.path.getmtime(os.path.join("results", d)) >= t_start
                         and name in open(os.path.join("results", d, "NETPV.txt")).read().split("(")[1].split(")")[0].split())
        for d in folders:
            rep = os.path.join("results", d, "report.md")
            if not os.path.exists(rep):
                continue
            L += [f"## {name}  ({d})", ""]
            L += [ln for ln in open(rep, encoding="utf-8", errors="replace").read().splitlines()
                  if ln.startswith("- H") or ln.startswith("- R-") or ln.startswith("Seeds ")] + [""]
    out = os.path.join("results", f"corrected_suite_summary_{time.strftime('%Y%m%d-%H%M%S')}.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L)); print("Summary saved to", out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        for k, (m, _, sd, _, mins) in SUITE.items():
            print(f"{k:9s} {m:22s} seeds {sd[0]}-{sd[-1]}   about {mins} min")
        print(f"total: about {sum(v[4] for v in SUITE.values()) / 60:.1f} h (measured on a 2-core machine)")
    elif cmd == "_run":                                      # internal: one experiment in this process
        run_one(sys.argv[2], [int(x) for x in sys.argv[3:]] or None)
    else:
        names = list(SUITE) if cmd == "all" else sys.argv[2:]
        assert names and all(n in SUITE for n in names), f"choose from {list(SUITE)}"
        t_start, failed = time.time(), []
        for n in names:
            print(f"\n=== {n} ({time.strftime('%H:%M:%S')}) ===", flush=True)
            env = dict(os.environ, EREPLAN_NETPV="1"); env.pop("EREPLAN_FMAX", None)
            if subprocess.run([sys.executable, __file__, "_run", n], env=env).returncode != 0:
                failed.append(n); print(f"!!! {n} FAILED; continuing with the next experiment", flush=True)
        summary([n for n in names if n not in failed], t_start)
        if failed:
            print("FAILED:", failed, "- run them again with:  python experiments/run_corrected_suite.py some " + " ".join(failed))
