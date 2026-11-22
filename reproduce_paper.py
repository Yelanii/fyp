"""Check that this machine reproduces every simulated and replayed result reported in the paper.

    python reproduce_paper.py            # 12 sampled runs per experiment (about 10-20 minutes)
    python reproduce_paper.py --n 40     # a larger sample
    python reproduce_paper.py --only fr11 d1

For each experiment in the paper's experiment table, it opens the saved confirmatory results folder, re-runs a random
sample of its runs with exactly the settings of that experiment, and compares loss, wrong answers kept, failed tasks
and checks per task with the saved values. Every line should say IDENTICAL. No language model is called: the
live-tool experiments replay the cached model answers in data/processed/d1_table.json.

Each experiment runs in its own Python process, because two settings are fixed when the code is first imported:
the f grid (EREPLAN_FMAX) and the check criterion (EREPLAN_NETPV; 1 = the corrected criterion used for every
result of the rule in the paper).

The four model-based measurements (Studies M and M2 and the two GSM8K agent experiments) are reproduced by running
their scripts again, which read every model answer from the cache; see docs/REPRODUCING.md.
"""
import argparse, glob, json, os, random, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "experiments"))   # the experiment scripts

# key: (paper experiment, results folder pattern, which folder if several, EREPLAN_FMAX, EREPLAN_NETPV)
SPECS = {
    "netpv":    ("Corrected against earlier criterion (8100-8119)", "netpv_confirm_*",               "latest", "0.5",  "0"),
    "sim":      ("Label-free rule, simulator (8200-8219)",          "v5_confirm_*_netpv",            "latest", "0.5",  "1"),
    "stress":   ("Unreliable comparisons, A3 (8220-8229)",          "v5_stress_*_netpv",             "latest", "0.5",  "1"),
    "bayes":    ("Distance to Bayes-optimal (8240-8259)",           "bayes_confirm_*_netpv",         "latest", "0.5",  "1"),
    "core2":    ("Published methods (8300-8319)",                   "core2_confirm_*_netpv",         "latest", "0.5",  "1"),
    "cb15":     ("CostBench, check at 15% (8340-8357)",             "costbench_v5_confirm_*_netpv",  "latest", "0.5",  "1"),
    "cb5":      ("CostBench, check at 5% (8360-8377)",              "costbench_v5_cheap_*_netpv",    "latest", "0.5",  "1"),
    "fr11":     ("CostBench, real-checker rates (8400-8417)",       "fr11_confirm_*_netpv",          "latest", "0.95", "1"),
    "robust":   ("Robustness to A1 and A3 (8500-8519)",             "robustness_confirm_*_netpv",    "latest", "0.5",  "1"),
    "freshqa":  ("FreshQA, two judge families (8600-8619)",         "freshqa_confirm_*_netpv",       "latest", "0.95", "1"),
    "anytool":  ("Any tool can degrade (8700-8719)",                "anytool_confirm_*_netpv",       "latest", "0.5",  "1"),
    "boundary": ("Monitoring vs buying (8800-8819)",                "boundary_confirm_*_netpv",      "latest", "0.5",  "1"),
    "ablation": ("Ablation (8900-8919)",                            "ablation_confirm_*_netpv",      "latest", "0.5",  "1"),
    "rho":      ("Learning rho (9000-9019)",                        "rho_confirm_*_netpv",           "latest", "0.5",  "1"),
    "dvsym":    ("Decision-value symmetry (9100-9119)",             "dvsym_confirm_*",               "latest", "0.5",  "1"),
    "detect":   ("Detectability and the boundary (9200-9219)",      "detect_confirm_*",              "first",  "0.95", "1"),
    "exact":    ("Exact step cost (9300-9319)",                     "exactline_confirm_*",           "latest", "0.5",  "1"),
    "d1":       ("Live tools, natural degradation (7100-7119)",     "d1_confirm_*",                  "latest", "0.5",  "1"),
    "d1cal":    ("Live tools, calibrated prior (7200-7219)",        "d1cal_confirm_*",               "latest", "0.5",  "1"),
    "pfsim":    ("Prior fix, simulator (9400-9419)",                "priorfix_sim_confirm_*",        "latest", "0.5",  "1"),
    "pflive":   ("Prior fix, live tools (7300-7319)",               "priorfix_live_confirm_*",       "latest", "0.5",  "1"),
    "pfcb":     ("Prior fix, CostBench (9500-9517)",                "priorfix_cb_confirm_*",         "latest", "0.95", "1"),
    "d1power":  ("Live tools, 200 seeds (7400-7599)",               "d1power_confirm_*",             "latest", "0.5",  "1"),
    "drift":    ("Gradual decline and checker drift (9600-9619)",   "drift_confirm_*",               "latest", "0.5",  "1"),
}
FIELDS = ("loss", "leak_rate", "wrong_rate", "fail_rate", "checks", "checks_per_task")
# CostBench has no licence file, so its task routes are not distributed; build them first (docs/REPRODUCING.md).
COSTBENCH_KEYS = ("cb15", "cb5", "fr11", "pfcb")
COSTBENCH_ROUTES = os.path.join("data", "processed", "costbench_routes.json")


def _replayer(key):
    """Imported only inside the child process, after the environment is set."""
    if key == "netpv":
        import run_netpv as m; return lambda r: m.job((r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"], r["seed"]))
    if key in ("sim", "stress", "bayes", "core2", "cb15", "cb5"):
        from ereplan import v5_exp, bayes_exp, core2_exp, costbench_v5
        return {
            "sim": lambda r: v5_exp._job((r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"], r["seed"])),
            "stress": lambda r: v5_exp._job_stress((r["strategy"], r["drop"], r["leak_mult"], r["f"], r["e"], r["seed"])),
            "bayes": lambda r: bayes_exp._job((r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["seed"])),
            "core2": lambda r: core2_exp._job((r["strategy"], *core2_exp.strategies()[r["strategy"]],
                                               (r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"]), r["seed"])),
            "cb15": lambda r: next(x for x in costbench_v5._job((r["drop"], r["q"], r["f"], r["pi"], r["leak_mult"], r["gap"], r["seed"]))
                                   if x["strategy"] == r["strategy"]),
            "cb5": lambda r: next(x for x in costbench_v5._job((r["drop"], r["q"], r["f"], r["pi"], r["leak_mult"], r["gap"], r["seed"],
                                                                r["check_frac"])) if x["strategy"] == r["strategy"]),
        }[key]
    if key == "fr11":
        import run_fr11 as m
        return lambda r: next(x for x in m.job((r["profile"], r["drop"], r["leak_mult"], r["gap"], r["check_frac"], r["seed"]))
                              if x["strategy"] == r["strategy"])
    if key == "robust":
        import run_robustness as m; return lambda r: m.job((r["strategy"], r["sigma"], r["e"], r["scenario"], r["q"], r["leak_mult"], r["seed"]))
    if key == "freshqa":
        import run_freshqa_confirm as m; return lambda r: m.job((r["strategy"], r["judge"], r["stream"], r["p_stale"], r["b_price"], r["seed"]))
    if key == "anytool":
        import run_anytool as m; return lambda r: m.job((r["strategy"], r["scenario"], r["q"], r["leak_mult"], r["seed"]))
    if key == "boundary":
        import run_boundary as m; return lambda r: m.job((r["strategy"], r["p_deg"], r["premium"], r["leak_mult"], r["seed"]))
    if key == "ablation":
        import run_ablation as m; return lambda r: m._job((r["strategy"], r["drop"], r["q"], r["f"], r["pi"], r["seed"]))
    if key == "rho":
        import run_rho as m; return lambda r: m._job((r["strategy"], r["group"], r["true_rho"], r["drop"], r["q"], r["f"], r["seed"]))
    if key == "dvsym":
        import run_dvsym as m; return lambda r: m.job((r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"], r["seed"]))
    if key == "detect":
        import run_detect as m; return lambda r: m.job((r["strategy"], r["det"], r["rho"], r["p_deg"], r["premium"], r["leak_mult"], r["seed"]))
    if key == "exact":
        import run_exactline as m; return lambda r: m.job((r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"], r["seed"]))
    if key in ("d1", "d1cal", "pflive"):
        if key == "d1cal":
            import run_d1cal  # noqa: F401  (registers the calibrated strategies)
        from ereplan import agent_live as d
        if key == "pflive":                     # registered exactly as in run_priorfix.py (live part)
            from ereplan.v5_exp import SESSION
            d.STRATS["v5_fix"] = ("Rule_v5_x", dict(SESSION, f_prior_matched=True), "none")
            d.RNG_ALIAS["v5_fix"] = "v5"
        table = json.load(open(d.TABLE))
        return lambda r: d.run_one(table, r["strategy"], r["seed"], r["price_b"], r["L"])
    if key == "pfsim":
        import run_priorfix as m
        v = m._sim_setup()
        return lambda r: v._job((r["strategy"], r["drop"], r["q"], r["leak_mult"], r["f"], r["pi"], r["seed"]))
    if key == "pfcb":
        import run_priorfix_cb as m
        return lambda r: next(x for x in m.job((r["profile"], r["drop"], r["leak_mult"], r["gap"], r["check_frac"], r["seed"]))
                              if x["strategy"] == r["strategy"])
    if key == "drift":
        import run_drift as m
        return lambda r: m.job((r["part"], r["strategy"], tuple(r["cond"]), r["seed"]))
    if key == "d1power":
        import run_d1power as m                 # registers v5_cal and v5_fix exactly as in the run
        m._init()
        return lambda r: m._job((r["strategy"], r["seed"], r["L"], r["price_b"]))
    raise KeyError(key)


def _folder(pattern, which):
    found = sorted(d for d in glob.glob(os.path.join("results", pattern)) if os.path.isdir(d))
    if not found:
        return None
    return found[0] if which == "first" else found[-1]


def child(key, n):
    title, pattern, which = SPECS[key][:3]
    if key in COSTBENCH_KEYS and not os.path.exists(COSTBENCH_ROUTES):
        print(f"SKIPPED    {title}: needs {COSTBENCH_ROUTES}, built by tools/costbench_routes.py"); return 3
    folder = _folder(pattern, which)
    if folder is None:
        print(f"NOT RUN    {title}: no folder results/{pattern} yet"); return 2
    rows = json.load(open(os.path.join(folder, "rows.json")))
    rows = rows["rows"] if isinstance(rows, dict) else rows
    redo = _replayer(key)
    sample = random.Random(0).sample(rows, min(n, len(rows)))
    bad = 0
    for r in sample:
        new = redo(r)
        bad += any(new[k] != r[k] for k in FIELDS if k in r and k in new)
    print(f"{'IDENTICAL ' if bad == 0 else 'DIFFERENT '} {title}: {len(sample) - bad}/{len(sample)} sampled runs match {folder}", flush=True)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--child", default=None)
    a = ap.parse_args()
    if a.child:
        sys.exit(child(a.child, a.n))
    keys = a.only or list(SPECS)
    codes = []
    for k in keys:
        env = dict(os.environ, EREPLAN_FMAX=SPECS[k][3], EREPLAN_NETPV=SPECS[k][4])
        codes.append(subprocess.call([sys.executable, __file__, "--child", k, "--n", str(a.n)], env=env))
    ok, missing, skipped = sum(c == 0 for c in codes), sum(c == 2 for c in codes), sum(c == 3 for c in codes)
    ran = len(codes) - missing - skipped
    print(f"\n{ok} of {ran} experiments reproduced exactly." + (f" {missing} not run yet." if missing else "") +
          (f" {skipped} skipped until the CostBench routes are built (docs/REPRODUCING.md)." if skipped else "") +
          ("" if ok == ran else " For any DIFFERENT line, note your Python, numpy and scipy versions (python check_local.py)."))
    sys.exit(0 if ok == ran else 1)


if __name__ == "__main__":
    main()
