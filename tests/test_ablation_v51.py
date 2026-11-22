"""Tests for the FR21 ablation: rule v5.1 with one ingredient removed at a time."""
from ereplan.config import Setting
from ereplan.runner import run
import ereplan.ablation_v51  # noqa: F401  (registers the ablation variants)

SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
DIRECT = dict(window=60, epsilon=0.02, k=3)   # SESSION minus the runner-only horizon_mode/session_cap


def _s(**kw):
    base = dict(q_true=0.8, q_assumed=0.5, check_frac=0.15, leak_mult=1.0, false_alarm=0.15, fa_persistence=0.8,
                xc_shared=0.3, third_shared=0.02, third_source_frac=0.5, audit_frac=0.08, n_tasks=200)
    return Setting().with_(**{**base, **kw})


def test_all_ablation_variants_run_and_are_reproducible():
    s = _s()
    for name in ("Rule_v5_1_nofa", "Rule_v5_1_noxc", "Rule_v5_1_noswitch", "Rule_v5_1_told"):
        a = run(name, dict(SESSION), s, "S1_sudden", seed=11)
        b = run(name, dict(SESSION), s, "S1_sudden", seed=11)
        assert a["total_loss_per_task"] == b["total_loss_per_task"]


def test_nofa_never_subtracts_a_false_alarm_cost():
    from ereplan.ablation_v51 import Rule_v5_1_nofa
    import numpy as np
    s = _s()
    rule = Rule_v5_1_nofa(s, np.random.default_rng(0), **DIRECT)
    assert rule.fa_cost(0.9, {"cur": 0, "trace": {}}) == 0.0


def test_noxc_never_cross_checks():
    s = _s(xc_shared=0.6, third_source_frac=1.0)
    res = run("Rule_v5_1_noxc", dict(SESSION), s, "S1_sudden", seed=12)
    assert res["crosschecks_per_task"] == 0.0
    assert res["third_checks_per_task"] == 0.0       # the third source needs a cross-check event to sample


def test_noswitch_never_switches():
    s = _s(q_true=0.5)                                 # severe degradation: the full rule would switch
    res_full = run("Rule_v5_1", dict(SESSION), s, "drop_0.5", seed=13)
    res_abl = run("Rule_v5_1_noswitch", dict(SESSION), s, "drop_0.5", seed=13)
    assert res_abl["switches"] == 0
    assert res_full["switches"] >= res_abl["switches"]


def test_told_never_learns_and_matches_the_assumed_values():
    from ereplan.ablation_v51 import Rule_v5_1_told
    import numpy as np
    s = _s(q_assumed=0.77, false_alarm=0.22)
    rule = Rule_v5_1_told(s, np.random.default_rng(0), **DIRECT)
    assert rule.cm.q_mean == 0.77
    assert abs(rule.cm.f_mean - 0.22) < 1e-9
    rule.observe(0, True, True, kind="flag_agree", a=0.9)   # should not move the fixed memory at all
    assert rule.cm.q_mean == 0.77 and abs(rule.cm.f_mean - 0.22) < 1e-9


def test_huge_window_disables_change_detection_and_changes_the_outcome():
    """No separate class for this ingredient: Rule_v5_1 itself with an effectively infinite window. Checks only
    that it actually changes behaviour relative to the normal window, on a scenario with a real change."""
    s = _s()
    normal = run("Rule_v5_1", dict(SESSION), s, "S1_sudden", seed=14)
    no_window = run("Rule_v5_1", dict(SESSION, window=1_000_000), s, "S1_sudden", seed=14)
    assert normal["total_loss_per_task"] != no_window["total_loss_per_task"]
