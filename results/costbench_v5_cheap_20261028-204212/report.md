# Rules v4 and v5 on CostBench, part 2: cheap checks (5% of a tool call), pre-registered test

Seeds 2200-2217; 128 conditions per seed; 20736 runs; 1377 s.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task |
|---|---|---|---|---|---|
| never | 114.7 | 11.2% | 0.0% | 0.00 | 0.00 |
| always | 124.7 | 1.6% | 13.4% | 3.25 | 0.00 |
| cusum | 114.1 | 8.1% | 1.0% | 0.21 | 0.00 |
| v2 | 127.0 | 1.4% | 12.2% | 3.01 | 0.00 |
| v4 | 111.0 | 8.8% | 0.8% | 0.20 | 0.00 |
| v4_nocal | 116.7 | 4.1% | 7.1% | 1.73 | 0.00 |
| always_x | 116.4 | 2.3% | 0.1% | 3.02 | 0.39 |
| v5_told | 109.4 | 6.0% | 0.1% | 1.06 | 0.13 |
| v5 | 110.7 | 8.3% | 0.1% | 0.31 | 0.05 |

## Pre-registered hypotheses

- H-CC1 v5 below v4_nocal: 110.7 vs 116.7 (-5.2%, 95% CI -6.1% to -4.2%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CC3 v5 below always_x: 110.7 vs 116.4 (-4.9%, 95% CI -6.1% to -3.7%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CC2 v5 (no labels) equivalent to v4 told q and f, within +/-3%: 110.7 vs 111.0 (-0.3%, 95% CI -0.8% to +0.1%) -> **CONFIRMED**
- Descriptive: v5's learned f, median |f_hat - f| = 0.041; v5_told 109.4