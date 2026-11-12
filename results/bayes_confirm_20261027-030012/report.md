# Part B: distance to the Bayes-optimal policy (small instance; pre-registered)

Seeds 1820-1839; 6720 runs; 1053 s. Two tools, single-step tasks, no retries; 48 conditions (drop x q x leak x f). Unit: the seed. Metric: total loss per task.

| Strategy | mean loss | regret vs Bayes | leak rate | failed tasks | checks/task |
|---|---|---|---|---|---|
| never | 34.10 | +26.7% | 5.7% | 5.8% | 0.00 |
| always | 28.62 | +6.4% | 0.6% | 15.0% | 1.00 |
| cusum | 28.82 | +7.1% | 2.7% | 3.9% | 0.08 |
| v4 | 27.49 | +2.2% | 1.5% | 7.2% | 0.52 |
| oracle_heur | 27.51 | +2.2% | 1.4% | 12.0% | 0.65 |
| bayes | 26.91 | +0.0% | 1.6% | 6.4% | 0.45 |
| v5 | 28.40 | +5.6% | 2.6% | 3.2% | 0.19 |

## Regret of rule v4 vs Bayes-optimal, by condition (mean loss)

| drop | f | Bayes | v4 | regret | always | never |
|---|---|---|---|---|---|---|
| 95% | 0 | 24.46 | 25.39 | +3.8% | 25.15 | 26.17 |
| 95% | 0.05 | 24.96 | 25.93 | +3.9% | 26.14 | 26.17 |
| 95% | 0.15 | 25.95 | 26.45 | +1.9% | 28.21 | 26.17 |
| 85% | 0 | 26.66 | 27.32 | +2.5% | 26.95 | 32.53 |
| 85% | 0.05 | 27.33 | 27.96 | +2.3% | 27.96 | 32.53 |
| 85% | 0.15 | 28.28 | 28.96 | +2.4% | 30.22 | 32.53 |
| 75% | 0 | 26.98 | 27.38 | +1.5% | 29.32 | 40.25 |
| 75% | 0.05 | 27.53 | 27.99 | +1.7% | 29.94 | 40.25 |
| 75% | 0.15 | 28.58 | 28.92 | +1.2% | 31.55 | 40.25 |
| 60% | 0 | 26.69 | 27.10 | +1.5% | 28.16 | 37.44 |
| 60% | 0.05 | 27.21 | 27.72 | +1.9% | 29.02 | 37.44 |
| 60% | 0.15 | 28.28 | 28.79 | +1.8% | 30.87 | 37.44 |

## Pre-registered hypotheses (PREREGISTRATION_v5.md, part B)
- H-B1 (sanity) Bayes has the lowest mean loss among never, always, cusum, v4: never 34.10, always 28.62, cusum 28.82, v4 27.49 vs Bayes 26.91 -> CONFIRMED
- H-B2 v4 within 5% of Bayes-optimal: regret +2.2% (95% CI +1.7% to +2.7%) -> CONFIRMED
- H-B3 v4 captures >= 80% of the achievable saving over never-check: 92% -> CONFIRMED
- Descriptive: v4 above Bayes on 20 of 20 seeds (p = 9.5e-07). v5 (extra cross-check action): 28.40; here a failed task costs only one call (22), less than a cross-check call (24).