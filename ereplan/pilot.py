"""Pilot (Table 3.16): tune on seeds 50-59, judge on seeds 0-19, apply the pre-registered go/no-go rule.

Usage:  python -m ereplan.pilot            (full pilot, about 10 minutes on a laptop)
        python -m ereplan.pilot --quick    (2 tuning and 5 judging seeds, for a fast check)
"""
import argparse, hashlib, itertools, json, math, os, platform, sys, time
from dataclasses import asdict
from multiprocessing import Pool

import numpy as np
from scipy.stats import wilcoxon

from .config import Setting, pilot_grid, SCENARIOS, TUNE_SEEDS, JUDGE_SEEDS
from .runner import run
from .strategies import protection_value

# Equal tuning budget: at most 8 configurations per strategy (Section 3.3.5.4).
TUNING_GRID = {
    "Rule": [dict(window=w, epsilon=e, k=k) for w, e, k in itertools.product((30, 60), (0.02, 0.05), (3, 5))],
    "B1_always": [dict(window=w) for w in (30, 60)],
    "B2_never": [dict(window=w) for w in (30, 60)],
    "B3_fixed": [dict(window=w, rate=r) for w, r in itertools.product((30, 60), (0.05, 0.1, 0.2, 0.3))],
    "B4_cusum": [dict(h=h, p1=p1) for h, p1 in itertools.product((2, 4, 6, 8), (0.7, 0.8))],
    "B8_fixed_est": [dict(rate=r) for r in (0.05, 0.1, 0.2, 0.3)],
    "B6_oracle": [dict()],
}
# Exploratory variant, reported but NOT used in the go/no-go decision.
EXPLORATORY = {"Rule_session": ("Rule", [dict(window=w, epsilon=e, k=k, horizon_mode="session")
                                          for w, e, k in itertools.product((30, 60), (0.02, 0.05), (3, 5))]),
               "Rule_leakaware": ("Rule_leakaware", [dict(window=w, epsilon=e, k=k)
                                                      for w, e, k in itertools.product((30, 60), (0.02, 0.05), (3, 5))])}
JUDGED_BASELINES = ("B1_always", "B2_never", "B3_fixed", "B4_cusum", "B8_fixed_est")
S3_DEGRADED_P = 0.85


def _job(args):
    label, strat, params, setting, scenario, seed = args
    r = run(strat, params, setting, scenario, seed)
    r["label"], r["params"] = label, json.dumps(params, sort_keys=True)
    return r


def _pool_map(jobs, procs):
    if procs <= 1:
        return [_job(j) for j in jobs]
    with Pool(procs) as pool:
        return pool.map(_job, jobs, chunksize=8)


def _finite_mean(xs):
    xs = [x for x in xs if math.isfinite(x)]
    return float(np.mean(xs)) if xs else math.inf


RULE_V2_CONFIGS = [dict(window=w, epsilon=e, k=k, horizon_mode="session", session_cap=50)
                   for w, e, k in itertools.product((30, 60), (0.02, 0.05), (3, 5))]


def get_candidates(rule_version):
    """label -> (strategy class name, configurations). 'Rule' is the version being judged."""
    c = {k: (k, v) for k, v in TUNING_GRID.items()}
    if rule_version == "v1":
        c.update(EXPLORATORY)
    else:  # v2, pre-registered in PREREGISTRATION_v2.md
        c["Rule"] = ("Rule_leakaware", RULE_V2_CONFIGS)
        c["Rule_v1"] = ("Rule", TUNING_GRID["Rule"])          # reference only, not judged
    return c


def tune(grid_settings, seeds, procs, rule_version="v1"):
    """Pick, for each strategy, the configuration with the lowest mean cost per successful task."""
    candidates = get_candidates(rule_version)
    jobs = []
    for label, (strat, configs) in candidates.items():
        for ci, params in enumerate(configs):
            for st in grid_settings:
                for sc in SCENARIOS:
                    for sd in seeds:
                        jobs.append((f"{label}#{ci}", strat, params, st, sc, sd))
    rows = _pool_map(jobs, procs)
    chosen, table = {}, []
    for label, (strat, configs) in candidates.items():
        best = None
        for ci, params in enumerate(configs):
            vals = [r["cost_per_success"] for r in rows if r["label"] == f"{label}#{ci}"]
            m = _finite_mean(vals)
            table.append(dict(strategy=label, config=params, mean_cost_per_success=m))
            if best is None or m < best[0]:
                best = (m, params)
        chosen[label] = (strat, best[1])
    return chosen, table


def judge(chosen, grid_settings, seeds, procs):
    jobs = [(label, strat, params, st, sc, sd)
            for label, (strat, params) in chosen.items()
            for st in grid_settings for sc in SCENARIOS for sd in seeds]
    return _pool_map(jobs, procs)


def go_no_go(rows, grid_settings):
    """Apply the three GO criteria of Table 3.16, per scenario, pooling the pilot settings."""
    def sel(label, sc, key=None):
        rs = [r for r in rows if r["label"] == label and r["scenario"] == sc]
        rs.sort(key=lambda r: (r["q"], r["check_frac"], r["seed"]))   # pairs line up by setting and seed
        return rs if key is None else np.array([r[key] for r in rs], dtype=float)

    report = {"scenarios": {}}
    wins = 0
    fs_ok_all = True
    for sc in SCENARIOS:
        rule = sel("Rule", sc, "cost_per_success")
        meds = {b: float(np.median(sel(b, sc, "cost_per_success"))) for b in JUDGED_BASELINES}
        best = min(meds, key=meds.get)
        base = sel(best, sc, "cost_per_success")
        diff = rule - base
        ok = np.isfinite(diff)
        try:
            p = float(wilcoxon(rule[ok], base[ok], alternative="less").pvalue)
        except ValueError:
            p = 1.0
        rel = float(np.median(rule) / meds[best] - 1.0)
        c1 = (rel <= -0.05) and (p < 0.05)
        wins += int(c1)
        fs_rule = float(np.mean(sel("Rule", sc, "false_switches_per_1000")))
        fs_base = float(np.mean(sel(best, sc, "false_switches_per_1000")))
        c2 = fs_rule <= fs_base
        fs_ok_all &= c2
        report["scenarios"][sc] = dict(
            best_baseline=best, baseline_median_cps=meds[best], rule_median_cps=float(np.median(rule)),
            relative_change=rel, wilcoxon_p_one_sided=p, criterion1_met=c1,
            rule_false_switches_per_1000=fs_rule, baseline_false_switches_per_1000=fs_base, criterion2_met=c2,
            all_baseline_medians=meds)

    # Criterion 3: harmless drift, only in settings where protection alone does not justify a check
    eligible = [st for st in grid_settings if protection_value(S3_DEGRADED_P, st) < st.check_price]
    c3_rows = []
    c3 = True
    for st in eligible:
        def pick(label, key):
            return np.array([r[key] for r in rows if r["label"] == label and r["scenario"] == "S3_harmless"
                             and r["q"] == st.q_true and r["check_frac"] == st.check_frac], dtype=float)
        rc, bc = pick("Rule", "checks_per_task").mean(), pick("B3_fixed", "checks_per_task").mean()
        rl, bl = pick("Rule", "leak_rate").mean(), pick("B3_fixed", "leak_rate").mean()
        met = (rc <= bc) and (rl <= bl)
        c3 &= met
        c3_rows.append(dict(q=st.q_true, check_frac=st.check_frac, rule_checks=rc, fixed_checks=bc,
                            rule_leak=rl, fixed_leak=bl, met=met))
    report["criterion1_scenarios_won"] = wins
    report["criterion1_met"] = wins >= 2
    report["criterion2_met"] = fs_ok_all
    report["criterion3_settings"] = c3_rows
    report["criterion3_met"] = bool(c3) if eligible else None
    report["decision"] = "GO" if (wins >= 2 and fs_ok_all and (c3 if eligible else True)) else "NO-GO (pivot)"
    return report


def summarise(rows):
    out = {}
    labels = sorted({r["label"] for r in rows})
    for sc in SCENARIOS:
        out[sc] = {}
        for lb in labels:
            rs = [r for r in rows if r["label"] == lb and r["scenario"] == sc]
            delays = [r["switch_delay"] for r in rs if not math.isnan(r["switch_delay"])]
            out[sc][lb] = dict(
                median_cost_per_success=float(np.median([r["cost_per_success"] for r in rs])),
                mean_total_loss_per_task=float(np.mean([r["total_loss_per_task"] for r in rs])),
                checks_per_task=float(np.mean([r["checks_per_task"] for r in rs])),
                false_switches_per_1000=float(np.mean([r["false_switches_per_1000"] for r in rs])),
                leak_rate=float(np.mean([r["leak_rate"] for r in rs])),
                median_switch_delay=float(np.median(delays)) if delays else math.nan,
            )
    return out


JUDGE_LABEL = "0-19"
RULE_LABEL = "v1 (proposal Section 3.3.5.5)"


def write_report(path, chosen, summary, decision, cpu_per_1000):
    L = ["# Pilot report (e-Replan proof of concept)", "", f"Rule version judged: {RULE_LABEL}", ""]
    L.append(f"**Decision: {decision['decision']}**  (pre-registered criteria, Table 3.16)")
    L.append("")
    L.append(f"- Criterion 1 (>= 5% lower median cost per successful task than the best non-oracle baseline, "
             f"paired Wilcoxon p < 0.05, in >= 2 of 3 scenarios): scenarios won = {decision['criterion1_scenarios_won']} "
             f"-> {'met' if decision['criterion1_met'] else 'not met'}")
    L.append(f"- Criterion 2 (no more false switches than that baseline): {'met' if decision['criterion2_met'] else 'not met'}")
    c3 = decision['criterion3_met']
    L.append(f"- Criterion 3 (harmless drift: no more checks than fixed-rate at equal or lower leak rate, "
             f"where protection alone does not justify a check): {'met' if c3 else ('not met' if c3 is not None else 'no eligible settings')}")
    L.append("")
    L.append("## Per-scenario comparison with the best non-oracle baseline")
    L.append("| Scenario | Best baseline | Baseline median | Rule median | Change | Wilcoxon p | False sw. rule / base |")
    L.append("|---|---|---|---|---|---|---|")
    for sc, d in decision["scenarios"].items():
        L.append(f"| {sc} | {d['best_baseline']} | {d['baseline_median_cps']:.1f} | {d['rule_median_cps']:.1f} | "
                 f"{d['relative_change']:+.1%} | {d['wilcoxon_p_one_sided']:.3g} | "
                 f"{d['rule_false_switches_per_1000']:.1f} / {d['baseline_false_switches_per_1000']:.1f} |")
    L.append("")
    if decision["criterion3_settings"]:
        L.append("## Criterion 3 detail (S3 harmless drift)")
        L.append("| q | Check price | Rule checks/task | Fixed-rate checks/task | Rule leak | Fixed-rate leak | Met |")
        L.append("|---|---|---|---|---|---|---|")
        for r in decision["criterion3_settings"]:
            L.append(f"| {r['q']} | {r['check_frac']:.0%} | {r['rule_checks']:.2f} | {r['fixed_checks']:.2f} | "
                     f"{r['rule_leak']:.3f} | {r['fixed_leak']:.3f} | {r['met']} |")
        L.append("")
    L.append(f"## All strategies (judging seeds {JUDGE_LABEL}, pooled over the four pilot settings)")
    for sc, d in summary.items():
        L.append(f"### {sc}")
        L.append("| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |")
        L.append("|---|---|---|---|---|---|---|")
        for lb, m in sorted(d.items(), key=lambda kv: kv[1]["median_cost_per_success"]):
            L.append(f"| {lb} | {m['median_cost_per_success']:.1f} | {m['mean_total_loss_per_task']:.1f} | "
                     f"{m['checks_per_task']:.2f} | {m['false_switches_per_1000']:.1f} | {m['leak_rate']:.3f} | "
                     f"{m['median_switch_delay']:.0f} |")
        L.append("")
    L.append("## Tuned configurations (seeds 50-59)")
    for lb, (strat, params) in chosen.items():
        L.append(f"- {lb}: {strat} {json.dumps(params)}")
    L.append("")
    L.append(f"Feasibility: about {cpu_per_1000:.2f} CPU-seconds per 1,000 simulated tasks.")
    L.append("")
    if RULE_LABEL.startswith("v1"):
        L.append("Rule_session and Rule_leakaware are exploratory variants added after the first pilot run "
             "(plan horizon = calls left in the run, capped at 50; switch line that also counts expected leak loss). "
             "They are not part of the go/no-go decision.")
    else:
        L.append("Rule_v1 is the proposal rule, shown for reference only; the judged 'Rule' is v2.")
    open(path, "w").write("\n".join(L))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--out", default="results")
    ap.add_argument("--rule", choices=("v1", "v2"), default="v1",
                    help="v1 = proposal rule; v2 = leak-aware line + session horizon (PREREGISTRATION_v2.md)")
    ap.add_argument("--judge-seeds", default=None, help="range such as 20-39 (default 0-19)")
    a = ap.parse_args(argv)
    global JUDGE_LABEL, RULE_LABEL
    tune_seeds = TUNE_SEEDS[:2] if a.quick else TUNE_SEEDS
    if a.judge_seeds:
        lo, hi = (int(x) for x in a.judge_seeds.split("-"))
        judge_seeds = tuple(range(lo, hi + 1))
    else:
        judge_seeds = JUDGE_SEEDS
    if a.quick:
        judge_seeds = judge_seeds[:5]
    JUDGE_LABEL = f"{judge_seeds[0]}-{judge_seeds[-1]}"
    if a.rule == "v2":
        RULE_LABEL = "v2 (leak-aware switch line, session horizon capped at 50; PREREGISTRATION_v2.md)"
    grid = pilot_grid()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = os.path.join(a.out, f"pilot_{a.rule}_{stamp}{'_quick' if a.quick else ''}")
    os.makedirs(out, exist_ok=True)

    t0, c0 = time.time(), time.process_time()
    print(f"Tuning on seeds {list(tune_seeds)} ...", flush=True)
    chosen, tuning_table = tune(grid, tune_seeds, a.procs, a.rule)
    print(f"Judging on seeds {list(judge_seeds)} ...", flush=True)
    rows = judge(chosen, grid, judge_seeds, a.procs)
    wall = time.time() - t0

    # CPU time per 1,000 tasks: time a single-process sample run so the figure is machine-comparable
    ts = time.process_time()
    for sc in SCENARIOS:
        run(chosen["Rule"][0], chosen["Rule"][1], grid[0], sc, 0)
    cpu_per_1000 = (time.process_time() - ts) / (len(SCENARIOS) * grid[0].n_tasks) * 1000

    decision = go_no_go(rows, grid)
    summary = summarise(rows)

    import csv
    keys = [k for k in rows[0].keys() if k != "trace"]
    with open(os.path.join(out, "runs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    json.dump(tuning_table, open(os.path.join(out, "tuning.json"), "w"), indent=1)
    json.dump(decision, open(os.path.join(out, "go_no_go.json"), "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    settings_blob = json.dumps([asdict(s) for s in grid], sort_keys=True, default=str)
    manifest = dict(
        created=stamp, quick=a.quick, rule_version=a.rule, tune_seeds=list(tune_seeds), judge_seeds=list(judge_seeds),
        settings_sha256=hashlib.sha256(settings_blob.encode()).hexdigest(),
        settings=json.loads(settings_blob), chosen={k: v[1] for k, v in chosen.items()},
        python=sys.version, platform=platform.platform(), processes=a.procs,
        numpy=np.__version__, wall_seconds=round(wall, 1),
        cpu_seconds_per_1000_tasks=round(cpu_per_1000, 3),
    )
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    write_report(os.path.join(out, "pilot_report.md"), chosen, summary, decision, cpu_per_1000)
    _plot(rows, os.path.join(out, "cost_per_success.png"))
    print(open(os.path.join(out, "pilot_report.md")).read())
    print(f"\nSaved to {out}  (wall time {wall:.0f} s)")


def _plot(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    present = {r["label"] for r in rows}
    labels = [l for l in ["Rule", "Rule_v1", "Rule_leakaware", "Rule_session", "B1_always", "B2_never",
                          "B3_fixed", "B4_cusum", "B8_fixed_est", "B6_oracle"] if l in present]
    fig, axes = plt.subplots(1, len(SCENARIOS), figsize=(13, 4), sharey=False)
    for ax, sc in zip(axes, SCENARIOS):
        data = [[r["cost_per_success"] for r in rows if r["label"] == lb and r["scenario"] == sc
                 and math.isfinite(r["cost_per_success"])] for lb in labels]
        ax.boxplot(data, showfliers=False)
        ax.set_xticks(range(1, len(labels) + 1), [l.replace("_", "\n") for l in labels], fontsize=7)
        ax.set_title(sc)
        ax.set_ylabel("Cost per successful task (simulated)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)


if __name__ == "__main__":
    main()
