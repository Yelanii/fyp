# Pre-registration: what the decision-value asymmetry costs

**Written:** 19 November 2026, before the confirmatory run. The confirmatory run is done once, on the author's laptop.

## Why
A review of paper draft v0.7.1 (19 Nov 2026, methodological soundness 6.5/10) said:

> "Appendix B explicitly acknowledges an asymmetry in the decision-value calculation: the staying cost counts tool
> price per success, whereas the alternative-tool cost includes the wrong-answer penalty. ... Its impact should be
> quantified, and the formulation should be corrected or rigorously justified."

In the evaluated rule (`Rule_v5_x` with `EREPLAN_NETPV=1`), the decision value DV compares
- the cost of staying, `u c / m` (price per success only), with
- the cost of switching, `R_alt + c_switch`, where `R_alt = min_j u (c_j/p_j + (1 - p_j)(1 - rho) L)` includes the
  wrong answers the alternative lets through.

The switch line itself uses `c/p + (1 - p)(1 - rho) L` on both sides. The symmetric variant `Rule_v5_sym` uses the
same per-call cost on the staying side of DV too. Nothing else changes: same random stream (`rng_name = "Rule_v5_x"`),
same estimates, same check test apart from DV.

## Design
- **Driver:** `python run_dvsym.py confirm` (sets `EREPLAN_NETPV=1` itself).
- **Testbed and grid:** the simulator grid of the label-free-rule experiment (`ereplan/v5_exp.py`): tool A drops to
  95, 85, 75 or 60%; q in {0.8, 0.95}; wrong-answer cost 1x or 3x a task; f in {0.05, 0.15}; pi in {0, 1}.
  64 conditions per seed.
- **Strategies:** never check; the retrying rule told q and f; the rule as evaluated; the rule with symmetric DV.
- **Seeds:** 9100-9119, run once. Development used seeds 8000-8003 on the cloud machine (pipeline check only).
- **Unit:** the seed (loss averaged over its 64 conditions).

## Hypotheses
- **H-D1 (primary).** The asymmetry costs at most 1%: the paired 95% bootstrap CI of the percentage difference in
  loss (symmetric vs evaluated) lies within -1% to +1%.
- **H-D2 (descriptive).** Two-sided Wilcoxon signed-rank test over the 20 seeds, symmetric vs evaluated.
- **H-D3.** The evaluated rule is within +3% of the retrying rule told q and f (upper CI bound <= +3%), on fresh
  seeds.
- **Reported regardless of outcome:** loss by wrong-answer cost and degradation level; wrong answers kept; failed
  tasks; checks per task; the share of runs in which both rules give exactly the same loss.

## What the outcomes would mean
- **H-D1 confirmed:** the asymmetry does not matter at the 1% level; the paper keeps the evaluated rule, reports the
  measured difference, and states the symmetric form as the recommended specification.
- **H-D1 not confirmed, symmetric cheaper:** the asymmetry costs more than 1%; the paper reports it, and the
  symmetric form is recommended. Earlier results are not re-run with it before submission, and this is stated.
- **H-D1 not confirmed, symmetric more expensive:** the asymmetry happens to help in this grid; reported as found.

## Known limits
- Simulator only. DV is non-zero only when the credible range of the current tool straddles the switch line, so
  the difference can only appear in those calls.
