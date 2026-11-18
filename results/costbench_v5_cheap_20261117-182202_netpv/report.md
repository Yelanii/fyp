# Rules v4 and v5 on CostBench, part 2: cheap checks (5% of a tool call), pre-registered test

Seeds 8360-8377; 128 conditions per seed; 20736 runs; 557 s.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task |
|---|---|---|---|---|---|
| never | 112.8 | 10.2% | 0.1% | 0.00 | 0.00 |
| always | 124.4 | 1.4% | 13.1% | 3.24 | 0.00 |
| cusum | 113.2 | 7.8% | 1.2% | 0.23 | 0.00 |
| v2 | 126.3 | 1.5% | 12.1% | 3.01 | 0.00 |
| v4 | 110.0 | 8.2% | 0.9% | 0.21 | 0.00 |
| v4_nocal | 115.7 | 3.9% | 7.0% | 1.75 | 0.00 |
| always_x | 115.9 | 2.1% | 0.1% | 3.02 | 0.37 |
| v5_told | 108.2 | 6.2% | 0.1% | 0.86 | 0.10 |
| v5 | 109.9 | 8.2% | 0.1% | 0.21 | 0.03 |

## Pre-registered hypotheses

- H-CC1 v5 below v4_nocal: 109.9 vs 115.7 (-5.0%, 95% CI -6.5% to -3.6%), Wilcoxon p = 7.6e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CC3 v5 below always_x: 109.9 vs 115.9 (-5.1%, 95% CI -6.2% to -4.1%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CC2 v5 (no labels) equivalent to v4 told q and f, within +/-3%: 109.9 vs 110.0 (-0.1%, 95% CI -0.4% to +0.2%) -> **CONFIRMED**
- Descriptive: v5's learned f, median |f_hat - f| = 0.043; v5_told 108.2