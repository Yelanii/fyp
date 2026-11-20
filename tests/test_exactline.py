"""Exact step cost (PREREGISTRATION_exactline.md): it equals Theorem 1's loss of policy N, and the variant runs."""
import numpy as np
from ereplan.config import Setting
from ereplan.strategies import exact_step_cost, leak_aware_line
from ereplan.theory import Step, loss_never


def test_exact_step_cost_equals_theorem_1_policy_N():
    s = Setting()
    for p in (0.6, 0.75, 0.85, 0.95, 1.0):
        st = Step(p=p, L=s.leak_loss, F=s.task_cost, f=0.0, q=0.0, R=s.r_max, rho=s.rho, w=s.eff_price(0), c=0.0)
        assert abs(exact_step_cost(s, 0, p) - loss_never(st)) < 1e-9


def test_exact_cost_is_one_call_when_failures_are_silent():
    s = Setting().with_(rho=0.0)
    assert abs(exact_step_cost(s, 0, 0.7) - (s.eff_price(0) + 0.3 * s.leak_loss)) < 1e-9


def test_exact_line_is_off_by_default_and_differs_when_on():
    s = Setting()
    alt = {0: 0.80, 1: 0.95, 2: 0.97}
    assert leak_aware_line(s, 0, 50, alt, s.switch_cost) == leak_aware_line(s, 0, 50, alt, s.switch_cost, exact=False)
    assert leak_aware_line(s, 0, 50, alt, s.switch_cost)[0] != leak_aware_line(s, 0, 50, alt, s.switch_cost, exact=True)[0]
