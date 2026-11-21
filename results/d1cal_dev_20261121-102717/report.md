# D1-cal: the rule with a labelled calibration prior on live tools (dev), seeds 7010-7014

180 runs; 29 s. Prior from Study M: q 0.450 (n=151), f 0.046 (n=239); v5_cal_small uses one fifth of that weight.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task | median learned f |
|---|---|---|---|---|---|---|
| never | 91.1 | 45.7% | 3.3% | 0.00 | 0.00 | - |
| cusum | 89.8 | 42.7% | 6.3% | 0.13 | 0.00 | - |
| v4 | 81.1 | 18.2% | 15.3% | 0.87 | 0.00 | - |
| always_x | 80.0 | 24.3% | 3.3% | 1.07 | 0.25 | - |
| v5_told | 80.6 | 27.8% | 3.0% | 0.59 | 0.14 | 0.040 |
| v5 | 85.7 | 36.0% | 3.1% | 0.24 | 0.06 | 0.145 |
| v5_cal | 81.4 | 28.9% | 3.0% | 0.57 | 0.14 | 0.045 |
| v5_cal_small | 81.2 | 28.7% | 3.0% | 0.58 | 0.14 | 0.045 |
| fix_B | 78.2 | 13.3% | 0.0% | 0.00 | 0.00 | - |

| B price | wrong-answer cost | never | cusum | v4 | always_x | v5_told | v5 | v5_cal | v5_cal_small | fix_B |
|---|---|---|---|---|---|---|---|---|---|---|
| 45 | 100 | 68.1 | 67.9 | 64.7 | 63.2 | 63.5 | 66.1 | 64.6 | 64.6 | 58.3 |
| 52 | 100 | 68.2 | 68.2 | 68.8 | 65.6 | 68.2 | 68.9 | 68.4 | 68.1 | 65.3 |
| 62 | 200 | 114.0 | 111.3 | 92.2 | 93.4 | 91.8 | 101.6 | 93.9 | 93.2 | 88.7 |
| 74 | 200 | 114.2 | 111.8 | 99.0 | 97.6 | 98.9 | 106.3 | 98.9 | 98.9 | 100.7 |

## Pre-registered hypotheses (PREREGISTRATION_d1cal.md)

- H-C1 the calibrated rule below never checking: 81.4 vs 91.1 (-10.6%, 95% CI -12.4% to -8.9%), one-sided Wilcoxon p = 0.031, Holm fail -> **NOT CONFIRMED**
- H-C2 the calibrated rule below the retrying rule told q and f: 81.4 vs 81.1 (+0.4%, 95% CI -3.4% to +5.3%), one-sided Wilcoxon p = 0.41, Holm fail -> **NOT CONFIRMED**
- Descriptive: calibrated rule vs v5: 81.4 vs 85.7 (-5.0%, 95% CI -7.6% to -3.0%)
- Descriptive: calibrated rule vs v5_told: 81.4 vs 80.6 (+1.1%, 95% CI +0.0% to +3.0%)
- Descriptive: calibrated rule vs always_x: 81.4 vs 80.0 (+1.9%, 95% CI +0.6% to +3.4%)
- Descriptive: calibrated rule vs cusum: 81.4 vs 89.8 (-9.3%, 95% CI -11.1% to -7.3%)
- Descriptive: calibrated rule vs fix_B: 81.4 vs 78.2 (+4.1%, 95% CI -2.9% to +10.8%)
- Descriptive: calibrated rule vs v5_cal_small: 81.4 vs 81.2 (+0.3%, 95% CI +0.1% to +0.5%)
- Descriptive: v5_cal_small vs never: 81.2 vs 91.1 (-10.9%, 95% CI -12.6% to -9.3%)