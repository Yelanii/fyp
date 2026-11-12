# Rules v4 and v5 on CostBench: development smoke test (not a test of the hypotheses)

CostBench tasks and prices (data/processed/costbench_routes.json); seeds 1990-1991; 128 conditions per seed; 2304 runs; 64 s.
Unit of analysis: the seed (mean over the conditions). Metric: total loss per task = spend + leak loss x leaks + route cost x failed tasks.

## Mean outcomes per strategy

| Strategy | total loss | spend | wrong answers kept | failed tasks | checks/task | cross-checks/task | false alarms resolved/task |
|---|---|---|---|---|---|---|---|
| never | 115.9 | 94.0 | 12.2% | 0.1% | 0.00 | 0.00 | 0.00 |
| always | 132.1 | 118.0 | 1.8% | 12.1% | 3.21 | 0.00 | 0.00 |
| cusum | 115.8 | 98.6 | 9.0% | 0.8% | 0.22 | 0.00 | 0.00 |
| v2 | 120.7 | 108.7 | 5.0% | 6.6% | 1.66 | 0.00 | 0.00 |
| v4 | 112.9 | 94.7 | 10.4% | 0.8% | 0.15 | 0.00 | 0.00 |
| v4_nocal | 111.7 | 96.3 | 8.7% | 1.5% | 0.31 | 0.00 | 0.00 |
| always_x | 125.9 | 120.9 | 2.7% | 0.1% | 2.98 | 0.38 | 0.25 |
| v5_told | 112.8 | 97.4 | 9.0% | 0.1% | 0.44 | 0.06 | 0.03 |
| v5 | 113.0 | 95.1 | 10.7% | 0.1% | 0.10 | 0.02 | 0.01 |

## Mean total loss by condition

| Strategy | leak 1 | leak 3 | pi 0 | pi 1 | f 0.05 | f 0.15 | native prices | X 20% cheaper |
|---|---|---|---|---|---|---|---|---|
| never | 105.0 | 126.8 | 115.9 | 115.9 | 115.9 | 115.9 | 121.3 | 110.5 |
| always | 130.4 | 133.7 | 125.6 | 138.6 | 121.8 | 142.4 | 142.5 | 121.7 |
| cusum | 107.6 | 124.0 | 115.3 | 116.2 | 115.6 | 115.9 | 123.1 | 108.5 |
| v2 | 104.5 | 136.9 | 116.1 | 125.3 | 114.4 | 127.0 | 127.6 | 113.8 |
| v4 | 105.1 | 120.7 | 112.8 | 113.0 | 112.5 | 113.3 | 120.0 | 105.8 |
| v4_nocal | 105.1 | 118.2 | 111.4 | 111.9 | 111.6 | 111.7 | 117.5 | 105.9 |
| always_x | 123.4 | 128.4 | 125.7 | 126.1 | 119.4 | 132.4 | 134.0 | 117.8 |
| v5_told | 104.7 | 120.8 | 112.8 | 112.8 | 112.4 | 113.1 | 119.6 | 106.0 |
| v5 | 105.3 | 120.8 | 113.1 | 113.0 | 112.9 | 113.2 | 119.4 | 106.7 |

## Mean total loss by degradation of X

| Strategy | X at 95% | X at 85% | X at 75% | X at 60% |
|---|---|---|---|---|
| never | 112.1 | 115.9 | 116.4 | 119.3 |
| always | 131.3 | 131.8 | 132.2 | 132.9 |
| cusum | 113.6 | 115.9 | 117.7 | 115.9 |
| v2 | 119.5 | 120.5 | 121.0 | 121.8 |
| v4 | 110.7 | 112.8 | 112.9 | 115.2 |
| v4_nocal | 110.3 | 111.1 | 112.2 | 113.1 |
| always_x | 125.3 | 125.5 | 125.9 | 126.9 |
| v5_told | 111.6 | 112.9 | 112.7 | 113.9 |
| v5 | 111.0 | 112.5 | 113.2 | 115.4 |

## Pre-registered hypotheses (PREREGISTRATION_costbench_v5.md)

- H-CB1 v5 below v4_nocal: 113.0 vs 111.7 (+1.2%, 95% CI +0.9% to +1.5%), Wilcoxon p = 1 over 2 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB2 v5 below always_x: 113.0 vs 125.9 (-10.2%, 95% CI -11.8% to -8.7%), Wilcoxon p = 0.25 over 2 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB3 v5 below v4: 113.0 vs 112.9 (+0.1%, 95% CI -0.3% to +0.6%), Wilcoxon p = 0.75 over 2 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB4 v4 below v2: 112.9 vs 120.7 (-6.5%, 95% CI -8.8% to -4.2%), Wilcoxon p = 0.25 over 2 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB5 v5 (no labels) within 3% of v5_told: 113.0 vs 112.8 (+0.2%, 95% CI upper +0.4%) -> **CONFIRMED**
- Descriptive: v5's learned f, median |f_hat - f| = 0.068; learned q, median |q_hat - q| = 0.322
- Descriptive, native CostBench prices only: v5 119.4, v4 120.0, v4_nocal 117.5, always_x 134.0, v2 127.6