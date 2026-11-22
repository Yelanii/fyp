"""Tests for rule v5.1 (FR19): the third source, the labelled audit, and the v4 fallback."""
import numpy as np

from ereplan.config import Setting
from ereplan.rule_v5_1 import Rule_v5_1
from ereplan.runner import run

SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)


DIRECT = dict(window=60, epsilon=0.02, k=3)   # SESSION minus the runner-only horizon_mode/session_cap


def _make_rule(**kw):
    s = Setting().with_(q_true=0.8, q_assumed=0.5, check_frac=0.15, leak_mult=1.0, false_alarm=0.1,
                        fa_persistence=0.8)
    rng = np.random.default_rng(0)
    return Rule_v5_1(s, rng, **{**DIRECT, **kw})


def test_sigma_hat_recovers_a_known_shared_mistake_rate():
    """Drive observe_third() directly with a known mixture of shared-mistake and genuine-false-alarm agreements
    and check the method-of-moments estimate recovers the true sigma within a reasonable tolerance."""
    rule = _make_rule()
    true_sigma, f_true, third_shared = 0.6, 0.1, rule.third_shared_belief
    rule.audit_f_n, rule.audit_f_hits = 500, int(round(500 * f_true))  # pin f via a large synthetic audit
    rng = np.random.default_rng(1)
    for _ in range(400):
        is_shared = rng.random() < true_sigma
        if is_shared:
            third_confirms = rng.random() < third_shared       # third source reproduces the shared mistake
        else:
            third_confirms = rng.random() >= f_true              # third source's own false-alarm chance
        rule.observe_third(agree=True, third_confirms=third_confirms)
    assert abs(rule.sigma_hat - true_sigma) < 0.12


def test_sigma_hat_stays_low_when_agreements_are_genuine_false_alarms():
    rule = _make_rule()
    rule.audit_f_n, rule.audit_f_hits = 500, 50     # f = 0.1
    rng = np.random.default_rng(2)
    for _ in range(300):
        third_confirms = rng.random() >= 0.1
        rule.observe_third(agree=True, third_confirms=third_confirms)
    assert rule.sigma_hat < 0.2


def test_audited_q_and_f_converge_from_labels():
    rule = _make_rule()
    rng = np.random.default_rng(3)
    true_q, true_f = 0.85, 0.12
    for _ in range(600):
        if rng.random() < 0.5:
            flagged = rng.random() < true_f
            rule.observe_audit(checked=True, outcome_kind="caught" if flagged else "none", truly_correct=True)
        else:
            flagged = rng.random() < true_q
            rule.observe_audit(checked=True, outcome_kind="caught" if flagged else "none", truly_correct=False)
    assert abs(rule.audited_q - true_q) < 0.08
    assert abs(rule.audited_f - true_f) < 0.06


def test_observe_audit_ignores_unchecked_calls():
    rule = _make_rule()
    before = (rule.audit_q_n, rule.audit_f_n)
    rule.observe_audit(checked=False, outcome_kind="none", truly_correct=True)
    assert (rule.audit_q_n, rule.audit_f_n) == before


def test_fallback_triggers_with_enough_evidence_of_high_sigma_and_not_with_low_sigma():
    high = _make_rule()
    high.audit_f_n, high.audit_f_hits = 200, 20         # f = 0.1
    rng = np.random.default_rng(4)
    for _ in range(20):
        third_confirms = rng.random() < 0.05            # almost always disputes -> high sigma
        high.observe_third(agree=True, third_confirms=third_confirms)
    assert high.sigma_hat >= high.fallback_sigma
    assert high.fallback is True

    low = _make_rule()
    low.audit_f_n, low.audit_f_hits = 200, 20
    rng = np.random.default_rng(5)
    for _ in range(20):
        third_confirms = rng.random() >= 0.1            # mostly confirms -> low sigma
        low.observe_third(agree=True, third_confirms=third_confirms)
    assert low.sigma_hat < low.fallback_sigma
    assert low.fallback is False


def test_fallback_needs_minimum_evidence_even_if_sigma_looks_high():
    rule = _make_rule()
    # fewer than min_evidence observations: fallback must not fire even though every one disputes
    for _ in range(rule.min_evidence - 1):
        rule.observe_third(agree=True, third_confirms=False)
    assert rule.fallback is False


def test_v5_1_runs_reproducibly_and_is_a_no_op_when_disabled():
    """With third_source_frac = audit_frac = 0 (the defaults), v5.1 must spend nothing extra and never falls
    back, so it should behave exactly like plain Rule_v5_s on the same scenario and seed."""
    s = Setting().with_(q_true=0.8, q_assumed=0.5, fa_assumed=0.0, check_frac=0.15, leak_mult=1.0,
                        false_alarm=0.05, fa_persistence=0.0)
    a = run("Rule_v5_1", dict(SESSION), s, "drop_0.75", 1601)
    b = run("Rule_v5_1", dict(SESSION), s, "drop_0.75", 1601)
    assert a["total_loss_fail"] == b["total_loss_fail"]                 # reproducible
    assert a["third_checks_per_task"] == 0.0 and a["audits_per_task"] == 0.0
    assert a["sigma_hat"] == 0.0 and a["fallback_share"] == 0.0
    c = run("Rule_v5_s", dict(SESSION), s, "drop_0.75", 1601)
    assert a["total_loss_fail"] == c["total_loss_fail"]                 # identical decisions when disabled


def test_third_source_and_audit_spend_when_enabled():
    s = Setting().with_(q_true=0.8, q_assumed=0.5, check_frac=0.15, leak_mult=1.0, false_alarm=0.15,
                        fa_persistence=0.8, xc_shared=0.4, third_source_frac=1.0, audit_frac=0.3, n_tasks=300)
    res = run("Rule_v5_1", dict(SESSION), s, "S1_sudden", seed=7)
    assert res["audits_per_task"] > 0.0
    # third-source spend tracks crosschecks_per_task since third_source_frac = 1.0 samples every one of them
    assert res["third_checks_per_task"] == res["crosschecks_per_task"]
