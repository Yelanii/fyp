"""Tests for the drift test's two simulator options (apply_drift.py) and its runner (run_drift.py)."""
import os
os.environ.setdefault("EREPLAN_NETPV", "1")
import numpy as np

from ereplan.config import Setting
from ereplan.env import Environment


def test_ramp_declines_linearly_from_the_sudden_drop_onset():
    s = Setting()
    for seed in (1, 2, 3):
        drop = Environment(s, "drop_0.75", seed).p[0]
        ramp = Environment(s, "ramp_0.75", seed).p[0]
        t0 = int(np.argmax(drop < 0.95))                 # first step of the sudden drop
        assert np.all(ramp[:t0 + 1] == 0.95)
        assert np.all(np.diff(ramp) <= 1e-12)            # never rises
        assert abs(ramp[t0 + 100] - 0.85) < 1e-9         # halfway after 100 calls
        assert np.all(np.abs(ramp[t0 + 200:] - 0.75) < 1e-9)


def test_checker_rates_change_once_at_a_drawn_step():
    s = Setting().with_(q_true=0.95, false_alarm=0.05, f_late=0.20)
    env = Environment(s, "drop_0.75", 9)
    assert 200 <= env.t_drift < 400
    assert env.f_at(env.t_drift - 1) == 0.05 and env.f_at(env.t_drift) == 0.20
    assert env.q_at(0) == 0.95 and env.q_at(599) == 0.95  # only f changes
    s2 = Setting().with_(q_true=0.95, false_alarm=0.05, q_late=0.60)
    env2 = Environment(s2, "drop_0.75", 9)
    assert env2.q_at(env2.t_drift - 1) == 0.95 and env2.q_at(env2.t_drift) == 0.60
    assert env2.f_at(599) == 0.05


def test_off_by_default():
    env = Environment(Setting().with_(false_alarm=0.15), "drop_0.75", 4)
    assert env.t_drift is None
    assert all(env.f_at(t) == 0.15 and env.q_at(t) == 0.8 for t in (0, 300, 599))


def test_false_alarm_rate_follows_the_change():
    s = Setting().with_(q_true=0.95, false_alarm=0.05, f_late=0.20, fa_persistence=0.0)
    env = Environment(s, "drop_0.95", 3)              # tool A never degrades, so most calls are correct
    before = [env.call(0, t, 0, True) for t in range(0, env.t_drift)]
    after = [env.call(0, t, 0, True) for t in range(env.t_drift, env.T)]
    fa = lambda xs: sum(x == "false_alarm" for x in xs) / sum(x in ("false_alarm", "ok") for x in xs)
    assert fa(before) < 0.10 < fa(after)


def test_runner_jobs():
    import run_drift as m
    g = m.job(("G", "v5", (0.75, 0.8, 1.0), 1604))
    d = m.job(("D", "v5_told", ("f_up", 0.75, 1.0), 1604))
    assert g["loss"] > 0 and d["loss"] > 0 and g["part"] == "G" and d["cond"][0] == "f_up"
