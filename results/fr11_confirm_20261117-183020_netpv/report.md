# FR11: CostBench with real-checker error rates (confirm)

Seeds 8400-8417; 128 conditions per seed; 20736 runs; 491 s.

## Mean total loss per task, by checker profile

| Strategy | all | qwen2.5:1.5b | qwen2.5:3b | phi4-mini | llama3.1:8b | failed tasks | checks/task |
|---|---|---|---|---|---|---|---|
| never | 113.7 | 113.7 | 113.7 | 113.7 | 113.7 | 0.1% | 0.00 |
| always | 172.4 | 147.2 | 121.9 | 211.4 | 208.9 | 53.3% | 3.30 |
| cusum | 117.9 | 114.0 | 113.1 | 123.2 | 121.5 | 4.3% | 0.26 |
| v2 | 165.5 | 139.0 | 116.8 | 205.4 | 200.9 | 39.5% | 2.41 |
| v4 | 111.4 | 110.8 | 109.4 | 112.7 | 112.6 | 1.0% | 0.11 |
| v4_nocal | 128.2 | 118.9 | 110.5 | 142.3 | 141.0 | 15.0% | 0.94 |
| always_x | 144.1 | 123.5 | 113.2 | 171.4 | 168.2 | 0.1% | 3.01 |
| v5_told | 110.3 | 109.5 | 107.9 | 111.9 | 111.9 | 0.1% | 0.38 |
| v5 | 111.4 | 111.1 | 110.3 | 112.1 | 112.2 | 0.1% | 0.08 |

## By check price

| Strategy | 5% | 15% |
|---|---|---|
| never | 113.7 | 113.7 |
| always | 167.3 | 177.4 |
| cusum | 117.5 | 118.3 |
| v2 | 181.5 | 149.6 |
| v4 | 111.2 | 111.6 |
| v4_nocal | 144.8 | 111.5 |
| always_x | 139.5 | 148.7 |
| v5_told | 109.6 | 110.9 |
| v5 | 111.0 | 111.8 |

## Pre-registered hypotheses

- H-RC1 v5 below v4_nocal: 111.4 vs 128.2 (-13.1%, 95% CI -14.1% to -11.8%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-RC3 v5 below always_x: 111.4 vs 144.1 (-22.7%, 95% CI -24.0% to -21.3%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-RC2 v5 equivalent to v4 told q and f, within +/-3%: 111.4 vs 111.4 (+0.0%, 95% CI -0.3% to +0.3%) -> **CONFIRMED**

## Descriptive: v5 per profile

| Profile | v5 vs never | v5 vs v4 told | median abs error of learned f | of learned q |
|---|---|---|---|---|
| qwen2.5:1.5b | -2.4% | +0.2% | 0.111 | 0.482 |
| qwen2.5:3b | -3.0% | +0.8% | 0.151 | 0.492 |
| phi4-mini | -1.5% | -0.5% | 0.101 | 0.307 |
| llama3.1:8b | -1.4% | -0.4% | 0.086 | 0.259 |