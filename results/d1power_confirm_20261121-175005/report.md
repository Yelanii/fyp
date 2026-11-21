# D1-power: live tools, high-power replication (confirm), seeds 7400-7599

8000 runs; 1337 s; 200 seeds x 4 conditions. Cached answers; no model called.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task | median learned f |
|---|---|---|---|---|---|---|
| never | 72.67 | 32.5% | 3.2% | 0.00 | 0.00 | - |
| always | 81.20 | 8.4% | 10.7% | 1.21 | 0.00 | - |
| cusum | 72.32 | 32.4% | 4.1% | 0.08 | 0.00 | - |
| v4 | 73.32 | 14.2% | 21.2% | 1.31 | 0.00 | - |
| always_x | 71.05 | 18.0% | 4.5% | 1.09 | 0.24 | - |
| v5_told | 72.34 | 24.9% | 4.0% | 0.41 | 0.08 | 0.040 |
| v5 | 73.54 | 26.5% | 3.9% | 0.12 | 0.02 | 0.135 |
| v5_fix | 73.21 | 26.0% | 3.9% | 0.20 | 0.04 | 0.088 |
| v5_cal | 72.31 | 24.9% | 4.0% | 0.39 | 0.08 | 0.046 |
| fix_B | 79.59 | 8.0% | 6.0% | 0.00 | 0.00 | - |

| B price | wrong-answer cost | never | always | cusum | v4 | always_x | v5_told | v5 | v5_fix | v5_cal | fix_B |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 45 | 100 | 55.8 | 64.8 | 55.8 | 61.0 | 57.5 | 57.0 | 56.7 | 56.8 | 57.0 | 60.4 |
| 52 | 100 | 56.4 | 72.4 | 56.0 | 63.6 | 59.9 | 58.8 | 58.7 | 58.8 | 58.9 | 68.4 |
| 62 | 200 | 89.2 | 89.1 | 88.6 | 82.1 | 81.3 | 85.5 | 87.9 | 87.0 | 85.4 | 87.9 |
| 74 | 200 | 89.3 | 98.5 | 88.9 | 86.6 | 85.5 | 88.1 | 90.8 | 90.2 | 88.0 | 101.7 |

## Pre-registered hypotheses (PREREGISTRATION_d1power.md; one-sided Wilcoxon over seeds, Holm across H-P1 to H-P4)

- H-P1 the label-light rule (calibrated prior) below never checking: 72.31 vs 72.67 (-0.49%, 95% CI -0.78% to -0.20%), p = 0.00063, Holm ok -> **CONFIRMED**
- H-P2 the label-light rule below the retrying rule told q and f: 72.31 vs 73.32 (-1.37%, 95% CI -1.74% to -1.01%), p = 3.4e-11, Holm ok -> **CONFIRMED**
- H-P3 cross-checking every call below never checking: 71.05 vs 72.67 (-2.23%, 95% CI -2.50% to -1.97%), p = 5.1e-29, Holm ok -> **CONFIRMED**
- H-P4 cross-checking every call below the retrying rule told q and f: 71.05 vs 73.32 (-3.10%, 95% CI -3.39% to -2.80%), p = 1e-31, Holm ok -> **CONFIRMED**

## Reported regardless of outcome (each against never checking)

- v5 vs never: 73.54 vs 72.67 (+1.20%, 95% CI +0.86% to +1.54%)
- v5_fix vs never: 73.21 vs 72.67 (+0.74%, 95% CI +0.40% to +1.08%)
- v5_told vs never: 72.34 vs 72.67 (-0.45%, 95% CI -0.72% to -0.18%)
- cusum vs never: 72.32 vs 72.67 (-0.47%, 95% CI -0.64% to -0.32%)
- always vs never: 81.20 vs 72.67 (+11.75%, 95% CI +11.03% to +12.48%)
- fix_B vs never: 79.59 vs 72.67 (+9.52%, 95% CI +9.06% to +9.99%)
- v5_cal vs always_x: 72.31 vs 71.05 (+1.78%, 95% CI +1.47% to +2.10%)
- Per-seed standard deviation of the loss: never 2.24, v5_cal 2.46, always_x 2.02, v4 2.27