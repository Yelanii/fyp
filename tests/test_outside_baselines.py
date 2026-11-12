"""Tests for the Core 2 outside baselines (ereplan/outside_baselines.py)."""
import math
import numpy as np

from ereplan.outside_baselines import SSVStyle, RDECusum, GLRklUCB, glr_detect, kl_ucb, _kl
from ereplan.v5_exp import setting
from ereplan.runner import run


def _s():
    return setting(0.8, 3.0, 0.15, 1.0, "true")


def test_kl_ucb_is_the_largest_q_within_the_bound():
    q = kl_ucb(0.7, 50, math.log(100))
    assert 0.7 < q < 1.0
    assert 50 * _kl(0.7, q) <= math.log(100) + 1e-6
    assert 50 * _kl(0.7, min(q + 1e-3, 1 - 1e-9)) > math.log(100)


def test_glr_detects_a_clear_change_and_not_a_stationary_stream():
    r = np.random.default_rng(0)
    stable = (r.random(400) < 0.95).astype(float)
    assert not glr_detect(stable, 1 / math.sqrt(600))
    changed = np.r_[(r.random(200) < 0.95), (r.random(200) < 0.5)].astype(float)
    assert glr_detect(changed, 1 / math.sqrt(600))


def test_ssv_updates_follow_algorithm_1():
    st = SSVStyle(_s(), np.random.default_rng(1), alpha=0.1, beta=0.1, eta=0.5, qx=0.5)
    st._w, st._q = 1.0, 0.5                       # accepted region (w > tau_A = 0.5), explored, found wrong
    st.ssv_feedback(0)
    assert np.isclose(st.tA, 0.5 + 0.5 * (1 - 0.1) / 0.5)   # accept threshold rises
    assert np.isclose(st.tR, 0.5)                            # g = 0 does not move tau_R
    st._w, st._q = 0.0, 0.5                       # rejected region, explored, found correct
    st.ssv_feedback(1)
    assert np.isclose(st.tR, max(0.5 + 0.5 * (0.1 - 1) / 0.5, -1e9))
    assert st.tR <= st.tA


def test_ssv_middle_band_always_queries_the_strong_verifier():
    st = SSVStyle(_s(), np.random.default_rng(2), qx=0.0)
    st.tR, st.tA = -0.1, 1.1                     # both verdicts inside the band
    assert all(st.ssv_action(0, fl) == "SV" for fl in (True, False) for _ in range(20))
    st.tR, st.tA = 0.5, 0.5
    assert st.ssv_action(0, False) == "A" and st.ssv_action(0, True) == "R"


def test_rde_cusum_skips_checks_while_the_statistic_is_negative():
    st = RDECusum(_s(), np.random.default_rng(3), mu=0.25)
    st.D = -1.0
    acts = []
    ctx = {"cur": 0, "u": 5, "t": 0, "left_in_run": 600}
    for _ in range(5):
        acts.append(st.decide(dict(ctx)))
    assert acts[:4] == ["call"] * 4 and acts[4] == "call_and_check"


def test_baselines_run_and_are_reproducible():
    for name in ("B13_ssv", "B14_rdecusum", "B15_glrklucb"):
        a = run(name, {}, _s(), "drop_0.75", 1601)
        b = run(name, {}, _s(), "drop_0.75", 1601)
        assert a["total_loss_fail"] == b["total_loss_fail"] and np.isfinite(a["total_loss_fail"])
