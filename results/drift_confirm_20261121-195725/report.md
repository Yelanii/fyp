# Drift test (confirm), seeds 9600-9619

3360 runs; 2156 s. Part G: 12 conditions per seed (gradual decline, f = 0.15, fully repeated verdicts). Part D: 12 conditions per seed (sudden drop; the checker changes from q = 0.95, f = 0.05 to f = 0.20 or q = 0.60).

## Part G: gradual decline

| Strategy | total loss | spend | wrong-answer cost | failure cost | wrong kept | failed | checks/task |
|---|---|---|---|---|---|---|---|
| never | 168.2 | 108.2 | 59.9 | 0.2 | 24.3% | 0.1% | 0.00 |
| cusum | 163.6 | 124.4 | 31.1 | 8.1 | 12.6% | 6.5% | 0.63 |
| v4 | 150.8 | 113.2 | 35.7 | 1.9 | 15.1% | 1.6% | 0.14 |
| v4_nocal | 187.9 | 136.9 | 10.3 | 40.7 | 5.5% | 33.0% | 3.11 |
| always_x | 166.6 | 152.2 | 14.1 | 0.3 | 5.7% | 0.2% | 5.31 |
| v5_told | 150.3 | 126.3 | 23.9 | 0.1 | 11.5% | 0.1% | 1.48 |
| v5 | 148.9 | 114.9 | 33.9 | 0.1 | 14.7% | 0.1% | 0.26 |

## Part D: the checker changes during the run

| Strategy | total loss | spend | wrong-answer cost | failure cost | wrong kept | failed | checks/task |
|---|---|---|---|---|---|---|---|
| never | 168.7 | 110.7 | 57.7 | 0.3 | 23.4% | 0.2% | 0.00 |
| cusum | 157.1 | 120.5 | 32.4 | 4.2 | 13.1% | 3.4% | 0.49 |
| v4 | 157.1 | 123.7 | 24.4 | 9.0 | 11.7% | 7.3% | 0.96 |
| v4_nocal | 170.3 | 134.5 | 12.9 | 22.9 | 7.0% | 18.6% | 2.75 |
| always_x | 165.0 | 147.6 | 16.8 | 0.6 | 6.8% | 0.5% | 5.33 |
| v5_told | 149.6 | 131.2 | 18.3 | 0.1 | 9.3% | 0.1% | 2.29 |
| v5 | 150.1 | 119.1 | 31.0 | 0.1 | 13.6% | 0.0% | 0.63 |

## Pre-registered hypotheses (PREREGISTRATION_drift.md)

Non-inferiority: confirmed if the upper end of the 95% bootstrap CI of the difference is at most +3%. Superiority: one-sided Wilcoxon on seed means, Holm across H-G2, H-G3 and H-D2.

- H-G1 part G: the rule within 3% of the same rule told q and f: 148.9 vs 150.3 (-0.93%, 95% CI -1.90% to -0.04%) -> **CONFIRMED**
- H-D1 part D: the rule within 3% of the same rule told the rates from before the change: 150.1 vs 149.6 (+0.35%, 95% CI -0.61% to +1.24%) -> **CONFIRMED**
- H-G2 part G: the rule below the label-free retrying rule: 148.9 vs 187.9 (-20.8%, 95% CI -22.3% to -19.2%), one-sided Wilcoxon p = 9.5e-07, Holm ok -> **CONFIRMED**
- H-G3 part G: the rule below never checking: 148.9 vs 168.2 (-11.5%, 95% CI -12.9% to -10.1%), one-sided Wilcoxon p = 9.5e-07, Holm ok -> **CONFIRMED**
- H-D2 part D: the rule below the label-free retrying rule: 150.1 vs 170.3 (-11.8%, 95% CI -13.2% to -10.4%), one-sided Wilcoxon p = 9.5e-07, Holm ok -> **CONFIRMED**

## Descriptive

- Part G: v5 vs v4: 148.9 vs 150.8 (-1.3%, 95% CI -2.0% to -0.6%)
- Part G: v5 vs cusum: 148.9 vs 163.6 (-9.0%, 95% CI -10.7% to -7.1%)
- Part G: v5 vs always_x: 148.9 vs 166.6 (-10.6%, 95% CI -11.6% to -9.6%)
- Part G: v5 vs never: 148.9 vs 168.2 (-11.5%, 95% CI -12.9% to -10.1%)
- Part D: v5 vs v4: 150.1 vs 157.1 (-4.5%, 95% CI -5.7% to -3.3%)
- Part D: v5 vs cusum: 150.1 vs 157.1 (-4.5%, 95% CI -5.7% to -3.3%)
- Part D: v5 vs always_x: 150.1 vs 165.0 (-9.0%, 95% CI -10.8% to -7.3%)
- Part D: v5 vs never: 150.1 vs 168.7 (-11.0%, 95% CI -13.3% to -8.7%)
- Part G, level 0.85: v5 145.1, v5_told 147.3, v4_nocal 187.1, never 157.0
- Part G, level 0.75: v5 152.1, v5_told 152.1, v4_nocal 187.8, never 182.1
- Part G, level 0.60: v5 149.4, v5_told 151.4, v4_nocal 188.8, never 165.4
- Part D, f_up: v5 150.6, v5_told 150.9, v4 160.2, v4_nocal 175.9, never 168.7
  learned at the end of the run (median): f 0.147, q 0.455
- Part D, q_down: v5 149.7, v5_told 148.3, v4 154.0, v4_nocal 164.7, never 168.7
  learned at the end of the run (median): f 0.072, q 0.446