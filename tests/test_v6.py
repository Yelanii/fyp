"""Tests for rule v6 (FR18, 10 Nov 2026), the any-tool scenarios and the fixed-tool references."""
import numpy as np
from ereplan.config import Setting
from ereplan.env import true_rates
from ereplan.runner import run
from ereplan.v5_exp import setting, SESSION


def test_any_scenarios_degrade_the_stated_number_of_tools_and_vary_which_one():
    s = Setting()
    hit = set()
    for seed in range(40):
        p = true_rates(s, "any_one", seed)
        bad = [k for k in range(3) if p[k].min() < 0.7]
        assert len(bad) == 1
        hit.add(bad[0])
        assert sum(true_rates(s, "any_two", seed)[k].min() < 0.7 for k in range(3)) == 2
        r = true_rates(s, "any_recover", seed)
        k = [k for k in range(3) if r[k].min() < 0.7][0]
        assert (r[k] < 0.7).sum() == 200 and r[k, -1] == s.tools[k].base_p          # it is repaired
    assert hit == {0, 1, 2}


def test_pdrop_degrades_in_roughly_the_stated_share_of_runs_and_never_at_p0():
    s = Setting()
    share = np.mean([true_rates(s, "pdrop_0.60@p50", sd)[0].min() < 0.7 for sd in range(200)])
    assert 0.38 < share < 0.62
    assert all(true_rates(s, "pdrop_0.60@p0", sd)[0].min() > 0.9 for sd in range(20))
    assert all(true_rates(s, "pdrop_0.60@p100", sd)[0].min() < 0.7 for sd in range(20))


def test_fixed_tool_policies_never_switch_or_check():
    s = setting(0.95, 3.0, 0.15, 1.0, "true")
    for name in ("R_fix_A", "R_fix_B", "R_fix_C"):
        r = run(name, dict(window=30), s, "any_one", 7)
        assert r["switches"] == 0 and r["checks_per_task"] == 0.0


def test_v6_is_reproducible_and_equals_v5_until_a_retest_happens():
    s = setting(0.95, 3.0, 0.15, 1.0, "none")
    a = run("Rule_v6", dict(SESSION), s, "any_recover", 11)
    b = run("Rule_v6", dict(SESSION), s, "any_recover", 11)
    assert a["total_loss_fail"] == b["total_loss_fail"]
    for seed in range(11, 31):                       # a run with no re-test must be identical to rule v5
        v6 = run("Rule_v6", dict(SESSION), s, "any_one", seed)
        if v6["retests"] == 0:
            assert v6["total_loss_fail"] == run("Rule_v5_x", dict(SESSION), s, "any_one", seed)["total_loss_fail"]
            break
    else:
        raise AssertionError("no run without a re-test found")


def test_v6_retests_a_tool_it_left_and_can_return_to_it():
    s = setting(0.95, 3.0, 0.15, 1.0, "none")
    rs = [run("Rule_v6", dict(SESSION), s, "any_recover", sd) for sd in range(40, 60)]
    v5 = [run("Rule_v5_x", dict(SESSION), s, "any_recover", sd) for sd in range(40, 60)]
    assert sum(r["retests"] for r in rs) > 0
    assert sum(r["switches"] for r in rs) > sum(r["switches"] for r in v5)      # it goes back; v5 never does
