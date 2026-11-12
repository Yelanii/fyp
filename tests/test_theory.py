"""Tests for the Core 3 theory (ereplan/theory.py)."""
import itertools
import numpy as np

from ereplan.theory import Step, loss_never, loss_check, loss_cross, fail_prob_correct, wrong_check_region
from ereplan.theory_check import simulate
from ereplan.config import Setting
from ereplan.env import Environment


def _G(st, kappa):
    l, s = (1 - st.p) * st.rho, (1 - st.p) * (1 - st.rho)
    A = st.w + st.c + s * (1 - st.q) * st.L
    return A * sum(kappa ** a for a in range(st.R + 1)) + st.F * kappa ** (st.R + 1)


def test_closed_forms_at_the_two_extremes():
    for p, f, R in itertools.product((0.5, 0.9, 0.99), (0.05, 0.2), (0, 1, 3)):
        st = Step(p=p, f=f, R=R)
        l, s = (1 - p) * st.rho, (1 - p) * (1 - st.rho)
        k0 = l + s * st.q + p * f
        assert np.isclose(loss_check(st.with_(pi=0.0)), _G(st, k0))
        kb, kg = l + s * st.q + p, l + s * st.q
        assert np.isclose(loss_check(st.with_(pi=1.0)), f * _G(st, kb) + (1 - f) * _G(st, kg))


def test_monotone_in_persistence_and_strict_with_retries():
    pis = np.linspace(0, 1, 11)
    for p, f, R in itertools.product((0.4, 0.8, 0.97), (0.05, 0.3), (0, 1, 2, 4)):
        v = np.array([loss_check(Step(p=p, f=f, R=R, pi=pi)) for pi in pis])
        if R == 0:
            assert np.allclose(v, v[0])                     # one attempt: persistence cannot matter
        else:
            assert np.all(np.diff(v) > 0)                   # strictly increasing in pi


def test_p_equal_one_gives_rule_v4_false_alarm_cost():
    # Rule_v4_pi (persistence_exp.py): FA = f [g^R F + (1 + g + ... + g^(R-1)) (w + c)], g = pi + (1 - pi) f
    for f, pi, R in itertools.product((0.05, 0.15), (0.0, 0.5, 1.0), (1, 2, 3)):
        st = Step(p=1.0, f=f, pi=pi, R=R)
        g = pi + (1 - pi) * f
        fa = f * (g ** R * st.F + sum(g ** k for k in range(R)) * (st.w + st.c))
        assert np.isclose(loss_check(st) - (st.w + st.c), fa)


def test_failure_probability_of_a_correct_step():
    for f, pi, R in itertools.product((0.05, 0.15), (0.0, 0.3, 1.0), (1, 2)):
        st = Step(p=1.0, f=f, pi=pi, R=R, w=0.0, c=0.0, L=0.0, F=1.0)
        assert np.isclose(loss_check(st), fail_prob_correct(f, pi, R))


def test_retry_cannot_rescue_a_false_alarm_when_pi_is_one():
    # Proposition 1: with pi = 1, once a correct attempt is flagged, the step ends failed or with a wrong output.
    s = Setting(n_tasks=2000, rho=0.5, q_true=0.8, false_alarm=0.3, fa_persistence=1.0, r_max=3)
    env = Environment(s, "drop_0.95", 11)
    env.p[0, :] = 0.7
    seen = 0
    for t in range(env.T):
        flagged_correct = False
        for att in range(s.r_max + 1):
            out = env.call(0, t, att, True)
            if out == "false_alarm":
                flagged_correct = True
                continue
            if out in ("loud", "caught"):
                continue
            if flagged_correct:
                seen += 1
                assert out == "leak"                       # never 'ok' after a false alarm on this step
            break
    assert seen > 50


def test_formulas_match_the_simulator():
    for st in (Step(p=0.8, f=0.15, pi=0.5, R=2), Step(p=0.95, f=0.05, pi=1.0, R=1)):
        for pol, fn in (("N", loss_never), ("C", loss_check), ("X", loss_cross)):
            sim, _ = simulate(st, pol, seeds=(7100,), n_tasks=3000)
            assert abs(sim / fn(st) - 1) < 0.02


def test_cross_check_is_far_less_sensitive_to_persistence():
    for p, f in itertools.product((0.8, 0.95), (0.05, 0.15)):
        st = Step(p=p, f=f)
        dc = loss_check(st.with_(pi=1.0)) - loss_check(st.with_(pi=0.0))
        dx = loss_cross(st.with_(pi=1.0)) - loss_cross(st.with_(pi=0.0))
        assert 0 <= dx < 0.05 * dc


def test_wrong_check_region_grows_with_persistence():
    base = Step(p=0.9, f=0.15, L=360.0, F=360.0)
    masks = [wrong_check_region(base.with_(pi=pi))[1] for pi in (0.2, 0.5, 0.8, 1.0)]
    for a, b in zip(masks, masks[1:]):
        assert np.all(b[a]) and b.sum() > a.sum()
    assert masks[0].any()
