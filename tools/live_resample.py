"""Follow-up analyses of the live-tool experiment (cached answers in data/processed/d1_table.json; no model is called).

These analyses were added after the 200-seed live-tool test, in answer to a review. They are not pre-registered and are
reported as descriptive.

  problems     Problem-level bootstrap. The 200 seeds of the live-tool test only reorder the same 300 GSM8K problems and
               move the time of the swap, so seed-level p-values show stability over orders, not over problems. Here each
               replicate draws 300 problems with replacement, runs every policy on that set over 10 seeds and four
               conditions, and records the percentage difference in mean loss. The 2.5 and 97.5 percentiles over the
               replicates give an interval that also covers the choice of problems.
  weights      Sensitivity to the loss weights. Each policy is run over a grid of the wrong-answer cost L, the cost F of a
               failed task (in units of one mean service price) and the price of service B, and the cheapest policy is
               recorded in each cell. The rules are told the same L and F that are used to score them.

Usage:  python tools/live_resample.py problems [--reps 100]
        python tools/live_resample.py weights
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # repository root, for ereplan
import argparse, dataclasses, importlib.util, itertools, json, os, time
import numpy as np
from multiprocessing import Pool
from ereplan import agent_live as d
from ereplan.config import Setting

# the strategy definitions of the 200-seed test (v5_cal, v5_fix) are registered by importing its script
_spec = importlib.util.spec_from_file_location("run_d1power", os.path.join(os.path.dirname(__file__), "..", "experiments", "run_d1power.py"))
_p = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_p)

COMPARE = {  # (policy, against): the comparisons reported for the live tools
    "label-light rule vs never check": ("v5_cal", "never"),
    "label-light rule vs retrying rule told q, f": ("v5_cal", "v4"),
    "cross-check every call vs never check": ("always_x", "never"),
    "cross-check every call vs retrying rule told q, f": ("always_x", "v4"),
    "rule (no labels) vs never check": ("v5", "never"),
    "label-light rule vs cross-check every call": ("v5_cal", "always_x"),
}
_TABLE = None


def _init():
    global _TABLE
    _TABLE = json.load(open(d.TABLE))


# ----------------------------------------------------------------------------- problem-level bootstrap
def _rep(a):
    b, seeds, keys = a
    idx = np.random.default_rng(10_000 + b).integers(0, len(_TABLE["truth"]), len(_TABLE["truth"]))
    t = {"problems": [_TABLE["problems"][i] for i in idx], "truth": [_TABLE["truth"][i] for i in idx],
         "out": {k: [v[i] for i in idx] for k, v in _TABLE["out"].items()}}
    loss = {k: np.mean([d.run_one(t, k, sd, pb, Lc)["loss"] for sd in seeds for Lc, pb in d.CONDS]) for k in keys}
    return {name: 100 * (loss[a] / loss[c] - 1) for name, (a, c) in COMPARE.items()}


def problems(reps, procs):
    seeds = tuple(range(7700, 7710))                       # 10 seeds per replicate, disjoint from every earlier test
    keys = sorted({k for pair in COMPARE.values() for k in pair})
    t0 = time.time()
    with Pool(procs, initializer=_init) as p:
        out = p.map(_rep, [(b, seeds, keys) for b in range(reps)], chunksize=1)
    L = ["# Live tools: problem-level bootstrap (follow-up, not pre-registered)", "",
         f"{reps} replicates, each 300 problems drawn with replacement from problems 201-500; per replicate 10 seeds "
         f"({seeds[0]}-{seeds[-1]}) x 4 conditions per policy. {time.time() - t0:.0f} s.", "",
         "| Comparison | median difference | 95% interval over problems | share of replicates below 0 |", "|---|---|---|---|"]
    res = {}
    for name in COMPARE:
        x = np.array([o[name] for o in out])
        res[name] = dict(median=float(np.median(x)), lo=float(np.percentile(x, 2.5)), hi=float(np.percentile(x, 97.5)),
                         share_below_0=float((x < 0).mean()))
        L.append(f"| {name} | {np.median(x):+.2f}% | {np.percentile(x, 2.5):+.2f}% to {np.percentile(x, 97.5):+.2f}% | {(x < 0).mean():.2f} |")
    return L, res, out


# ----------------------------------------------------------------------------- loss-weight sensitivity
@dataclasses.dataclass(frozen=True)
class _SettingF(Setting):
    fail_cost: float = -1.0                                # cost of a failed task; -1 keeps one mean price

    @property
    def task_cost(self) -> float:
        return self.steps_per_task * self.mean_price if self.fail_cost < 0 else self.fail_cost


def _job_w(a):
    k, sd, Lc, pb, fm = a
    base = d.make_setting
    def make(price_b, L, told, _fm=fm):
        s = base(price_b, L, told)
        s = _SettingF(**{f.name: getattr(s, f.name) for f in dataclasses.fields(Setting)})
        return s.with_(fail_cost=_fm * s.mean_price)
    d.make_setting = make
    try:
        r = d.run_one(_TABLE, k, sd, pb, Lc)
    finally:
        d.make_setting = base
    mp = (d.PRICE_A + pb) / 2
    spend = r["loss"] - Lc * r["wrong_rate"] - mp * r["fail_rate"]    # run_one scores a failure at one mean price
    r["loss"] = spend + Lc * r["wrong_rate"] + fm * mp * r["fail_rate"]
    r["F_mult"] = fm
    return r


KEYS_W = ("never", "always", "cusum", "v4", "always_x", "v5", "v5_cal", "fix_B")
GRID_L = (50.0, 100.0, 200.0, 400.0)
GRID_F = (1.0, 2.0, 4.0)
GRID_B = (45.0, 62.0)


def weights(procs):
    seeds = tuple(range(7800, 7820))
    jobs = [(k, sd, Lc, pb, fm) for k, sd, Lc, pb, fm in itertools.product(KEYS_W, seeds, GRID_L, GRID_B, GRID_F)]
    t0 = time.time()
    with Pool(procs, initializer=_init) as p:
        rows = p.map(_job_w, jobs, chunksize=8)
    mean = lambda k, Lc, pb, fm: np.mean([r["loss"] for r in rows if r["strategy"] == k and r["L"] == Lc and r["price_b"] == pb and r["F_mult"] == fm])
    L = ["# Live tools: sensitivity to the loss weights (follow-up, not pre-registered)", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s; seeds {seeds[0]}-{seeds[-1]}. L: cost of a wrong answer kept; "
         "F: cost of a failed task in mean service prices; B: price of service B (A costs 20).", "",
         "| B price | L | F | cheapest | second | " + " | ".join(KEYS_W) + " |", "|---|---|---|---|---|" + "---|" * len(KEYS_W)]
    cells = []
    for pb, Lc, fm in itertools.product(GRID_B, GRID_L, GRID_F):
        m = {k: mean(k, Lc, pb, fm) for k in KEYS_W}
        rk = sorted(m, key=m.get)
        cells.append(dict(price_b=pb, L=Lc, F_mult=fm, best=rk[0], second=rk[1], loss=m))
        L.append(f"| {pb:g} | {Lc:g} | {fm:g} | {rk[0]} | {rk[1]} | " + " | ".join(f"{m[k]:.1f}" for k in KEYS_W) + " |")
    return L, cells, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("problems", "weights"))
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2)))
    a = ap.parse_args()
    out = os.path.join("results", f"live_{a.what}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    if a.what == "problems":
        L, res, raw = problems(a.reps, a.procs)
        json.dump(dict(summary=res, replicates=raw), open(os.path.join(out, "rows.json"), "w"), indent=1)
    else:
        L, cells, rows = weights(a.procs)
        json.dump(dict(cells=cells, rows=rows), open(os.path.join(out, "rows.json"), "w"), indent=0)
    open(os.path.join(out, "report.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L)); print("->", out)


if __name__ == "__main__":
    main()
