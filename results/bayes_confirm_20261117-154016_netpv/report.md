# Part B: distance to the Bayes-optimal policy (small instance; pre-registered)

Seeds 8240-8259; 6720 runs; 4336 s. Two tools, single-step tasks, no retries; 48 conditions (drop x q x leak x f). Unit: the seed. Metric: total loss per task.

| Strategy | mean loss | regret vs Bayes | leak rate | failed tasks | checks/task |
|---|---|---|---|---|---|
| never | 34.58 | +28.9% | 5.9% | 5.9% | 0.00 |
| always | 28.70 | +7.0% | 0.7% | 15.6% | 1.00 |
| cusum | 28.77 | +7.2% | 2.7% | 3.8% | 0.08 |
| v4 | 27.37 | +2.0% | 1.6% | 6.8% | 0.50 |
| oracle_heur | 27.46 | +2.4% | 1.4% | 12.0% | 0.65 |
| bayes | 26.82 | +0.0% | 1.6% | 6.3% | 0.45 |
| v5 | 28.42 | +5.9% | 2.8% | 3.1% | 0.14 |

## Regret of rule v4 vs Bayes-optimal, by condition (mean loss)

| drop | f | Bayes | v4 | regret | always | never |
|---|---|---|---|---|---|---|
| 95% | 0 | 24.52 | 25.40 | +3.6% | 25.14 | 26.46 |
| 95% | 0.05 | 25.07 | 25.88 | +3.2% | 26.25 | 26.46 |
| 95% | 0.15 | 26.14 | 26.76 | +2.4% | 28.33 | 26.46 |
| 85% | 0 | 26.50 | 26.96 | +1.8% | 26.84 | 32.91 |
| 85% | 0.05 | 27.09 | 27.67 | +2.1% | 27.79 | 32.91 |
| 85% | 0.15 | 28.05 | 28.53 | +1.7% | 29.92 | 32.91 |
| 75% | 0 | 26.83 | 27.27 | +1.6% | 29.30 | 39.96 |
| 75% | 0.05 | 27.33 | 27.84 | +1.9% | 30.10 | 39.96 |
| 75% | 0.15 | 28.24 | 28.58 | +1.2% | 31.31 | 39.96 |
| 60% | 0 | 26.66 | 27.11 | +1.7% | 28.97 | 39.00 |
| 60% | 0.05 | 27.19 | 27.68 | +1.8% | 29.64 | 39.00 |
| 60% | 0.15 | 28.27 | 28.72 | +1.6% | 30.80 | 39.00 |

## Pre-registered hypotheses (PREREGISTRATION_v5.md, part B)
- H-B1 (sanity) Bayes has the lowest mean loss among never, always, cusum, v4: never 34.58, always 28.70, cusum 28.77, v4 27.37 vs Bayes 26.82 -> CONFIRMED
- H-B2 v4 within 5% of Bayes-optimal: regret +2.0% (95% CI +1.5% to +2.5%) -> CONFIRMED
- H-B3 v4 captures >= 80% of the achievable saving over never-check: 93% -> CONFIRMED
- Descriptive: v4 above Bayes on 19 of 20 seeds (p = 1.9e-06). v5 (extra cross-check action): 28.42; here a failed task costs only one call (22), less than a cross-check call (24).