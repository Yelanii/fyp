"""Unit tests built from the worked examples in the proposal (Sections 2.4.5 and 3.3.5.5)."""
import math
import numpy as np
import pytest

from ereplan.config import Setting, Tool
from ereplan.env import Environment
from ereplan.estimator import RangeEstimator
from ereplan.runner import run
from ereplan.strategies import (switch_line, protection_value, decision_value, ThreeZoneRule)


def two_tool_setting():
    return Setting(tools=(Tool("A", 20.0, 0.0, 0.95, 0.95), Tool("B", 24.0, 0.0, 1.0, 1.0)),
                   switch_cost=5.0, lam=0.0)


def test_switch_line_worked_example():
    # 3 calls left at price 20, R_rest = 0, R_alt + c_switch = 72 + 5 = 77 -> line = 60/77 (about 78%)
    s = two_tool_setting()
    line, alt, R_alt = switch_line(s, 0, 3, {0: 0.9, 1: 1.0}, s.switch_cost)
    assert alt == 1 and R_alt == pytest.approx(72.0)
    assert line == pytest.approx(60 / 77)
    # at p = 0.80 staying costs 75 (< 77): stay; at p = 0.75 it costs 80 (> 77): switch
    assert 3 * 20 / 0.80 < 77 < 3 * 20 / 0.75


def test_line_moves_with_the_plan():
    s = two_tool_setting()
    lines = [switch_line(s, 0, u, {0: 0.9, 1: 1.0}, s.switch_cost)[0] for u in (1, 3, 5)]
    assert lines[0] < lines[1] < lines[2]          # fewer calls left -> switching is worth less


def test_check_correction_removes_bias():
    # p = 0.80, rho = 0.5, q = 0.8: checked calls show 18% failures; naive estimate would read 82%
    est = RangeEstimator(window=1000, rho=0.5, q=0.8, prior_mean=0.5, prior_strength=2.0)
    for i in range(1000):
        est.update(True, i < 180)
    mean, low, high = est.summary()
    assert mean == pytest.approx(0.80, abs=0.01)
    assert low < 0.80 < high


def test_unchecked_loud_failures_are_free_evidence():
    est = RangeEstimator(window=400, rho=0.5, q=0.8, prior_mean=0.5, prior_strength=2.0)
    for i in range(400):                         # true p = 0.8 -> loud failure share 0.1
        est.update(False, i < 40)
    assert est.mean == pytest.approx(0.80, abs=0.02)


def test_protection_value_formula():
    s = Setting()
    assert protection_value(0.9, s) == pytest.approx(s.q_assumed * 0.1 * (1 - s.rho) * s.leak_loss)


def test_decision_value_zero_far_from_line():
    s = Setting()
    est = RangeEstimator(60, s.rho, s.q_assumed, 0.95, s.prior_strength)
    for _ in range(60):
        est.update(True, False)                  # a perfect record: no result of 3 checks can flip "stay"
    line, alt, R_alt = switch_line(s, 0, 5, {0: est.mean, 1: 0.95, 2: 0.95}, s.switch_cost)
    assert decision_value(est, s, 0, 5, R_alt, 3) == pytest.approx(0.0, abs=1e-9)


def test_rule_switches_when_whole_range_below_line():
    s = Setting()
    rule = ThreeZoneRule(s, np.random.default_rng(0), window=60, epsilon=0.0, k=3)
    for i in range(60):
        rule.ests[0].update(True, i < 30)        # very unreliable tool
    ctx = {"cur": 0, "u": 5, "t": 0, "left_in_run": 100}
    assert rule.decide(ctx) == "switch"


def test_common_random_numbers_and_reproducibility():
    s = Setting()
    e1, e2 = Environment(s, "S1_sudden", 3), Environment(s, "S1_sudden", 3)
    assert np.array_equal(e1.p, e2.p) and np.array_equal(e1.u_success, e2.u_success)
    r1 = run("Rule", {}, s, "S2_gradual", 1)
    r2 = run("Rule", {}, s, "S2_gradual", 1)
    assert r1["spend"] == r2["spend"] and r1["checks_per_task"] == r2["checks_per_task"]


def test_scenarios_match_table_3_12():
    s = Setting()
    for sc, low in (("S1_sudden", 0.60), ("S2_gradual", 0.70), ("S3_harmless", 0.85)):
        p = Environment(s, sc, 0).p
        assert p[0, 0] == pytest.approx(0.95) and p[0, -1] == pytest.approx(low)
        assert np.allclose(p[1], 0.95)


def test_optimum_task_formula_matches_simulation():
    from ereplan.optimum import _step
    s = Setting().with_(q_true=0.8, q_assumed=0.8, check_frac=0.15, leak_mult=3.0)
    steps = [(0.95, 20.0), (0.7, 20.0), (0.6, 24.0)]
    pattern = (False, True, False)
    a0, a1, spend, leak = 1.0, 0.0, 0.0, 0.0
    for (p, c), chk in zip(steps, pattern):
        e, pl, px = _step(p, c, s.check_price, chk, s)
        spend += (a0 + a1) * e; leak += a0 * pl
        a0, a1 = a0 * (1 - pl - px), a1 * (1 - px) + a0 * pl
    exact = spend + s.leak_loss * leak
    rng = np.random.default_rng(7); N = 40000; tot = 0.0
    for _ in range(N):
        sp, leaked = 0.0, False
        for (p, c), chk in zip(steps, pattern):
            done = False
            for _a in range(s.r_max + 1):
                sp += c + (s.check_price if chk else 0)
                if rng.random() < p: done = True; break
                if rng.random() < s.rho: continue
                if chk and rng.random() < s.q_true: continue
                leaked = True; done = True; break
            if not done:
                break
        tot += sp + (s.leak_loss if leaked else 0)
    assert tot / N == pytest.approx(exact, rel=0.02)


def test_optimum_is_a_lower_bound_on_average():
    from ereplan.optimum import optimum
    s = Setting().with_(q_true=0.8, q_assumed=0.8, check_frac=0.15, leak_mult=3.0)
    bound = np.mean([optimum(s, "drop_0.75", sd)[0] for sd in (1, 2)])
    oracle = np.mean([run("B6_oracle", {}, s, "drop_0.75", sd)["total_loss_per_task"] for sd in (1, 2)])
    assert bound <= oracle * 1.03


def test_selfcal_estimator_recovers_bad_checker():
    # true tool success 0.7, loud share 0.5, but the check catches only 10% of silent failures;
    # the agent wrongly assumes 0.8. The joint estimate should recover both p and q.
    from ereplan.selfcal import JointEstimator
    rng = np.random.default_rng(3)
    est = JointEstimator(window=2000, rho=0.5, q_prior_mean=0.8, q_prior_strength=3.0,
                         p_prior_mean=0.95, p_prior_strength=20.0)
    for _ in range(2000):
        checked = True
        if rng.random() < 0.7:
            kind = "none"
        elif rng.random() < 0.5:
            kind = "loud"
        else:
            kind = "caught" if rng.random() < 0.1 else "none"
        est.update(checked, kind)
    mean, low, high = est.summary()
    assert mean == pytest.approx(0.7, abs=0.04)
    assert est.q_hat == pytest.approx(0.1, abs=0.07)


def test_gsm8k_gold_plan_runs():
    import json
    from ereplan.realagent import gold_plan, execute
    r = json.loads(open("data/raw/gsm8k_test.jsonl").readline())
    plan = gold_plan(r["answer"])
    assert execute(plan) == pytest.approx(18.0)          # Janet's ducks: 16 - 3 - 4 = 9; 9 * 2 = 18
    assert plan["steps"][1][1] == "r1*2"                  # the second step refers to the first result


def test_false_alarms_are_persistent_and_only_on_checked_correct_calls():
    s = Setting().with_(false_alarm=0.3)
    env = Environment(s, "drop_0.95", 5)
    for t in range(200):
        outs = [env.call(0, t, a, True) for a in range(3)]
        for a, o in enumerate(outs):
            if env.u_success[0, t, a] < env.p[0, t]:                 # a correct result
                assert o == ("false_alarm" if env.u_fa[t, 0] < 0.3 else "ok")
        assert all(env.call(0, t, a, False) != "false_alarm" for a in range(3))   # unchecked: never


def test_rule_v4_reduces_to_v3_likelihood_when_f_is_zero():
    from ereplan.selfcal import JointEstimator
    from ereplan.fa_rule import JointEstimatorFA
    a = JointEstimator(60, 0.5, 0.8, 3.0, 0.95, 20.0)
    b = JointEstimatorFA(60, 0.5, 0.8, 3.0, 0.95, 20.0, f=0.0)
    for i in range(60):
        kind = ("loud", "caught", "none", "none")[i % 4]
        a.update(i % 2 == 0, kind); b.update(i % 2 == 0, kind)
    assert np.allclose(a.joint(), b.joint())


# ----------------------------------------------------------------------------- part E
def test_persistence_dial_endpoints_reproduce_old_cases():
    for old, pi in ((True, 1.0), (False, 0.0)):
        a = Environment(Setting(false_alarm=0.15, fa_persistent=old), "drop_0.75", 7)
        b = Environment(Setting(false_alarm=0.15, fa_persistence=pi), "drop_0.75", 7)
        outs_a = [a.call(k, t, att, True) for k in range(3) for t in range(0, 600, 7) for att in range(3)]
        outs_b = [b.call(k, t, att, True) for k in range(3) for t in range(0, 600, 7) for att in range(3)]
        assert outs_a == outs_b


def test_reflag_rate_matches_persistence():
    # all tools always correct, so every flag is a false alarm; P(flag again | flagged) = pi + (1 - pi) f
    tools = tuple(Tool(n, 20.0 + i, 1.0, 1.0, 1.0) for i, n in enumerate("ABC"))
    s = Setting(tools=tools, n_tasks=4000, false_alarm=0.2, fa_persistence=0.6)
    e = Environment(s, "S3_harmless", 1)
    first = again = 0
    for t in range(e.T):
        if e.call(1, t, 0, True) == "false_alarm":
            first += 1
            again += e.call(1, t, 1, True) == "false_alarm"
    assert again / first == pytest.approx(0.6 + 0.4 * 0.2, abs=0.03)


def test_recheck_repeats_verdict_when_fully_persistent():
    e = Environment(Setting(false_alarm=0.15, fa_persistence=1.0), "drop_0.75", 3)
    assert all(e.recheck(0, t, 0, j, True, True) for t in range(0, 600, 11) for j in (1, 2))


def test_v4_pi_equals_v4_when_persistence_is_one():
    from ereplan.litbaselines import fa_cost_pi
    s = Setting(false_alarm=0.14, q_true=0.95, q_assumed=0.95, leak_mult=3.0)
    p = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50, q_prior_strength=3.0)
    a = run("Rule_v4_fa", p, s, "drop_0.75", 11)
    b = run("Rule_v4_pi", dict(p, pi_assumed=1.0), s, "drop_0.75", 11)
    assert a["total_loss_fail"] == b["total_loss_fail"] and a["checks_per_task"] == b["checks_per_task"]
    # independence (pi = 0): the step fails only if every retry is flagged; one extra attempt expected
    f, m = 0.1, 0.9
    want = m * f * (f ** s.r_max * s.task_cost + (1 + f) * (s.eff_price(0) + s.check_price))
    assert fa_cost_pi(m, f, 0.0, s, 0) == pytest.approx(want)


def test_tool_memory_is_fixed_within_a_task():
    from ereplan.litbaselines import BetaToolMemory
    s = Setting()
    m = BetaToolMemory(s, np.random.default_rng(0), n_off=20)
    before = m.ests[0].mean
    for _ in range(5):
        m.observe(0, False, True)
    assert m.ests[0].mean == before                  # not updated during the episode
    m.start_task({"t": 5, "u": 5, "cur": 0, "left_in_run": 595})
    assert m.ests[0].mean < before                   # updated once the episode ends


def test_real_judge_retries_use_fresh_seeds_only_when_sampling():
    from ereplan.realagent import Judge
    seen = []
    class FakeLLM:
        model = "fake"
        def __call__(self, prompt, max_tokens=256, stop=None, temperature=0.0, seed=0):
            seen.append((temperature, seed)); return "7"
    for att in range(3):
        Judge(FakeLLM(), "recompute", temperature=0.0, seed=0).says_wrong("3+4", 7.0, "ok", attempt=att)
        Judge(FakeLLM(), "recompute", temperature=0.7, seed=1).says_wrong("3+4", 7.0, "ok", attempt=att)
    assert [s for t, s in seen if t == 0.0] == [0, 0, 0]          # greedy: same question, same cached answer
    assert [s for t, s in seen if t == 0.7] == [1, 2, 3]          # sampled: each retry is a fresh draw
