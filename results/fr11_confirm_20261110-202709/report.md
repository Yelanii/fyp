# FR11: CostBench with real-checker error rates (confirm)

Seeds 2800-2817; 128 conditions per seed; 20736 runs; 919 s.

## Mean total loss per task, by checker profile

| Strategy | all | qwen2.5:1.5b | qwen2.5:3b | phi4-mini | llama3.1:8b | failed tasks | checks/task |
|---|---|---|---|---|---|---|---|
| never | 113.2 | 113.2 | 113.2 | 113.2 | 113.2 | 0.1% | 0.00 |
| always | 173.6 | 150.2 | 123.2 | 211.5 | 209.5 | 54.1% | 3.29 |
| cusum | 118.4 | 116.3 | 112.9 | 122.7 | 121.7 | 4.8% | 0.28 |
| v2 | 165.6 | 143.2 | 118.7 | 201.9 | 198.5 | 40.3% | 2.41 |
| v4 | 110.9 | 110.6 | 108.9 | 112.2 | 112.1 | 1.1% | 0.12 |
| v4_nocal | 128.1 | 120.5 | 110.7 | 141.1 | 140.2 | 15.3% | 0.95 |
| always_x | 147.2 | 125.2 | 114.3 | 176.2 | 173.1 | 0.1% | 3.03 |
| v5_told | 110.5 | 109.7 | 108.2 | 111.9 | 112.0 | 0.1% | 0.50 |
| v5 | 111.0 | 110.6 | 109.8 | 111.8 | 111.9 | 0.1% | 0.11 |

## By check price

| Strategy | 5% | 15% |
|---|---|---|
| never | 113.2 | 113.2 |
| always | 168.6 | 178.6 |
| cusum | 118.0 | 118.8 |
| v2 | 181.5 | 149.7 |
| v4 | 110.6 | 111.3 |
| v4_nocal | 144.9 | 111.3 |
| always_x | 142.6 | 151.8 |
| v5_told | 109.9 | 111.0 |
| v5 | 110.7 | 111.4 |

## Pre-registered hypotheses

- H-RC1 v5 below v4_nocal: 111.0 vs 128.1 (-13.3%, 95% CI -14.2% to -12.4%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-RC3 v5 below always_x: 111.0 vs 147.2 (-24.6%, 95% CI -25.6% to -23.5%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-RC2 v5 equivalent to v4 told q and f, within +/-3%: 111.0 vs 110.9 (+0.1%, 95% CI -0.2% to +0.4%) -> **CONFIRMED**

## Descriptive: v5 per profile

| Profile | v5 vs never | v5 vs v4 told | median abs error of learned f | of learned q |
|---|---|---|---|---|
| qwen2.5:1.5b | -2.3% | +0.0% | 0.111 | 0.484 |
| qwen2.5:3b | -3.0% | +0.8% | 0.150 | 0.490 |
| phi4-mini | -1.3% | -0.3% | 0.147 | 0.310 |
| llama3.1:8b | -1.2% | -0.2% | 0.137 | 0.262 |