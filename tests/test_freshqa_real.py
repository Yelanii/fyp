"""Tests for the real-judge FreshQA environment (ereplan/freshqa_real.py), using the stub judge."""
import os
import numpy as np

from ereplan import freshqa_real as fr
from ereplan.v5_exp import setting


def _env(seed=5):
    if not os.path.exists(fr.verdict_path("stub")):
        fr.collect("stub")
    return fr.FreshQARealEnvironment(setting(0.8, 3.0, 0.15, 1.0, "true"), "fqr_news|stub", seed)


def test_verdicts_repeat_on_retries_and_follow_the_data():
    env = _env()
    T = env.T
    for t in range(T):
        outs = [env.call(0, t, a, True) for a in range(3)]
        non_loud = {o for o in outs if o != "loud"}
        assert len(non_loud) <= 1                       # same question, same answer, same verdict (pi = 1)
        row, v = env.pool[env.qs[t]]
        stale_now = t >= env.t0 and row["stale_wrong"]
        for o in non_loud:
            if stale_now:
                assert o == ("caught" if v["flag_old"] else "leak")
            else:
                assert o in ("ok", "false_alarm")


def test_fresh_tools_are_never_silently_wrong():
    env = _env()
    for t in range(env.T):
        assert env.call(1, t, 0, False) in ("ok", "loud")


def test_agreement_uses_the_judges_comparison():
    env = _env()
    for t in range(env.t0, env.T):
        row, v = env.pool[env.qs[t]]
        assert env.agree(0, 1, t, True, "ok") == v["same"]       # stale-era A vs B: the judge's comparison
        if fr.norm(row["old0"]) == fr.norm(row["new0"]):
            assert v["same"]                                       # identical answers always agree
    assert env.agree(1, 2, 10, True, "ok") is True                 # B and C give the same (fresh) answer


def test_loud_errors_follow_the_base_rates():
    env = _env(6)
    loud = np.mean([env.call(1, t, 0, False) == "loud" for t in range(env.T)])
    assert 0.02 < loud < 0.09
