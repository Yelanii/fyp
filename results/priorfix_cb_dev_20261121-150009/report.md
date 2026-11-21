# Prior-fix test, CostBench with real-checker rates (dev), seeds 1990-1991

128 conditions per seed; 1024 runs; 53 s. f grid [0, 0.95].

| Strategy | total loss | checks/task | median learned f - true f, by checker profile |
|---|---|---|---|
| v5 | 113.4 | 0.09 | qwen2.5:1.5b: +0.039; qwen2.5:3b: +0.111; phi4-mini: -0.208; llama3.1:8b: -0.168 |
| v5_fix | 112.7 | 0.18 | qwen2.5:1.5b: -0.021; qwen2.5:3b: +0.019; phi4-mini: -0.343; llama3.1:8b: -0.303 |
| v5_told | 112.0 | 0.42 | qwen2.5:1.5b: -0.004; qwen2.5:3b: +0.009; phi4-mini: -0.002; llama3.1:8b: -0.001 |
| v4 | 113.2 | 0.11 | - |

## Pre-registered hypotheses (PREREGISTRATION_priorfix.md)

- H-F6 the fixed prior lowers the bias of the learned f: 0.087 vs 0.042, one-sided Wilcoxon p = 1 -> **NOT CONFIRMED**
- H-F7 the fixed prior costs at most 1% loss: 112.7 vs 113.4 (-0.57%, 95% CI -0.90% to -0.22%) -> **CONFIRMED**
- Descriptive: v5_fix vs v5_told: 112.7 vs 112.0 (+0.64%, 95% CI +0.57% to +0.70%)
- Descriptive: v5_fix vs v4: 112.7 vs 113.2 (-0.46%, 95% CI -1.11% to +0.24%)