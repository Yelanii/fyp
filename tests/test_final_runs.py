"""Tests for the 10 Nov 2026 confirmatory drivers: FR11 (CostBench with real-checker rates) and the FreshQA test."""
import os
os.environ.setdefault("EREPLAN_FMAX", "0.95")
import run_fr11
import run_freshqa_confirm as fq


def test_fr11_profiles_are_the_measured_rates_and_valid():
    assert set(run_fr11.PROFILES) == {"qwen2.5:1.5b", "qwen2.5:3b", "phi4-mini", "llama3.1:8b"}
    for q, f, pi in run_fr11.PROFILES.values():
        assert 0 < f < q < 1 and pi == 1.0


def test_fr11_job_is_reproducible_and_runs_all_nine_strategies():
    a = run_fr11.job(("phi4-mini", 0.75, 3.0, 0.0, 0.05, 1990))
    b = run_fr11.job(("phi4-mini", 0.75, 3.0, 0.0, 0.05, 1990))
    assert len(a) == 9 and [r["loss"] for r in a] == [r["loss"] for r in b]
    assert all(r["profile"] == "phi4-mini" and r["f"] == 0.556 for r in a)


def test_freshqa_job_is_reproducible_and_use_B_never_keeps_a_stale_answer():
    k = ("use_B", "phi4-mini@plain", "fqr_news", 100, 24.0, 2500)
    a, b = fq.job(k), fq.job(k)
    assert a["loss"] == b["loss"] and a["leak_rate"] == 0.0 and a["checks"] == 0.0


def test_freshqa_dearer_tool_B_costs_use_B_more_and_confirm_seeds_are_fresh():
    lo = fq.job(("use_B", "phi4-mini@plain", "fqr_mixed", 50, 24.0, 2501))["loss"]
    hi = fq.job(("use_B", "phi4-mini@plain", "fqr_mixed", 50, 30.0, 2501))["loss"]
    assert hi > lo
    assert not set(fq.SEEDS["confirm"]) & set(range(2500, 2530))      # every seed touched in FreshQA exploration
    assert fq.PROPOSED == "rho_cap"
