# Prior-fix test, CostBench with real-checker rates (confirm), seeds 9500-9517

128 conditions per seed; 9216 runs; 700 s. f grid [0, 0.95].

| Strategy | total loss | checks/task | median learned f - true f, by checker profile |
|---|---|---|---|
| v5 | 110.8 | 0.07 | qwen2.5:1.5b: +0.154; qwen2.5:3b: +0.149; phi4-mini: -0.055; llama3.1:8b: -0.039 |
| v5_fix | 110.3 | 0.14 | qwen2.5:1.5b: +0.004; qwen2.5:3b: +0.025; phi4-mini: -0.308; llama3.1:8b: -0.268 |
| v5_told | 109.7 | 0.36 | qwen2.5:1.5b: -0.004; qwen2.5:3b: +0.009; phi4-mini: -0.002; llama3.1:8b: -0.001 |
| v4 | 110.9 | 0.10 | - |

## Pre-registered hypotheses (PREREGISTRATION_priorfix.md)

- H-F6a checkers with low f (Qwen): the fixed prior LOWERS the bias of the learned f: 0.036 vs 0.159, one-sided Wilcoxon p = 3.8e-06 -> **CONFIRMED**
- H-F6b judges with high f (Phi-4 Mini, Llama 3.1 8B): the fixed prior RAISES the bias of the learned f (shrinkage towards the prior mean): 0.301 vs 0.119, one-sided Wilcoxon p = 3.8e-06 -> **CONFIRMED**
- H-F7 the fixed prior costs at most 1% loss: 110.3 vs 110.8 (-0.42%, 95% CI -0.66% to -0.18%) -> **CONFIRMED**
- Descriptive: v5_fix vs v5_told: 110.3 vs 109.7 (+0.58%, 95% CI +0.31% to +0.86%)
- Descriptive: v5_fix vs v4: 110.3 vs 110.9 (-0.52%, 95% CI -0.85% to -0.20%)