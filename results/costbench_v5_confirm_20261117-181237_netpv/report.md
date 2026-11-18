# Rules v4 and v5 on CostBench: pre-registered test

CostBench tasks and prices (data/processed/costbench_routes.json); seeds 8340-8357; 128 conditions per seed; 20736 runs; 2379 s.
Unit of analysis: the seed (mean over the conditions). Metric: total loss per task = spend + leak loss x leaks + route cost x failed tasks.

## Mean outcomes per strategy

| Strategy | total loss | spend | wrong answers kept | failed tasks | checks/task | cross-checks/task | false alarms resolved/task |
|---|---|---|---|---|---|---|---|
| never | 114.3 | 94.7 | 10.8% | 0.1% | 0.00 | 0.00 | 0.00 |
| always | 134.9 | 120.2 | 1.4% | 13.2% | 3.27 | 0.00 | 0.00 |
| cusum | 114.8 | 99.3 | 7.8% | 1.1% | 0.24 | 0.00 | 0.00 |
| v2 | 121.0 | 109.6 | 4.3% | 6.8% | 1.64 | 0.00 | 0.00 |
| v4 | 111.4 | 95.6 | 8.9% | 0.6% | 0.13 | 0.00 | 0.00 |
| v4_nocal | 110.2 | 96.9 | 7.6% | 1.0% | 0.25 | 0.00 | 0.00 |
| always_x | 124.9 | 121.4 | 1.9% | 0.1% | 3.02 | 0.38 | 0.27 |
| v5_told | 110.5 | 97.1 | 8.0% | 0.1% | 0.28 | 0.04 | 0.02 |
| v5 | 111.7 | 95.7 | 9.3% | 0.1% | 0.08 | 0.02 | 0.01 |

## Mean total loss by condition

| Strategy | leak 1 | leak 3 | pi 0 | pi 1 | f 0.05 | f 0.15 | native prices | X 20% cheaper |
|---|---|---|---|---|---|---|---|---|
| never | 104.5 | 124.0 | 114.3 | 114.3 | 114.3 | 114.3 | 120.0 | 108.6 |
| always | 133.6 | 136.2 | 126.3 | 143.4 | 123.7 | 146.1 | 144.7 | 125.0 |
| cusum | 107.5 | 122.0 | 114.5 | 115.1 | 114.0 | 115.5 | 122.1 | 107.5 |
| v2 | 104.2 | 137.8 | 115.7 | 126.3 | 114.3 | 127.8 | 127.6 | 114.4 |
| v4 | 104.3 | 118.5 | 111.3 | 111.5 | 110.7 | 112.0 | 118.2 | 104.5 |
| v4_nocal | 104.2 | 116.2 | 109.8 | 110.6 | 110.0 | 110.3 | 116.5 | 103.9 |
| always_x | 123.2 | 126.6 | 124.9 | 125.0 | 118.9 | 130.9 | 133.4 | 116.5 |
| v5_told | 104.1 | 116.8 | 110.5 | 110.5 | 110.0 | 110.9 | 117.5 | 103.5 |
| v5 | 104.4 | 119.0 | 111.7 | 111.7 | 111.5 | 111.9 | 118.3 | 105.1 |

## Mean total loss by degradation of X

| Strategy | X at 95% | X at 85% | X at 75% | X at 60% |
|---|---|---|---|---|
| never | 108.8 | 112.4 | 115.3 | 120.8 |
| always | 133.6 | 134.4 | 135.0 | 136.5 |
| cusum | 111.3 | 115.4 | 115.5 | 116.8 |
| v2 | 118.9 | 120.7 | 121.6 | 122.9 |
| v4 | 107.5 | 110.7 | 112.4 | 114.9 |
| v4_nocal | 107.7 | 109.8 | 110.9 | 112.2 |
| always_x | 123.7 | 124.6 | 125.1 | 126.3 |
| v5_told | 107.6 | 110.0 | 111.5 | 112.7 |
| v5 | 107.5 | 111.0 | 113.3 | 115.1 |

## Pre-registered hypotheses (PREREGISTRATION_costbench_v5.md)

- H-CB1 v5 below v4_nocal: 111.7 vs 110.2 (+1.4%, 95% CI +0.6% to +2.2%), Wilcoxon p = 1 over 18 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB2 v5 below always_x: 111.7 vs 124.9 (-10.6%, 95% CI -11.5% to -9.7%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CB3 v5 below v4: 111.7 vs 111.4 (+0.3%, 95% CI +0.0% to +0.5%), Wilcoxon p = 0.98 over 18 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB4 v4 below v2: 111.4 vs 121.0 (-8.0%, 95% CI -8.9% to -7.0%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CB5 v5 (no labels) within 3% of v5_told: 111.7 vs 110.5 (+1.1%, 95% CI upper +1.6%) -> **CONFIRMED**
- Descriptive: v5's learned f, median |f_hat - f| = 0.076; learned q, median |q_hat - q| = 0.315
- Descriptive, native CostBench prices only: v5 118.3, v4 118.2, v4_nocal 116.5, always_x 133.4, v2 127.6