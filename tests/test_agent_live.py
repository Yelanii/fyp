"""D1 (agent_live.py): the run loop on a small synthetic answer table, no models."""
import numpy as np
from ereplan import agent_live as d


def _table(n=60, seed=1):
    r = np.random.default_rng(seed)

    def mk(acc):
        rows = []
        for _ in range(n):
            loud = r.random() < 0.03
            ok = (not loud) and r.random() < acc
            rows.append(dict(value=None if loud else (1.0 if ok else 2.0), correct=ok, loud=loud,
                             flag=None if loud else bool(r.random() < (0.05 if ok else 0.45))))
        return rows
    return {"truth": [1.0] * n, "out": {"A_before": mk(0.66), "A_after": mk(0.53), "B": mk(0.85)}}


def test_conditions_make_A_better_before_and_B_after():
    g = lambda c, p, L: c / p + (1 - p) * (1 - d.RHO) * L
    for L, pb in d.CONDS:
        assert g(d.PRICE_A, d.ADV["A"], L) < g(pb, d.ADV["B"], L) < g(d.PRICE_A, 0.535, L)


def test_every_strategy_runs_and_fixed_B_never_uses_A():
    t = _table()
    for k in d.STRATS:
        r = d.run_one(t, k, 7000, 52.0, 100.0)
        assert r["loss"] > 0 and 0 <= r["wrong_rate"] <= 1 and 0 <= r["fail_rate"] <= 1
    assert d.run_one(t, "fix_B", 7000, 52.0, 100.0)["acc_a_after"] is None


def test_retry_repeats_a_deterministic_answer():
    t = _table()
    for o in t["out"]["A_before"] + t["out"]["A_after"] + t["out"]["B"]:   # every answer flagged and correct
        o.update(loud=False, correct=True, value=1.0, flag=True)
    r = d.run_one(t, "always", 7000, 52.0, 100.0)
    assert r["fail_rate"] == 1.0                                # the same flag on every retry: every task fails
