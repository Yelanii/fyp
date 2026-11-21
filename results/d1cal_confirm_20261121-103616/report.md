# D1-cal: the rule with a labelled calibration prior on live tools (confirm), seeds 7200-7219

720 runs; 463 s. Prior from Study M: q 0.450 (n=151), f 0.046 (n=239); v5_cal_small uses one fifth of that weight.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task | median learned f |
|---|---|---|---|---|---|---|
| never | 72.8 | 32.5% | 3.1% | 0.00 | 0.00 | - |
| cusum | 72.5 | 32.6% | 4.0% | 0.08 | 0.00 | - |
| v4 | 73.1 | 13.9% | 20.7% | 1.28 | 0.00 | - |
| always_x | 71.0 | 18.1% | 4.4% | 1.09 | 0.24 | - |
| v5_told | 72.1 | 24.4% | 3.9% | 0.42 | 0.09 | 0.040 |
| v5 | 73.6 | 26.1% | 3.7% | 0.10 | 0.02 | 0.130 |
| v5_cal | 72.3 | 24.2% | 4.0% | 0.40 | 0.08 | 0.045 |
| v5_cal_small | 72.0 | 24.9% | 3.9% | 0.37 | 0.08 | 0.049 |
| fix_B | 79.6 | 8.0% | 6.0% | 0.00 | 0.00 | - |

| B price | wrong-answer cost | never | cusum | v4 | always_x | v5_told | v5 | v5_cal | v5_cal_small | fix_B |
|---|---|---|---|---|---|---|---|---|---|---|
| 45 | 100 | 55.9 | 55.8 | 60.6 | 57.4 | 57.2 | 56.9 | 57.5 | 57.4 | 60.3 |
| 52 | 100 | 56.5 | 56.0 | 63.5 | 59.8 | 59.3 | 59.3 | 59.4 | 58.6 | 68.4 |
| 62 | 200 | 89.2 | 88.8 | 81.9 | 81.3 | 84.7 | 87.8 | 84.6 | 84.7 | 87.9 |
| 74 | 200 | 89.4 | 89.2 | 86.4 | 85.4 | 87.1 | 90.4 | 87.5 | 87.4 | 101.7 |

## Pre-registered hypotheses (PREREGISTRATION_d1cal.md)

- H-C1 the calibrated rule below never checking: 72.3 vs 72.8 (-0.7%, 95% CI -1.8% to +0.6%), one-sided Wilcoxon p = 0.16, Holm fail -> **NOT CONFIRMED**
- H-C2 the calibrated rule below the retrying rule told q and f: 72.3 vs 73.1 (-1.2%, 95% CI -2.2% to -0.2%), one-sided Wilcoxon p = 0.038, Holm fail -> **NOT CONFIRMED**
- Descriptive: calibrated rule vs v5: 72.3 vs 73.6 (-1.8%, 95% CI -2.9% to -0.8%)
- Descriptive: calibrated rule vs v5_told: 72.3 vs 72.1 (+0.2%, 95% CI +0.0% to +0.5%)
- Descriptive: calibrated rule vs always_x: 72.3 vs 71.0 (+1.8%, 95% CI +0.9% to +2.8%)
- Descriptive: calibrated rule vs cusum: 72.3 vs 72.5 (-0.3%, 95% CI -1.4% to +0.9%)
- Descriptive: calibrated rule vs fix_B: 72.3 vs 79.6 (-9.2%, 95% CI -10.6% to -7.9%)
- Descriptive: calibrated rule vs v5_cal_small: 72.3 vs 72.0 (+0.3%, 95% CI -0.2% to +0.8%)
- Descriptive: v5_cal_small vs never: 72.0 vs 72.8 (-1.0%, 95% CI -2.1% to +0.3%)