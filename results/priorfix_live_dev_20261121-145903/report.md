# Prior-fix test, live tools (dev), seeds 7010-7014

160 runs; 12 s. Calibrated f (Study M) = 0.046.

| Strategy | total loss | wrong kept | failed | checks/task | median learned f |
|---|---|---|---|---|---|
| never | 91.1 | 45.7% | 3.3% | 0.00 | - |
| cusum | 89.8 | 42.7% | 6.3% | 0.13 | - |
| v4 | 81.1 | 18.2% | 15.3% | 0.87 | - |
| always_x | 80.0 | 24.3% | 3.3% | 1.07 | - |
| v5_told | 80.4 | 22.5% | 3.0% | 0.93 | 0.040 |
| v5 | 81.7 | 26.0% | 3.3% | 0.82 | 0.102 |
| v5_fix | 81.5 | 24.2% | 3.3% | 0.94 | 0.084 |
| fix_B | 78.2 | 13.3% | 0.0% | 0.00 | - |

## Pre-registered hypotheses (PREREGISTRATION_priorfix.md; Holm across H-F3 to H-F5)

- H-F3 the fixed prior lowers the bias of the learned f (vs calibrated 0.046): 0.032 vs 0.053, one-sided Wilcoxon p = 0.031, Holm fail -> **NOT CONFIRMED**
- H-F4 the fixed rule below the rule as evaluated: 81.456 vs 81.742 (-0.3%, 95% CI -0.8% to +0.1%), one-sided Wilcoxon p = 0.16, Holm fail -> **NOT CONFIRMED**
- H-F5 the fixed rule below never checking: 81.456 vs 91.138 (-10.6%, 95% CI -13.3% to -8.5%), one-sided Wilcoxon p = 0.031, Holm fail -> **NOT CONFIRMED**
- Descriptive: v5_fix vs v5_told: 81.5 vs 80.4 (+1.4%, 95% CI -0.4% to +3.2%)
- Descriptive: v5_fix vs v4: 81.5 vs 81.1 (+0.4%, 95% CI -3.8% to +5.0%)
- Descriptive: v5_fix vs always_x: 81.5 vs 80.0 (+1.9%, 95% CI -0.4% to +5.1%)
- Descriptive: v5_fix vs cusum: 81.5 vs 89.8 (-9.3%, 95% CI -11.9% to -7.0%)
- Descriptive: v5_fix vs fix_B: 81.5 vs 78.2 (+4.1%, 95% CI -3.3% to +11.2%)