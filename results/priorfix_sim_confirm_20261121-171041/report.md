# Prior-fix test, simulator (confirm), seeds 9400-9419

5120 runs; 5919 s. 64 conditions per seed (label-free-rule grid).

| Strategy | total loss | checks/task | wrong kept | median learned f - true f | median abs error of f |
|---|---|---|---|---|---|
| v5 | 146.7 | 0.64 | 12.7% | +0.017 | 0.029 |
| v5_fix | 146.7 | 0.77 | 12.3% | +0.001 | 0.021 |
| v5_told | 146.8 | 1.84 | 9.9% | +0.000 | 0.010 |
| v4 | 147.4 | 0.47 | 12.7% | - | - |

## Pre-registered hypotheses (PREREGISTRATION_priorfix.md)

- H-F1 the fixed prior lowers the bias of the learned f (|median of learned f - true f| per seed): 0.010 vs 0.022, one-sided Wilcoxon p = 0.00084 -> **CONFIRMED**
- H-F2 the fixed prior costs at most 1% loss: 146.7 vs 146.7 (-0.04%, 95% CI -0.32% to +0.23%) -> **CONFIRMED**
- Descriptive: v5_fix vs v5_told: 146.7 vs 146.8 (-0.05%, 95% CI -0.59% to +0.48%)
- Descriptive: v5_fix vs v4: 146.7 vs 147.4 (-0.48%, 95% CI -0.90% to -0.09%)