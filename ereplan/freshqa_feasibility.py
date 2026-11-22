"""FreshQA-grounded feasibility check (EXPLORATORY, not pre-registered).

Natural degradation instead of simulated drops. Tool A answers from the FreshQA snapshot of 24 Nov 2025 (price 20);
tool B answers from the 21 Apr 2026 snapshot (price 24); tool C is a premium service (price 30). Questions are real
FreshQA questions, matched by text across the two snapshots (data/processed/freshqa_staleness.json, built by
tools/freshqa_compare.py). At a random call t0 in [150, 350) the world moves on: from then on, tool A's answer to a
question is wrong exactly when FreshQA's April 2026 snapshot no longer accepts its November 2025 answer. Stale answers
are SILENT (never an error message). Base failure rates: 5% for A and B before/apart from staleness, 3% for C.

Two question streams: 'news' (fast-changing questions only; 50.7% go stale) and 'mixed' (all question types; 14.5%).
The checker is still SIMULATED, with catch rate 0.95 and false-alarm rate 0.15 that repeats on retries, as measured
for the real Qwen2.5 checkers. So this tests the rules on real fault patterns, not real checker behaviour.

Usage: python -m ereplan.freshqa_feasibility
"""
import json, os, time
from multiprocessing import Pool
import numpy as np

from . import runner
from .env import Environment, _rng
from .v5_exp import STRATS as V5_STRATS, setting

DATA = "data/processed/freshqa_staleness.json"
STREAMS = {"fq_news": lambda r: r["fact"] == "fast-changing", "fq_mixed": lambda r: True}
KEYS = ("never", "always", "cusum", "v4", "always_x", "v5", "v5_1_noaudit", "v5_1")
SEEDS = tuple(range(2300, 2310))
_ROWS = None


class FreshQAEnvironment(Environment):
    def __init__(self, setting, scenario, seed):
        global _ROWS
        if not scenario.startswith("fq_"):
            return super().__init__(setting, scenario, seed)
        super().__init__(setting, "drop_0.95", seed)          # base random streams; rates are replaced below
        if _ROWS is None:
            _ROWS = json.load(open(DATA))["rows"]
        pool = [r for r in _ROWS if STREAMS[scenario](r)]
        r = _rng("freshqa", scenario, seed)
        T = self.p.shape[1]
        qs = r.integers(0, len(pool), T)                       # one real question per call
        stale = np.array([pool[i]["stale_wrong"] for i in qs], dtype=bool)
        t0 = int(r.integers(150, 350))
        self.p[0, :] = 0.95
        hit = (np.arange(T) >= t0) & stale
        self.p[0, hit] = 0.0                                   # tool A's answer is now out of date: wrong
        A = self.u_loud.shape[2]
        self.u_loud[0, hit, :] = 1.0                           # ... and silently so (never an error message)
        self.t0, self.stale_share = t0, float(stale.mean())


runner.Environment = FreshQAEnvironment                        # the runner builds environments through this name


def _job(a):
    key, sc, seed = a
    name, params, told = V5_STRATS[key]
    r = runner.run(name, dict(params), setting(0.95, 3.0, 0.15, 1.0, told), sc, seed)
    return dict(strategy=key, stream=sc, seed=seed, loss=r["total_loss_fail"], leak_rate=r["leak_rate"],
                fail_rate=r["fail_rate"], checks=r["checks_per_task"], switches=r["switches"])


def main():
    jobs = [(k, sc, sd) for k in KEYS for sc in STREAMS for sd in SEEDS]
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(_job, jobs, chunksize=4)
    g = lambda k, sc, f="loss": np.mean([x[f] for x in rows if x["strategy"] == k and x["stream"] == sc])
    lab = {"fq_news": "news (fast-changing)", "fq_mixed": "mixed (all types)"}
    L = ["# FreshQA-grounded feasibility check (EXPLORATORY, not pre-registered)", "",
         f"Seeds {SEEDS[0]}-{SEEDS[-1]}; real FreshQA staleness (Nov 2025 -> Apr 2026); simulated checker q 0.95, f 0.15, "
         f"repeating; wrong answer = 3 tasks; {len(rows)} runs; {time.time() - t0:.0f} s.", "",
         "| Strategy | " + " | ".join(f"{lab[s]} loss" for s in STREAMS) + " | " + " | ".join(f"{lab[s]} vs never" for s in STREAMS)
         + " | wrong answers kept (news) | failed tasks (news) | switches (news) |", "|---|" + "---|" * (2 * len(STREAMS) + 3)]
    for k in KEYS:
        L.append(f"| {k} | " + " | ".join(f"{g(k, s):.1f}" for s in STREAMS) + " | "
                 + " | ".join(f"{100 * (g(k, s) / g('never', s) - 1):+.1f}%" for s in STREAMS)
                 + f" | {g(k, 'fq_news', 'leak_rate'):.1%} | {g(k, 'fq_news', 'fail_rate'):.1%} | {g(k, 'fq_news', 'switches'):.1f} |")
    out = os.path.join("results", f"freshqa_feasibility_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out)


if __name__ == "__main__":
    main()
