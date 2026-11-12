"""Tests for rule v5 (27 Oct 2026): label-free checker learning and cross-checking."""
import numpy as np

from ereplan.config import Setting
from ereplan.crosscheck import CheckerMemory, FG
from ereplan.runner import run

SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)


def _sample_obs(rng, n, p, q, f, a, rho=0.5):
    """Draw n checked observations from the likelihood in crosscheck.py's docstring."""
    out = []
    for _ in range(n):
        correct = rng.random() < p
        if correct:
            if rng.random() < f:                      # false alarm
                u = rng.random()
                out.append("flag_agree" if u < a else ("flag_altloud" if u < a + (1 - a) * rho else "flag_disagree"))
            else:
                out.append("none")
        else:
            if rng.random() < rho:
                out.append("loud")
            elif rng.random() < q:                    # caught
                out.append("flag_altloud" if rng.random() < (1 - a) * rho else "flag_disagree")
            else:
                out.append("none")
    return out


def test_checker_memory_learns_f_and_q_without_labels():
    rng = np.random.default_rng(0)
    p, q, f, a = 0.7, 0.9, 0.15, 0.95
    cm = CheckerMemory(0.5)
    for k in _sample_obs(rng, 3000, p, q, f, a):
        cm.update(k, p, a)
    assert abs(cm.f_mean - f) < 0.03
    assert abs(cm.q_mean - q) < 0.1


def test_told_memory_is_a_point_mass_and_ignores_data():
    cm = CheckerMemory(0.5, fixed=(0.8, 0.14))
    before = (cm.q_mean, cm.f_mean)
    cm.update("flag_agree", 0.9, 0.95)
    assert (cm.q_mean, cm.f_mean) == before
    assert abs(cm.q_mean - 0.8) < 0.02 and abs(cm.f_mean - FG[np.argmin(abs(FG - 0.14))]) < 1e-9


def test_crosscheck_resolves_false_alarms_so_no_task_fails_from_them():
    s = Setting().with_(q_true=0.95, q_assumed=0.95, check_frac=0.15, leak_mult=3.0, false_alarm=0.15,
                        fa_persistence=1.0)
    r_x = run("B12_always_x", dict(window=30), s, "drop_0.85", 1600)
    r_1 = run("B1_always", dict(window=30), s, "drop_0.85", 1600)
    assert r_x["fa_failed_rate"] == 0.0 and r_x["fa_resolved_per_task"] > 0
    assert r_1["fail_rate"] > r_x["fail_rate"]


def test_v5_is_reproducible_and_reports_learned_values():
    s = Setting().with_(q_true=0.8, q_assumed=0.5, fa_assumed=0.0, check_frac=0.15, leak_mult=1.0,
                        false_alarm=0.05, fa_persistence=0.0)
    a = run("Rule_v5_x", dict(SESSION), s, "drop_0.75", 1601)
    b = run("Rule_v5_x", dict(SESSION), s, "drop_0.75", 1601)
    assert a["total_loss_fail"] == b["total_loss_fail"]
    assert 0.0 <= a["f_hat"] <= 0.5 and a["cm_obs"] > 0


def test_bayes_policy_value_matches_simulation_and_beats_simple_rules():
    from ereplan.config import Tool
    from ereplan.bayes_opt import BayesPolicy
    tools = (Tool("A", 20.0, 1.0, 0.95, 0.95), Tool("B", 24.0, 1.0, 0.95, 0.95))
    s = Setting(tools=tools, steps_per_task=1, n_tasks=600, r_max=0).with_(
        q_true=0.95, q_assumed=0.95, check_frac=0.15, leak_mult=15.0, false_alarm=0.05, fa_persistence=1.0)
    pol = BayesPolicy(s, 0.75)
    sims = [run("B13_bayes", dict(p1=0.75), s, "drop_0.75", sd)["total_loss_fail"] for sd in range(1900, 1910)]
    never = [run("B2_never", dict(window=30), s, "drop_0.75", sd)["total_loss_fail"] for sd in range(1900, 1910)]
    assert abs(np.mean(sims) - pol.V[0, 0] / 600) < 1.0
    assert np.mean(sims) < np.mean(never)
