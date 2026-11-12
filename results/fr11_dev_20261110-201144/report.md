# FR11: CostBench with real-checker error rates (dev)

Seeds 1990-1991; 128 conditions per seed; 2304 runs; 55 s.

## Mean total loss per task, by checker profile

| Strategy | all | qwen2.5:1.5b | qwen2.5:3b | phi4-mini | llama3.1:8b | failed tasks | checks/task |
|---|---|---|---|---|---|---|---|
| never | 115.9 | 115.9 | 115.9 | 115.9 | 115.9 | 0.1% | 0.00 |
| always | 170.3 | 141.8 | 117.9 | 211.7 | 210.0 | 51.8% | 3.25 |
| cusum | 117.5 | 116.4 | 114.9 | 119.8 | 119.0 | 3.9% | 0.26 |
| v2 | 164.8 | 136.8 | 115.0 | 205.2 | 202.2 | 37.9% | 2.38 |
| v4 | 113.2 | 112.6 | 111.4 | 114.5 | 114.5 | 1.0% | 0.11 |
| v4_nocal | 128.5 | 118.6 | 110.3 | 143.1 | 141.9 | 14.6% | 0.95 |
| always_x | 144.6 | 125.1 | 113.6 | 171.8 | 168.1 | 0.1% | 2.99 |
| v5_told | 111.9 | 111.8 | 108.9 | 113.4 | 113.5 | 0.1% | 0.52 |
| v5 | 113.3 | 111.8 | 110.7 | 115.3 | 115.3 | 0.1% | 0.13 |

## By check price

| Strategy | 5% | 15% |
|---|---|---|
| never | 115.9 | 115.9 |
| always | 165.3 | 175.3 |
| cusum | 117.1 | 117.9 |
| v2 | 180.6 | 149.0 |
| v4 | 112.9 | 113.5 |
| v4_nocal | 144.4 | 112.6 |
| always_x | 140.0 | 149.3 |
| v5_told | 110.8 | 113.0 |
| v5 | 113.0 | 113.5 |

## Pre-registered hypotheses

- H-RC1 v5 below v4_nocal: 113.3 vs 128.5 (-11.8%, 95% CI -14.6% to -9.1%), Wilcoxon p = 0.25 over 2 seeds, Holm fail -> **NOT CONFIRMED**
- H-RC3 v5 below always_x: 113.3 vs 144.6 (-21.7%, 95% CI -23.8% to -19.6%), Wilcoxon p = 0.25 over 2 seeds, Holm fail -> **NOT CONFIRMED**
- H-RC2 v5 equivalent to v4 told q and f, within +/-3%: 113.3 vs 113.2 (+0.0%, 95% CI -0.1% to +0.2%) -> **CONFIRMED**

## Descriptive: v5 per profile

| Profile | v5 vs never | v5 vs v4 told | median abs error of learned f | of learned q |
|---|---|---|---|---|
| qwen2.5:1.5b | -3.5% | -0.7% | 0.047 | 0.471 |
| qwen2.5:3b | -4.5% | -0.6% | 0.090 | 0.441 |
| phi4-mini | -0.6% | +0.7% | 0.205 | 0.324 |
| llama3.1:8b | -0.5% | +0.7% | 0.165 | 0.277 |