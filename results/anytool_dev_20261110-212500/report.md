# FR18: any tool can degrade (dev), seeds 4900-4905

648 runs; 115 s. 12 conditions per seed. Metric: total loss per task.

| Strategy | all | any_one | any_two | any_recover | wrong kept | failed | checks/task | switches/run |
|---|---|---|---|---|---|---|---|---|
| fix_A | 178.5 | 166.9 | 193.5 | 175.0 | 28.4% | 0.6% | 0.00 | 0.00 |
| fix_B | 179.3 | 188.3 | 187.0 | 162.7 | 21.3% | 0.3% | 0.00 | 0.00 |
| fix_C | 217.7 | 209.0 | 258.7 | 185.3 | 23.2% | 0.4% | 0.00 | 0.00 |
| never | 153.2 | 144.6 | 159.7 | 155.4 | 17.8% | 0.2% | 0.00 | 0.56 |
| cusum | 162.1 | 158.3 | 169.0 | 159.1 | 12.5% | 5.8% | 0.59 | 5.11 |
| always_x | 169.7 | 161.4 | 182.9 | 164.6 | 5.8% | 0.5% | 5.24 | 0.64 |
| v4 | 149.8 | 147.2 | 149.8 | 152.5 | 14.4% | 1.5% | 0.15 | 0.94 |
| v5 | 149.0 | 145.5 | 150.7 | 150.8 | 14.0% | 0.1% | 0.42 | 0.78 |
| v6 | 149.0 | 147.1 | 151.2 | 148.6 | 14.5% | 0.1% | 0.43 | 1.68 |

## Pre-registered hypotheses (PREREGISTRATION_anytool.md)

- H-N1a v6 below fixed tool A: 149.0 vs 178.5 (-16.5%, 95% CI -22.1% to -10.5%), Wilcoxon p = 0.016 over 6 seeds, Holm fail -> **NOT CONFIRMED**
- H-N1b v6 below fixed tool B: 149.0 vs 179.3 (-16.9%, 95% CI -24.0% to -8.1%), Wilcoxon p = 0.031 over 6 seeds, Holm fail -> **NOT CONFIRMED**
- H-N1c v6 below fixed tool C: 149.0 vs 217.7 (-31.6%, 95% CI -36.9% to -26.6%), Wilcoxon p = 0.016 over 6 seeds, Holm fail -> **NOT CONFIRMED**
- H-N2 v6 below never checking: 149.0 vs 153.2 (-2.8%, 95% CI -6.8% to +1.6%), Wilcoxon p = 0.22 over 6 seeds, Holm fail -> **NOT CONFIRMED**
- H-N3 on any_recover, v6 below v5: 148.6 vs 150.8 (-1.4%, 95% CI -3.3% to +1.1%), Wilcoxon p = 0.22 over 6 seeds, Holm fail -> **NOT CONFIRMED**

- Secondary: v6 vs v5 over all scenarios: 149.0 vs 149.0 (+0.0%, 95% CI -1.1% to +1.1%)
- Descriptive: best fixed tool chosen in hindsight per scenario, mean 172.2; v6 149.0
- Descriptive: v6 re-tests per run 0.76