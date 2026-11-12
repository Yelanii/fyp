"""How close does each strategy get to the perfect-knowledge optimum?

Uses the check-worth map runs (total loss per task, seeds 200-209) and computes, for every condition
and seed, the optimum's expected total loss. Reports per strategy:
  * excess loss over the optimum (0% = as good as perfect knowledge);
  * share of the possible saving captured = (never-check loss - strategy loss) / (never-check loss - optimum).

Usage: python -m ereplan.gap [results/checkmap_.../rows.json]
"""
import glob, json, os, sys
from multiprocessing import Pool
import numpy as np

from .config import Setting
from .optimum import optimum

ORDER = ["Decision rule v2", "Change alarm, CUSUM (B4)", "Always check (B1)", "Fixed-rate check (B3)",
         "Never check (B2)", "Oracle (knows truth)"]


def _opt(key):
    drop, q, cf, lm, seed = key
    s = Setting().with_(q_true=q, q_assumed=q, check_frac=cf, leak_mult=lm)
    return key, optimum(s, f"drop_{drop:.2f}", seed)[0]


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    path = argv[0] if argv else sorted(glob.glob("results/checkmap_*/rows.json"))[-1]
    rows = json.load(open(path))
    keys = sorted({(r["drop"], r["q"], r["check_frac"], r["leak_mult"], r["seed"]) for r in rows})
    with Pool(os.cpu_count() or 2) as pool:
        opt = dict(pool.map(_opt, keys, chunksize=4))
    out = os.path.dirname(path)
    json.dump([dict(drop=k[0], q=k[1], check_frac=k[2], leak_mult=k[3], seed=k[4], optimum=v)
               for k, v in opt.items()], open(os.path.join(out, "optimum.json"), "w"), indent=1)

    conds = sorted({k[:4] for k in keys})
    loss = {}
    for r in rows:
        loss.setdefault((r["drop"], r["q"], r["check_frac"], r["leak_mult"], r["strategy"]), []).append(r["total_loss"])
    res = {}
    violations = 0
    for c in conds:
        o = np.mean([opt[c + (sd,)] for sd in sorted({k[4] for k in keys})])
        never = np.mean(loss[c + ("Never check (B2)",)])
        best_real = min(np.mean(loss[c + (st,)]) for st in ORDER)
        violations += best_real < o * 0.98
        for st in ORDER:
            m = np.mean(loss[c + (st,)])
            room = never - o
            res.setdefault(st, []).append(dict(lm=c[3], drop=c[0], excess=m / o - 1,
                                               captured=(never - m) / room if room > 1e-9 else np.nan))
    L = ["# Distance to the perfect-knowledge optimum", "",
         f"Source: {path}. Conditions: {len(conds)}. Optimum is a lower bound "
         f"(conditions where some strategy's mean fell >2% below it, from sampling noise: {violations}).", ""]
    for lm in sorted({c[3] for c in conds}):
        L += [f"## Leak loss = {lm:g} task(s)", "",
              "| Strategy | Median excess loss over optimum | Median share of possible saving captured |",
              "|---|---|---|"]
        for st in ORDER:
            ex = [x["excess"] for x in res[st] if x["lm"] == lm]
            cap = [x["captured"] for x in res[st] if x["lm"] == lm and not np.isnan(x["captured"])]
            L.append(f"| {st} | {np.median(ex)*100:+.1f}% | {np.median(cap)*100:.0f}% |")
        L.append("")
    open(os.path.join(out, "gap_to_optimum.md"), "w").write("\n".join(L))
    _plot(res, out)
    print("\n".join(L))


def _plot(res, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, lm in zip(axes, (1.0, 3.0)):
        names = ORDER[:-1]
        vals = [np.median([x["excess"] for x in res[st] if x["lm"] == lm]) * 100 for st in names]
        ax.barh(range(len(names)), vals, color=["#2a9d8f"] + ["#999999"] * (len(names) - 1))
        ax.set_yticks(range(len(names)), names)
        ax.invert_yaxis()
        for i, v in enumerate(vals):
            ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=9)
        ax.set_xlabel("extra loss compared with the perfect-knowledge optimum (median over conditions)")
        ax.set_title(f"Wrong answer costs {lm:g} task(s)")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "gap_to_optimum.png"), dpi=130)


if __name__ == "__main__":
    main()
