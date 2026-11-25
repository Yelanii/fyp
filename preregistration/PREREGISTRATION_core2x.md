# Pre-registration: published baselines given the cross-check (Core 2x)

Written before any confirmatory seed is run, and committed to the repository before the confirmatory run.

## Why

In Core 2 (re-run with the corrected criterion on seeds 8300 to 8319) the rule beat adaptations of three published methods by 7.6 to 15.9%. Two of them, SSV and GLR-klUCB, check almost every call and resolve a flag by retrying, so they failed 15.8 and 21.9% of tasks when the checker repeats its false alarms. A review asked whether the rule's advantage comes from its decision logic or only from resolving flags by a cross-check instead of a retry. The ablation suggests the second may matter less than it seems (removing the cross-check from the rule cost 0.4%), but that ablation removed it from the rule, not added it to the baselines. This test adds it to the baselines.

This test was designed after the Core 2 and ablation results had been seen.

## Design

**Simulator, conditions and seeds.**
- The simulator and the 64 conditions per seed are exactly those of Core 2 (`ereplan/core2_exp.py`, `_conds()`): four drop levels, two catch rates, two wrong-answer costs, two false-alarm rates and two persistence levels.
- The corrected check criterion is on (`EREPLAN_NETPV=1`), as in every reported result.
- Confirmatory seeds: 9700 to 9719 (20 seeds, not used before).
- Development seeds: 9690 and 9691. These are a pipeline check only and are not used for any decision about the hypotheses.

**Strategies.**
- `v5`: the rule, without labels, unchanged.
- `ssv`, `rdecusum`, `glrklucb`: the three adapted published methods, unchanged, with the parameters tuned for Core 2 (`data/processed/core2_tuned.json`).
- `ssv_x`, `rdecusum_x`, `glrklucb_x`: the same three methods with the same parameters. Each resolves a flag by the rule's cross-check instead of a retry (`ereplan/outside_xcheck.py`).
  - SSV's reject region goes to its strong verifier, which in this adaptation is the cross-check.
  - For RDE-CUSUM and GLR-klUCB, agreement after a flag counts as no failure. Disagreement, or a loud failure of the alternative, counts as a failure.
  - The parameters are not re-tuned. This is a limitation: re-tuning could help the variants further.

**Metric.** Total loss per task, averaged over the 64 conditions for each seed, which gives one value per seed and strategy, as in Core 2.

## Hypotheses

**Superiority.** One-sided Wilcoxon signed-rank test on seed means, with Holm's correction across the three hypotheses at alpha = 0.05.
- **H-X1:** the rule's loss is below that of `ssv_x`.
- **H-X2:** the rule's loss is below that of `rdecusum_x`.
- **H-X3:** the rule's loss is below that of `glrklucb_x`.

**Descriptive only:**
- each baseline with the cross-check against the same baseline without it;
- the rule against the three original baselines on these seeds;
- spend, wrong answers kept, failed tasks, checks and cross-checks per task for every strategy.

## What the outcomes would mean

- **All three confirmed:** the rule's advantage does not come only from resolving flags by a cross-check. Its decisions about when to check and when to switch also matter. The paper then reports the new gaps, which will be smaller than in Core 2 if the cross-check helps the baselines.
- **Some or all not confirmed:** much of the rule's advantage over these baselines comes from the cross-check itself. The paper then says so: once flags are resolved by a second tool, these published methods do about as well as the rule. This supports the paper's main recommendation (resolve flags on a second tool, do not retry) and weakens any claim for the rule's own decision logic against them.

Either outcome is reported in the paper.
