"""Tests for the FR20 confirmatory-test plumbing: run()'s rho_belief override (a strategy can be
handed a WRONG fixed belief about the loud-failure share while the environment keeps the true s.rho) and the
rho_hat field in run()'s output for rules that learn it (ereplan/rule_rho.py)."""
from ereplan.config import Setting
from ereplan.runner import run

SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)


def _s(**kw):
    base = dict(q_true=0.8, q_assumed=0.8, check_frac=0.15, leak_mult=1.0, false_alarm=0.1, rho=0.1, n_tasks=200)
    return Setting().with_(**{**base, **kw})


def test_rho_belief_none_keeps_old_behaviour():
    """Default (no rho_belief): a rho-learning strategy still starts from the true s.rho, as before this change."""
    s = _s()
    a = run("Rule_v5_rho", dict(SESSION), s, "S1_sudden", seed=21)
    b = run("Rule_v5_rho", dict(SESSION), s, "S1_sudden", seed=21)
    assert a["total_loss_per_task"] == b["total_loss_per_task"]          # still reproducible
    assert a["rho_hat"] is not None


def test_rho_belief_overrides_only_the_strategy_not_the_environment():
    """With rho_belief = 0.9 and true s.rho = 0.1, a FIXED-rho rule (no learning) must behave as if failures were
    90% loud, even though the environment actually makes them 10% loud -- i.e. the override reaches the
    strategy's belief, not the environment's generator. Checked indirectly: Rule_v5_x (fixed rho, no learning)
    given the wrong belief must differ from the same rule given the true belief, on the same seed/scenario."""
    s = _s()
    wrong = run("Rule_v5_x", dict(SESSION, rho_belief=0.9), s, "S1_sudden", seed=22)
    true_ = run("Rule_v5_x", dict(SESSION), s, "S1_sudden", seed=22)
    assert wrong["total_loss_per_task"] != true_["total_loss_per_task"]


def test_rho_belief_is_reproducible():
    s = _s()
    a = run("Rule_v5_x", dict(SESSION, rho_belief=0.9), s, "S1_sudden", seed=23)
    b = run("Rule_v5_x", dict(SESSION, rho_belief=0.9), s, "S1_sudden", seed=23)
    assert a["total_loss_per_task"] == b["total_loss_per_task"]


def test_rho_hat_absent_for_rules_that_do_not_learn_rho():
    s = _s()
    res = run("Rule_v5_x", dict(SESSION), s, "S1_sudden", seed=24)
    assert "rho_hat" not in res


def test_rho_hat_moves_away_from_a_wrong_starting_belief_towards_the_truth():
    """Rule_v5_rho starts its belief at rho_belief (here deliberately wrong: 0.9, true rho = 0.1) and should learn
    downward over a long enough run."""
    s = _s(n_tasks=400)
    res = run("Rule_v5_rho", dict(SESSION, rho_belief=0.9), s, "S1_sudden", seed=25)
    assert res["rho_hat"] < 0.9
