"""Confirmatory test for PREREGISTRATION_selfcal.md. Usage: python -m ereplan.confirm_selfcal"""
import itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon
from .config import Setting
from .runner import run

STRATS = {"never": ("B2_never", dict(window=30)), "always": ("B1_always", dict(window=30)),
          "cusum": ("B4_cusum", dict(h=6, p1=0.8)),
          "v2": ("Rule_leakaware", dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)),
          "v3": ("Rule_v3_selfcal", dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50,
                                          q_prior_strength=3.0))}
DROPS, LEAKS, PRICES, CORRS, SEEDS = (0.85, 0.80, 0.75, 0.60), (1.0, 3.0), (0.15, 0.30), (0.0, 0.9), tuple(range(900, 920))


def _job(key):
    name, d, lm, cf, corr, sd = key
    st, p = STRATS[name]
    s = Setting().with_(q_true=0.8, q_assumed=0.8, check_frac=cf, leak_mult=lm, check_corr=corr)
    return dict(strategy=name, drop=d, leak=lm, price=cf, corr=corr, seed=sd,
                total_loss=run(st, p, s, f"drop_{d:.2f}", sd)["total_loss_per_task"])


def main():
    keys = list(itertools.product(STRATS, DROPS, LEAKS, PRICES, CORRS, SEEDS))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(_job, keys, chunksize=8)
    L = {(r["strategy"], r["drop"], r["leak"], r["price"], r["corr"], r["seed"]): r["total_loss"] for r in rows}
    conds = list(itertools.product(DROPS, LEAKS, PRICES))
    pairs = lambda a, b, corr: (np.array([L[(a, *c, corr, s)] for c in conds for s in SEEDS]),
                                np.array([L[(b, *c, corr, s)] for c in conds for s in SEEDS]))
    # H-FR
    al, nv = pairs("always", "never", 0.9)
    worse = sum(np.mean([L[("always", *c, 0.9, s)] for s in SEEDS]) > np.mean([L[("never", *c, 0.9, s)] for s in SEEDS]) for c in conds)
    p_fr = wilcoxon(al, nv, alternative="greater").pvalue
    h_fr = worse >= 2 * len(conds) / 3 and p_fr < 0.01
    # H-SC
    v3, v2 = pairs("v3", "v2", 0.9)
    rel_sc = float(np.mean(v3) / np.mean(v2) - 1)
    p_sc = wilcoxon(v3, v2, alternative="less").pvalue
    h_sc = rel_sc <= -0.02 and p_sc < 0.01
    # H-NI
    v3o, v2o = pairs("v3", "v2", 0.0)
    rel_ni = float(np.mean(v3o) / np.mean(v2o) - 1)
    h_ni = rel_ni <= 0.01
    means = {(n, corr): float(np.mean([L[(n, *c, corr, s)] for c in conds for s in SEEDS])) for n in STRATS for corr in CORRS}
    res = dict(seeds=[SEEDS[0], SEEDS[-1]], wall_seconds=round(time.time() - t0),
               H_FR=dict(conditions_always_worse_than_never=int(worse), of=len(conds), p=float(p_fr),
                         mean_always=float(al.mean()), mean_never=float(nv.mean()), confirmed=bool(h_fr)),
               H_SC=dict(mean_v3=float(v3.mean()), mean_v2=float(v2.mean()), relative=rel_sc, p=float(p_sc), confirmed=bool(h_sc)),
               H_NI=dict(mean_v3=float(v3o.mean()), mean_v2=float(v2o.mean()), relative=rel_ni, confirmed=bool(h_ni)),
               mean_total_loss={f"{n} corr={c}": v for (n, c), v in means.items()})
    out = os.path.join("results", f"confirm_selfcal_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "result.json"), "w"), indent=1)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
