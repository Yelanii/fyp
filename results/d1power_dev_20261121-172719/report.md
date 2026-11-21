# D1-power: live tools, high-power replication (dev), seeds 7010-7014

200 runs; 14 s; 5 seeds x 4 conditions. Cached answers; no model called.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task | median learned f |
|---|---|---|---|---|---|---|
| never | 91.14 | 45.7% | 3.3% | 0.00 | 0.00 | - |
| always | 88.33 | 15.5% | 22.9% | 1.46 | 0.00 | - |
| cusum | 89.77 | 42.7% | 6.3% | 0.13 | 0.00 | - |
| v4 | 81.14 | 18.2% | 15.3% | 0.87 | 0.00 | - |
| always_x | 79.96 | 24.3% | 3.3% | 1.07 | 0.25 | - |
| v5_told | 80.60 | 27.8% | 3.0% | 0.59 | 0.14 | 0.040 |
| v5 | 85.72 | 36.0% | 3.1% | 0.24 | 0.06 | 0.145 |
| v5_fix | 83.00 | 31.3% | 3.3% | 0.47 | 0.12 | 0.076 |
| v5_cal | 81.44 | 28.9% | 3.0% | 0.57 | 0.14 | 0.045 |
| fix_B | 78.25 | 13.3% | 0.0% | 0.00 | 0.00 | - |

| B price | wrong-answer cost | never | always | cusum | v4 | always_x | v5_told | v5 | v5_fix | v5_cal | fix_B |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 45 | 100 | 68.1 | 72.3 | 67.9 | 64.7 | 63.2 | 63.5 | 66.1 | 64.3 | 64.6 | 58.3 |
| 52 | 100 | 68.2 | 78.1 | 68.2 | 68.8 | 65.6 | 68.2 | 68.9 | 67.7 | 68.4 | 65.3 |
| 62 | 200 | 114.0 | 98.2 | 111.3 | 92.2 | 93.4 | 91.8 | 101.6 | 94.6 | 93.9 | 88.7 |
| 74 | 200 | 114.2 | 104.8 | 111.8 | 99.0 | 97.6 | 98.9 | 106.3 | 105.4 | 98.9 | 100.7 |

## Pre-registered hypotheses (PREREGISTRATION_d1power.md; one-sided Wilcoxon over seeds, Holm across H-P1 to H-P4)

- H-P1 the label-light rule (calibrated prior) below never checking: 81.44 vs 91.14 (-10.64%, 95% CI -12.40% to -8.85%), p = 0.031, Holm fail -> **NOT CONFIRMED**
- H-P2 the label-light rule below the retrying rule told q and f: 81.44 vs 81.14 (+0.38%, 95% CI -3.36% to +5.29%), p = 0.41, Holm fail -> **NOT CONFIRMED**
- H-P3 cross-checking every call below never checking: 79.96 vs 91.14 (-12.26%, 95% CI -14.49% to -9.78%), p = 0.031, Holm fail -> **NOT CONFIRMED**
- H-P4 cross-checking every call below the retrying rule told q and f: 79.96 vs 81.14 (-1.45%, 95% CI -4.74% to +3.58%), p = 0.31, Holm fail -> **NOT CONFIRMED**

## Reported regardless of outcome (each against never checking)

- v5 vs never: 85.72 vs 91.14 (-5.94%, 95% CI -9.14% to -2.00%)
- v5_fix vs never: 83.00 vs 91.14 (-8.93%, 95% CI -11.33% to -6.36%)
- v5_told vs never: 80.60 vs 91.14 (-11.57%, 95% CI -15.00% to -8.91%)
- cusum vs never: 89.77 vs 91.14 (-1.50%, 95% CI -2.07% to -0.99%)
- always vs never: 88.33 vs 91.14 (-3.08%, 95% CI -8.39% to +3.56%)
- fix_B vs never: 78.25 vs 91.14 (-14.14%, 95% CI -20.86% to -7.26%)
- v5_cal vs always_x: 81.44 vs 79.96 (+1.86%, 95% CI +0.59% to +3.37%)
- Per-seed standard deviation of the loss: never 9.22, v5_cal 7.01, always_x 6.66, v4 4.55