# Rules v4 and v5 on CostBench: pre-registered test

CostBench tasks and prices (data/processed/costbench_routes.json); seeds 2000-2017; 128 conditions per seed; 20736 runs; 626 s.
Unit of analysis: the seed (mean over the conditions). Metric: total loss per task = spend + leak loss x leaks + route cost x failed tasks.

## Mean outcomes per strategy

| Strategy | total loss | spend | wrong answers kept | failed tasks | checks/task | cross-checks/task | false alarms resolved/task |
|---|---|---|---|---|---|---|---|
| never | 113.1 | 94.8 | 10.1% | 0.1% | 0.00 | 0.00 | 0.00 |
| always | 133.7 | 120.2 | 1.0% | 12.9% | 3.25 | 0.00 | 0.00 |
| cusum | 113.8 | 98.8 | 7.7% | 1.0% | 0.22 | 0.00 | 0.00 |
| v2 | 120.6 | 109.5 | 4.2% | 6.6% | 1.61 | 0.00 | 0.00 |
| v4 | 110.9 | 95.7 | 8.5% | 0.5% | 0.12 | 0.00 | 0.00 |
| v4_nocal | 110.3 | 96.7 | 7.5% | 1.0% | 0.23 | 0.00 | 0.00 |
| always_x | 124.7 | 121.7 | 1.6% | 0.1% | 3.02 | 0.38 | 0.27 |
| v5_told | 110.0 | 97.7 | 7.2% | 0.1% | 0.35 | 0.05 | 0.02 |
| v5 | 111.0 | 96.0 | 8.6% | 0.1% | 0.10 | 0.01 | 0.01 |

## Mean total loss by condition

| Strategy | leak 1 | leak 3 | pi 0 | pi 1 | f 0.05 | f 0.15 | native prices | X 20% cheaper |
|---|---|---|---|---|---|---|---|---|
| never | 104.0 | 122.3 | 113.1 | 113.1 | 113.1 | 113.1 | 119.6 | 106.7 |
| always | 132.8 | 134.6 | 125.1 | 142.4 | 123.2 | 144.3 | 143.7 | 123.7 |
| cusum | 106.8 | 120.9 | 113.1 | 114.6 | 113.3 | 114.3 | 121.5 | 106.1 |
| v2 | 104.0 | 137.2 | 115.1 | 126.1 | 114.3 | 126.9 | 127.8 | 113.4 |
| v4 | 103.8 | 118.0 | 110.9 | 111.0 | 110.4 | 111.5 | 118.7 | 103.2 |
| v4_nocal | 103.8 | 116.8 | 109.9 | 110.7 | 109.8 | 110.8 | 117.4 | 103.2 |
| always_x | 123.2 | 126.2 | 124.6 | 124.8 | 118.9 | 130.5 | 133.2 | 116.2 |
| v5_told | 103.8 | 116.2 | 110.0 | 110.0 | 109.6 | 110.4 | 117.6 | 102.4 |
| v5 | 104.0 | 117.9 | 110.9 | 111.0 | 110.8 | 111.1 | 118.5 | 103.4 |

## Mean total loss by degradation of X

| Strategy | X at 95% | X at 85% | X at 75% | X at 60% |
|---|---|---|---|---|
| never | 107.8 | 111.1 | 114.2 | 119.4 |
| always | 132.8 | 133.2 | 133.8 | 135.1 |
| cusum | 109.8 | 113.2 | 115.3 | 117.0 |
| v2 | 118.5 | 119.9 | 121.3 | 122.7 |
| v4 | 107.0 | 109.6 | 111.9 | 115.2 |
| v4_nocal | 107.7 | 109.4 | 111.3 | 112.9 |
| always_x | 123.5 | 124.1 | 125.0 | 126.2 |
| v5_told | 107.2 | 109.3 | 110.7 | 112.7 |
| v5 | 107.1 | 109.9 | 112.0 | 114.9 |

## Pre-registered hypotheses (PREREGISTRATION_costbench_v5.md)

- H-CB1 v5 below v4_nocal: 111.0 vs 110.3 (+0.6%, 95% CI -0.1% to +1.3%), Wilcoxon p = 0.96 over 18 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB2 v5 below always_x: 111.0 vs 124.7 (-11.0%, 95% CI -12.0% to -10.0%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CB3 v5 below v4: 111.0 vs 110.9 (+0.0%, 95% CI -0.3% to +0.3%), Wilcoxon p = 0.75 over 18 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB4 v4 below v2: 110.9 vs 120.6 (-8.0%, 95% CI -8.9% to -7.1%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CB5 v5 (no labels) within 3% of v5_told: 111.0 vs 110.0 (+0.9%, 95% CI upper +1.3%) -> **CONFIRMED**
- Descriptive: v5's learned f, median |f_hat - f| = 0.055; learned q, median |q_hat - q| = 0.315
- Descriptive, native CostBench prices only: v5 118.5, v4 118.7, v4_nocal 117.4, always_x 133.2, v2 127.8