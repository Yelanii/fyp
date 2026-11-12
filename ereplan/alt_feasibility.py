"""Feasibility check (28 October 2026, EXPLORATORY, not pre-registered): what happens when the alternative tool can
degrade too? Until now every experiment let only the primary tool A degrade.

Tools: A (price 20), B (24), C premium (30, stays at 97%). Scenarios:
  S1 only A degrades (reference)      S2 B degrades 50-150 calls after A      S3 A and B degrade at unrelated times
  S4 A and B degrade together (shared cause)                                  S5 A degrades, then is fixed 200 calls later
Existing strategies are run unchanged. The question is only: can the framework express these cases, and what do the
current rules do in them? Seeds 2100-2109 (fresh). q 0.95, false alarms f 0.15 repeating (pi 1), wrong answer = 3 tasks.

No oracle: the existing oracle knows the success rates but not the false alarms, so it is not a fair reference here.

Usage: python -m ereplan.alt_feasibility
"""
import itertools, json, os, time
from multiprocessing import Pool
import numpy as np

from .config import Setting
from .runner import run
from .v5_exp import STRATS as V5_STRATS, setting

SCEN = ("alt_S1_only_A", "alt_S2_after", "alt_S3_indep", "alt_S4_common", "alt_S5_recover")
LABEL = {"alt_S1_only_A": "S1 only A", "alt_S2_after": "S2 B fails after switch", "alt_S3_indep": "S3 independent",
         "alt_S4_common": "S4 shared cause", "alt_S5_recover": "S5 A recovers"}
KEYS = ("never", "always", "cusum", "v4", "always_x", "v5")
SEEDS = tuple(range(2100, 2110))


def _job(a):
    key, sc, seed = a
    name, params, told = V5_STRATS[key]
    r = run(name, dict(params), setting(0.95, 3.0, 0.15, 1.0, told), sc, seed)
    return dict(strategy=key, scenario=sc, seed=seed, loss=r["total_loss_fail"], switches=r["switches"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"])


def main():
    jobs = [(k, sc, sd) for k in KEYS for sc in SCEN for sd in SEEDS]
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(_job, jobs, chunksize=4)
    g = lambda k, sc, f="loss": np.mean([r[f] for r in rows if r["strategy"] == k and r["scenario"] == sc])
    L = ["# Feasibility: the alternative tool can degrade too (EXPLORATORY, not pre-registered)", "",
         f"Seeds {SEEDS[0]}-{SEEDS[-1]}; q 0.95, f 0.15, pi 1, leak 3; {len(rows)} runs; {time.time() - t0:.0f} s.", "",
         "## Mean total loss per task", "",
         "| Strategy | " + " | ".join(LABEL[s] for s in SCEN) + " |", "|---|" + "---|" * len(SCEN)]
    for k in KEYS:
        L.append(f"| {k} | " + " | ".join(f"{g(k, s):.1f}" for s in SCEN) + " |")
    L += ["", "## Loss compared with never checking", "", "| Strategy | " + " | ".join(LABEL[s] for s in SCEN) + " |",
          "|---|" + "---|" * len(SCEN)]
    for k in KEYS:
        L.append(f"| {k} | " + " | ".join(f"{100 * (g(k, s) / g('never', s) - 1):+.1f}%" for s in SCEN) + " |")
    L += ["", "## Mean tool switches per run", "", "| Strategy | " + " | ".join(LABEL[s] for s in SCEN) + " |",
          "|---|" + "---|" * len(SCEN)]
    for k in KEYS:
        L.append(f"| {k} | " + " | ".join(f"{g(k, s, 'switches'):.1f}" for s in SCEN) + " |")
    out = os.path.join("results", f"alt_feasibility_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out)


if __name__ == "__main__":
    main()
