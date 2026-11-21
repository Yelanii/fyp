# Prior-fix test, live tools (confirm), seeds 7300-7319

640 runs; 279 s. Calibrated f (Study M) = 0.046.

| Strategy | total loss | wrong kept | failed | checks/task | median learned f |
|---|---|---|---|---|---|
| never | 73.5 | 32.9% | 3.1% | 0.00 | - |
| cusum | 73.1 | 32.9% | 4.2% | 0.08 | - |
| v4 | 73.7 | 14.4% | 20.7% | 1.30 | - |
| always_x | 71.3 | 18.0% | 4.5% | 1.09 | - |
| v5_told | 72.9 | 24.8% | 4.1% | 0.37 | 0.040 |
| v5 | 74.2 | 26.8% | 4.0% | 0.14 | 0.113 |
| v5_fix | 73.7 | 26.2% | 4.0% | 0.19 | 0.072 |
| fix_B | 79.6 | 8.0% | 6.0% | 0.00 | - |

## Pre-registered hypotheses (PREREGISTRATION_priorfix.md; Holm across H-F3 to H-F5)

- H-F3 the fixed prior lowers the bias of the learned f (vs calibrated 0.046): 0.044 vs 0.087, one-sided Wilcoxon p = 0.00013, Holm ok -> **CONFIRMED**
- H-F4 the fixed rule below the rule as evaluated: 73.739 vs 74.211 (-0.6%, 95% CI -1.2% to -0.1%), one-sided Wilcoxon p = 0.015, Holm ok -> **CONFIRMED**
- H-F5 the fixed rule below never checking: 73.739 vs 73.504 (+0.3%, 95% CI -0.7% to +1.3%), one-sided Wilcoxon p = 0.7, Holm fail -> **NOT CONFIRMED**
- Descriptive: v5_fix vs v5_told: 73.7 vs 72.9 (+1.2%, 95% CI +0.3% to +2.1%)
- Descriptive: v5_fix vs v4: 73.7 vs 73.7 (+0.1%, 95% CI -1.1% to +1.2%)
- Descriptive: v5_fix vs always_x: 73.7 vs 71.3 (+3.4%, 95% CI +2.0% to +4.7%)
- Descriptive: v5_fix vs cusum: 73.7 vs 73.1 (+0.9%, 95% CI -0.2% to +2.0%)
- Descriptive: v5_fix vs fix_B: 73.7 vs 79.6 (-7.3%, 95% CI -8.3% to -6.3%)