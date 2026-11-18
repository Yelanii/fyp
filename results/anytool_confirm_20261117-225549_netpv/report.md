# FR18: any tool can degrade (confirm), seeds 8700-8719

2160 runs; 1584 s. 12 conditions per seed. Metric: total loss per task.

| Strategy | all | any_one | any_two | any_recover | wrong kept | failed | checks/task | switches/run |
|---|---|---|---|---|---|---|---|---|
| fix_A | 170.0 | 170.2 | 184.4 | 155.5 | 25.5% | 0.5% | 0.00 | 0.00 |
| fix_B | 187.9 | 175.0 | 219.2 | 169.6 | 24.3% | 0.3% | 0.00 | 0.00 |
| fix_C | 222.4 | 224.9 | 248.8 | 193.7 | 24.9% | 0.7% | 0.00 | 0.00 |
| never | 147.4 | 145.1 | 153.5 | 143.5 | 15.7% | 0.2% | 0.00 | 0.50 |
| cusum | 164.4 | 162.8 | 175.5 | 154.9 | 13.6% | 6.4% | 0.62 | 5.47 |
| always_x | 171.0 | 162.3 | 187.8 | 163.0 | 7.4% | 0.3% | 5.22 | 0.56 |
| v4 | 146.3 | 142.9 | 152.1 | 143.8 | 13.0% | 2.0% | 0.18 | 0.89 |
| v5 | 144.5 | 140.7 | 150.8 | 141.9 | 12.7% | 0.1% | 0.40 | 0.72 |
| v6 | 146.8 | 143.8 | 153.6 | 143.1 | 13.7% | 0.1% | 0.44 | 1.57 |

## Pre-registered hypotheses (PREREGISTRATION_anytool.md)

- H-N1a v6 below fixed tool A: 146.8 vs 170.0 (-13.6%, 95% CI -18.0% to -8.8%), Wilcoxon p = 0.00043 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N1b v6 below fixed tool B: 146.8 vs 187.9 (-21.9%, 95% CI -26.1% to -16.6%), Wilcoxon p = 6.7e-06 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N1c v6 below fixed tool C: 146.8 vs 222.4 (-34.0%, 95% CI -39.0% to -28.2%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N2 v6 below never checking: 146.8 vs 147.4 (-0.4%, 95% CI -2.3% to +1.5%), Wilcoxon p = 0.51 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-N3 on any_recover, v6 below v5: 143.1 vs 141.9 (+0.9%, 95% CI -0.7% to +2.8%), Wilcoxon p = 0.73 over 20 seeds, Holm fail -> **NOT CONFIRMED**

- Secondary: v6 vs v5 over all scenarios: 146.8 vs 144.5 (+1.6%, 95% CI +0.9% to +2.6%)
- Descriptive: best fixed tool chosen in hindsight per scenario, mean 170.0; v6 146.8
- Descriptive: v6 re-tests per run 0.66