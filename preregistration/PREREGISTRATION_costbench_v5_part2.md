# Pre-registration, part 2: rules v4 and v5 on CostBench when checks are cheap (28 October 2026, before running seeds 2200-2217)

**Why.** In part 1 (PREREGISTRATION_costbench_v5.md) v5 did not beat v4 on CostBench (H-CB1 and H-CB3 not confirmed).
Part 1 stays as reported. Its interpretation was that checks rarely paid at a check price of 15% of a tool call, so
learning the checker had little to improve. Part 2 tests that explanation directly.

**How the condition was chosen (stated honestly).** After part 1, an exploratory run on development seeds 1990-1995
varied the check price (5%, 15%) and the cost of the route around X (native, +20%, +50%, +100%). The detour cost did
not change v5's position; the check price did. At 5%, v5 was 8-10% below v4_nocal on the development seeds; at
15% it was 2-3% above it. Part 2 therefore fixes the check price at 5% and tests on fresh seeds. This is a new,
narrower claim chosen after seeing development data; it does not replace part 1's result.

Why 5% is a realistic price: the real checkers in this project are small local models (Qwen2.5 1.5B/3B), whose
cost per verdict is a small fraction of a paid tool call.

## Design
Identical to part 1 except: check price 5% of the mean tool price; price gap {native, X 20% cheaper} (larger gaps
gave the same routes in development); seeds 2200-2217 (18, never used before). Grid 4 x 2 x 2 x 2 x 2 x 2 = 128
conditions per seed. Same nine strategies, all parameters frozen. Command: `python -m ereplan.costbench_v5 cheap`.

## Hypotheses
- **H-CC1** v5 has lower total loss than v4_nocal (both without labelled calibration). One-sided Wilcoxon over seeds.
- **H-CC2** v5 (no labels) is equivalent to v4 told q and f: the 95% bootstrap CI of the difference lies within +/-3%.
- **H-CC3** v5 has lower total loss than always_x.
Holm correction over H-CC1 and H-CC3 at alpha 0.05.

## What the outcomes would mean
- H-CC1 confirmed: v5's label-free learning pays on CostBench when checks are cheap enough to be used. The claim
  becomes "v5 replaces labelled calibration when checking is cheap", with part 1 as its boundary.
- H-CC1 not confirmed: the development result did not replicate, and v5's advantage is limited to the synthetic study.
- H-CC2 confirmed: without labels, v5 matches the rule that is given labels.

## Outcome (added after the run, 28 October 2026; results/costbench_v5_cheap_20261028-204212)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-CC1 v5 < v4_nocal | 110.7 vs 116.7 (-5.2%, CI -6.1% to -4.2%), p = 3.8e-06, 18 seeds | CONFIRMED |
| H-CC2 v5 equivalent to v4 told, +/-3% | 110.7 vs 111.0 (-0.3%, CI -0.8% to +0.1%) | CONFIRMED |
| H-CC3 v5 < always_x | 110.7 vs 116.4 (-4.9%, CI -6.1% to -3.7%), p = 3.8e-06 | CONFIRMED |

The effect on fresh seeds (-5.2%) is smaller than on the development seeds (-8 to -10%), as expected when a
condition is chosen on development data. Why v4 without labels loses here: it assumes the checker never raises false
alarms, so with cheap checks it checks often (1.73 checks per task) and its repeated false alarms fail 7.1% of tasks.
v5 learns the false-alarm rate (median error 0.041), checks 0.31 times per task and fails 0.1%.
Combined claim with part 1: without any labelled calibration, v5 matches the rule that is given labels on CostBench;
it beats the rule without labels when checks are cheap enough to be used (5%), and ties when they rarely pay (15%).
