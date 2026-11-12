# FR18: any tool can degrade (confirm), seeds 5200-5219

2160 runs; 381 s. 12 conditions per seed. Metric: total loss per task.

| Strategy | all | any_one | any_two | any_recover | wrong kept | failed | checks/task | switches/run |
|---|---|---|---|---|---|---|---|---|
| fix_A | 175.5 | 177.1 | 202.5 | 146.8 | 27.3% | 0.8% | 0.00 | 0.00 |
| fix_B | 199.3 | 183.3 | 229.3 | 185.3 | 28.5% | 0.6% | 0.00 | 0.00 |
| fix_C | 203.2 | 208.0 | 211.9 | 189.8 | 18.5% | 0.4% | 0.00 | 0.00 |
| never | 149.1 | 145.4 | 161.3 | 140.6 | 15.8% | 0.2% | 0.00 | 0.62 |
| cusum | 171.2 | 161.8 | 191.1 | 160.6 | 15.2% | 6.9% | 0.68 | 6.53 |
| always_x | 172.9 | 163.3 | 192.0 | 163.4 | 7.3% | 0.4% | 5.23 | 0.63 |
| v4 | 147.6 | 145.1 | 155.5 | 142.2 | 13.4% | 1.7% | 0.17 | 0.84 |
| v5 | 147.5 | 146.3 | 154.9 | 141.2 | 13.1% | 0.0% | 0.40 | 0.82 |
| v6 | 148.6 | 147.9 | 156.6 | 141.3 | 13.8% | 0.1% | 0.41 | 1.73 |

## Pre-registered hypotheses (PREREGISTRATION_anytool.md)

- H-N1a v6 below fixed tool A: 148.6 vs 175.5 (-15.3%, 95% CI -18.6% to -11.5%), Wilcoxon p = 9.5e-06 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N1b v6 below fixed tool B: 148.6 vs 199.3 (-25.4%, 95% CI -29.9% to -20.8%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N1c v6 below fixed tool C: 148.6 vs 203.2 (-26.9%, 95% CI -31.0% to -22.3%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N2 v6 below never checking: 148.6 vs 149.1 (-0.3%, 95% CI -2.4% to +1.6%), Wilcoxon p = 0.52 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-N3 on any_recover, v6 below v5: 141.3 vs 141.2 (+0.1%, 95% CI -0.5% to +0.7%), Wilcoxon p = 0.61 over 20 seeds, Holm fail -> **NOT CONFIRMED**

- Secondary: v6 vs v5 over all scenarios: 148.6 vs 147.5 (+0.8%, 95% CI +0.0% to +1.5%)
- Descriptive: best fixed tool chosen in hindsight per scenario, mean 175.5; v6 148.6
- Descriptive: v6 re-tests per run 0.68