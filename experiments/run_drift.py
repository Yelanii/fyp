"""Drift test: gradual tool degradation, and a checker whose error rates change during a run.
See PREREGISTRATION_drift.md.

Part G: tool A declines linearly to 85, 75 or 60% over 200 calls ("ramp_<level>") instead of dropping at once.
Part D: tool A drops at once, as in the main test, and at a step drawn per run the checker changes: its
        false-alarm rate rises from 0.05 to 0.20 ("f_up"), or its catch rate falls from 0.95 to 0.60 ("q_down").
        Strategies that are told q and f are told the rates from before the change.

Usage:  python experiments/run_drift.py dev       # seeds 1604-1605, pipeline check (not results)
        python experiments/run_drift.py confirm   # seeds 9600-9619, run once
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import os, sys
os.environ["EREPLAN_NETPV"] = "1"          # the corrected check criterion, as in every result for the rule
os.environ["EREPLAN_FMAX"] = "0.5"         # the default f grid, as in the simulator studies
import itertools, json, time
import numpy as np
from multiprocessing import Pool
from scipy.stats import wilcoxon

KEYS = ("never", "cusum", "v4", "v4_nocal", "always_x", "v5_told", "v5")
LEVELS, QS, LEAKS = (0.85, 0.75, 0.60), (0.8, 0.95), (1.0, 3.0)
F_G = 0.15                                                    # false-alarm rate in part G, as in the robustness test
LATE = {"f_up": dict(f_late=0.20), "q_down": dict(q_late=0.60)}
Q_D, F_D = 0.95, 0.05                                         # checker rates before the change in part D
SEEDS = {"dev": (1604, 1605), "confirm": tuple(range(9600, 9620))}
MARGIN = 3.0                                                  # non-inferiority margin, %, as in the main test


def conditions():
    g = [("G", c) for c in itertools.product(LEVELS, QS, LEAKS)]
    d = [("D", c) for c in itertools.product(LATE, LEVELS, LEAKS)]
    return g + d


def job(a):
    part, key, cond, seed = a
    from ereplan import v5_exp as v
    from ereplan.runner import run
    name, params, told = v.STRATS[key]
    if part == "G":
        level, q, lm = cond
        s, scen = v.setting(q, lm, F_G, 1.0, told), f"ramp_{level:.2f}"
    else:
        drift, level, lm = cond
        s, scen = v.setting(Q_D, lm, F_D, 1.0, told).with_(**LATE[drift]), f"drop_{level:.2f}"
    r = run(name, dict(params), s, scen, seed)
    return dict(part=part, strategy=key, cond=list(cond), seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"],
                crosschecks=r["crosschecks_per_task"], spend=r["tool_check_spend_per_task"] + r["switch_spend_per_task"],
                leak_cost=r["leak_cost_per_task"], fail_cost=r["fail_cost_per_task"], f_hat=r.get("f_hat"), q_hat=r.get("q_hat_cm"))


def _boot(x, y, n=10000, seed=0):
    idx = np.random.default_rng(seed).integers(0, len(x), (n, len(x)))
    d = 100 * (x[idx].mean(axis=1) / y[idx].mean(axis=1) - 1)
    return np.percentile(d, 2.5), np.percentile(d, 97.5)


def _wil(x, y):
    return 1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative="less").pvalue)


def _holm(ps):
    order = sorted(ps, key=ps.get); ok, stop = {}, False
    for j, h in enumerate(order):
        ok[h] = (not stop) and ps[h] < 0.05 / (len(order) - j); stop = stop or not ok[h]
    return ok


def main(which):
    seeds = SEEDS[which]
    jobs = [(part, k, c, sd) for (part, c) in conditions() for k in KEYS for sd in seeds]
    t0 = time.time()
    with Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
        rows = pool.map(job, jobs, chunksize=4)
    secs = time.time() - t0
    sm = lambda part, k, filt=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["part"] == part and r["strategy"] == k
                                                                 and r["seed"] == s and filt(r)]) for s in seeds])
    pct = lambda x, y: 100 * (x.mean() / y.mean() - 1)
    L = [f"# Drift test ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(rows)} runs; {secs:.0f} s. Part G: {len(LEVELS) * len(QS) * len(LEAKS)} conditions per seed (gradual decline, f = {F_G}, "
         f"fully repeated verdicts). Part D: {len(LATE) * len(LEVELS) * len(LEAKS)} conditions per seed (sudden drop; the checker "
         f"changes from q = {Q_D}, f = {F_D} to f = 0.20 or q = 0.60).", ""]
    for part, title in (("G", "Part G: gradual decline"), ("D", "Part D: the checker changes during the run")):
        L += [f"## {title}", "", "| Strategy | total loss | spend | wrong-answer cost | failure cost | wrong kept | failed | checks/task |",
              "|---|---|---|---|---|---|---|---|"]
        for k in KEYS:
            R = [r for r in rows if r["part"] == part and r["strategy"] == k]
            mu = lambda f: np.mean([r[f] for r in R])
            L.append(f"| {k} | {sm(part, k).mean():.1f} | {mu('spend'):.1f} | {mu('leak_cost'):.1f} | {mu('fail_cost'):.1f} | "
                     f"{100 * mu('leak_rate'):.1f}% | {100 * mu('fail_rate'):.1f}% | {mu('checks'):.2f} |")
        L.append("")
    # pre-registered hypotheses
    ni = {"H-G1 part G: the rule within 3% of the same rule told q and f": ("G", "v5", "v5_told"),
          "H-D1 part D: the rule within 3% of the same rule told the rates from before the change": ("D", "v5", "v5_told")}
    sup = {"H-G2 part G: the rule below the label-free retrying rule": ("G", "v5", "v4_nocal"),
           "H-G3 part G: the rule below never checking": ("G", "v5", "never"),
           "H-D2 part D: the rule below the label-free retrying rule": ("D", "v5", "v4_nocal")}
    L += ["## Pre-registered hypotheses (PREREGISTRATION_drift.md)", "",
          f"Non-inferiority: confirmed if the upper end of the 95% bootstrap CI of the difference is at most +{MARGIN:.0f}%. "
          "Superiority: one-sided Wilcoxon on seed means, Holm across H-G2, H-G3 and H-D2.", ""]
    for h, (part, a, b) in ni.items():
        x, y = sm(part, a), sm(part, b); lo, hi = _boot(x, y)
        L.append(f"- {h}: {x.mean():.1f} vs {y.mean():.1f} ({pct(x, y):+.2f}%, 95% CI {lo:+.2f}% to {hi:+.2f}%) "
                 f"-> **{'CONFIRMED' if hi <= MARGIN else 'NOT CONFIRMED'}**")
    ps = {h: _wil(sm(p, a), sm(p, b)) for h, (p, a, b) in sup.items()}; ok = _holm(ps)
    for h, (part, a, b) in sup.items():
        x, y = sm(part, a), sm(part, b); lo, hi = _boot(x, y)
        L.append(f"- {h}: {x.mean():.1f} vs {y.mean():.1f} ({pct(x, y):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%), one-sided Wilcoxon "
                 f"p = {ps[h]:.2g}, Holm {'ok' if ok[h] else 'fail'} -> **{'CONFIRMED' if ok[h] else 'NOT CONFIRMED'}**")
    L += ["", "## Descriptive", ""]
    for part in ("G", "D"):
        for k in ("v4", "cusum", "always_x", "never"):
            x, y = sm(part, "v5"), sm(part, k); lo, hi = _boot(x, y)
            L.append(f"- Part {part}: v5 vs {k}: {x.mean():.1f} vs {y.mean():.1f} ({pct(x, y):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%)")
    for lv in LEVELS:
        f = lambda r, lv=lv: r["cond"][0] == lv
        L.append(f"- Part G, level {lv:.2f}: v5 {sm('G', 'v5', f).mean():.1f}, v5_told {sm('G', 'v5_told', f).mean():.1f}, "
                 f"v4_nocal {sm('G', 'v4_nocal', f).mean():.1f}, never {sm('G', 'never', f).mean():.1f}")
    for dr in LATE:
        f = lambda r, dr=dr: r["cond"][0] == dr
        L.append(f"- Part D, {dr}: v5 {sm('D', 'v5', f).mean():.1f}, v5_told {sm('D', 'v5_told', f).mean():.1f}, "
                 f"v4 {sm('D', 'v4', f).mean():.1f}, v4_nocal {sm('D', 'v4_nocal', f).mean():.1f}, never {sm('D', 'never', f).mean():.1f}")
        fh = [r["f_hat"] for r in rows if r["part"] == "D" and r["strategy"] == "v5" and f(r) and r["f_hat"] is not None]
        qh = [r["q_hat"] for r in rows if r["part"] == "D" and r["strategy"] == "v5" and f(r) and r["q_hat"] is not None]
        if fh and qh:
            L.append(f"  learned at the end of the run (median): f {np.median(fh):.3f}, q {np.median(qh):.3f}")
    out = os.path.join("results", f"drift_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", out)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in SEEDS:
        sys.exit(__doc__)
    main(sys.argv[1])
