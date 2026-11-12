"""Check-worth map: WHEN does paying for checks pay off?

For every combination of
    drop size   (the cheap tool's success rate falls from 95% to 90%, 85%, ..., 60%),
    catch rate  q (how often a check catches a silent failure),
    check price (as a share of the mean tool price),
    leak loss   (cost of a wrong answer reaching the user, in task costs),
it runs the same strategies on the same simulated worlds and records which is cheapest per successful
task, and how much the best checking strategy saves compared with never checking.

Settings for every strategy are the ones tuned in the v2 pilot (seeds 50-59) and are NOT re-tuned here.
Seeds 200-209 are new.

Usage: python -m ereplan.checkmap [--quick]
"""
import argparse, itertools, json, os, time
from multiprocessing import Pool
import numpy as np

from .config import Setting
from .runner import run

STRATEGIES = {
    "Never check (B2)": ("B2_never", dict(window=30)),
    "Always check (B1)": ("B1_always", dict(window=30)),
    "Fixed-rate check (B3)": ("B3_fixed", dict(window=30, rate=0.2)),
    "Change alarm, CUSUM (B4)": ("B4_cusum", dict(h=6, p1=0.8)),
    "Decision rule v2": ("Rule_leakaware", dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)),
    "Oracle (knows truth)": ("B6_oracle", dict()),
}
CHECKERS = ["Always check (B1)", "Fixed-rate check (B3)", "Change alarm, CUSUM (B4)", "Decision rule v2"]
DROPS = (0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.60)
QS = (0.5, 0.8, 0.95)
PRICES = (0.05, 0.15, 0.30)
LEAKS = (1.0, 3.0)
SEEDS = tuple(range(200, 210))


def _job(a):
    label, strat, params, drop, q, cf, lm, seed = a
    s = Setting().with_(q_true=q, q_assumed=q, check_frac=cf, leak_mult=lm)
    r = run(strat, params, s, f"drop_{drop:.2f}", seed)
    return dict(strategy=label, drop=drop, q=q, check_frac=cf, leak_mult=lm, seed=seed,
                cost_per_success=r["cost_per_success"], total_loss=r["total_loss_per_task"],
                checks=r["checks_per_task"], leak_rate=r["leak_rate"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--out", default="results")
    a = ap.parse_args(argv)
    seeds = SEEDS[:3] if a.quick else SEEDS
    jobs = [(lb, st, pr, d, q, cf, lm, sd) for lb, (st, pr) in STRATEGIES.items()
            for d, q, cf, lm, sd in itertools.product(DROPS, QS, PRICES, LEAKS, seeds)]
    t0 = time.time()
    with Pool(a.procs) as pool:
        rows = pool.map(_job, jobs, chunksize=16)
    out = os.path.join(a.out, f"checkmap_{time.strftime('%Y%m%d-%H%M%S')}{'_quick' if a.quick else ''}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))

    for metric in ("cost_per_success", "total_loss"):
        table = analyse(rows, metric)
        tag = "" if metric == "cost_per_success" else "_totalloss"
        json.dump(table, open(os.path.join(out, f"cells{tag}.json"), "w"), indent=1)
        _plot(table, out, metric, tag)
        _summary(table, out, time.time() - t0, seeds, metric, tag)
        print(open(os.path.join(out, f"summary{tag}.md")).read())
    print(f"Saved to {out}")


def analyse(rows, metric):
    cells = {}
    for r in rows:
        cells.setdefault((r["drop"], r["q"], r["check_frac"], r["leak_mult"]), {}).setdefault(r["strategy"], []).append(r[metric])
    table = []
    for key, d in cells.items():
        med = {k: float(np.median(v)) for k, v in d.items()}
        nonoracle = {k: v for k, v in med.items() if not k.startswith("Oracle")}
        best = min(nonoracle, key=nonoracle.get)
        best_checker = min(CHECKERS, key=lambda k: med[k])
        saving = 1 - med[best_checker] / med["Never check (B2)"]
        table.append(dict(drop=key[0], q=key[1], check_frac=key[2], leak_mult=key[3], winner=best,
                          best_checker=best_checker, saving_vs_never=saving,
                          rule_vs_cusum=med["Decision rule v2"] / med["Change alarm, CUSUM (B4)"] - 1, **med))
    return table


def _plot(table, out, metric, tag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    VMAX = max(20.0, max(abs(t["saving_vs_never"]) for t in table) * 100)
    for lm in LEAKS:
        fig, axes = plt.subplots(1, len(QS), figsize=(13, 4.2), sharey=True)
        for ax, q in zip(axes, QS):
            M = np.array([[next(t["saving_vs_never"] for t in table if t["drop"] == d and t["q"] == q
                               and t["check_frac"] == cf and t["leak_mult"] == lm) * 100
                           for cf in PRICES] for d in DROPS])
            im = ax.imshow(M, cmap="RdYlGn", vmin=-VMAX, vmax=VMAX, aspect="auto")
            for i in range(len(DROPS)):
                for j in range(len(PRICES)):
                    ax.text(j, i, f"{M[i, j]:+.0f}%", ha="center", va="center", fontsize=8)
            ax.set_xticks(range(len(PRICES)), [f"{int(c*100)}%" for c in PRICES])
            ax.set_yticks(range(len(DROPS)), [f"{int(d*100)}%" for d in DROPS])
            ax.set_xlabel("check price (share of tool price)")
            ax.set_title(f"catch rate q = {q}")
        axes[0].set_ylabel("cheap tool falls to")
        what = "cost per successful task" if metric == "cost_per_success" else "total loss per task (incl. leak loss)"
        fig.suptitle(f"Saving from the best checking strategy vs never checking: {what}; leak loss = {lm:g} task")
        fig.colorbar(im, ax=axes, shrink=0.8, label="saving")
        fig.savefig(os.path.join(out, f"checkmap{tag}_leak{lm:g}.png"), dpi=130, bbox_inches="tight")


def _summary(table, out, wall, seeds, metric, tag):
    L = [f"# Check-worth map (metric: {metric})", "", f"Cells: {len(table)}; seeds {seeds[0]}-{seeds[-1]}; wall time {wall:.0f} s.", ""]
    pays = [t for t in table if t["saving_vs_never"] >= 0.05]
    L.append(f"- Checking saves at least 5% in {len(pays)} of {len(table)} cells.")
    from collections import Counter
    L.append("- Cheapest non-oracle strategy per cell: " +
             ", ".join(f"{k} {v}" for k, v in Counter(t['winner'] for t in table).most_common()))
    for d in DROPS:
        sub = [t for t in table if t["drop"] == d]
        L.append(f"- Drop to {int(d*100)}%: median saving from checking {np.median([t['saving_vs_never'] for t in sub])*100:+.1f}%; "
                 f"rule v2 vs CUSUM median {np.median([t['rule_vs_cusum'] for t in sub])*100:+.1f}%")
    for lm in LEAKS:
        sub = [t for t in table if t["leak_mult"] == lm]
        L.append(f"- Leak loss {lm:g} task(s): median saving {np.median([t['saving_vs_never'] for t in sub])*100:+.1f}%; "
                 f"max {max(t['saving_vs_never'] for t in sub)*100:+.1f}%")
    open(os.path.join(out, f"summary{tag}.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    main()
