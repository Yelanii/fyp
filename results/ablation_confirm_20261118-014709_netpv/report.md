# FR21 ablation: pre-registered test

Seeds 8900-8919; 3840 runs; 9750 s. Unit of analysis: the seed (mean over the 32 conditions of drop x q x f x pi). Metric: total loss per task.

## Mean outcomes per strategy

| Strategy | total loss | leak rate | failed tasks | checks/task | cross-checks/task | switches |
|---|---|---|---|---|---|---|
| full | 131.5 | 13.2% | 0.0% | 0.10 | 0.01 | 0.81 |
| nofa | 132.0 | 12.5% | 0.0% | 0.26 | 0.03 | 0.81 |
| noxc | 132.0 | 13.1% | 0.5% | 0.13 | 0.00 | 0.82 |
| noswitch | 154.5 | 21.5% | 0.9% | 1.68 | 0.35 | 0.00 |
| told | 131.3 | 13.1% | 0.0% | 0.12 | 0.01 | 0.81 |
| nowindow | 134.4 | 17.7% | 0.1% | 0.10 | 0.01 | 0.65 |

## Pre-registered hypotheses (PREREGISTRATION_ablation_v51.md)
- H-A1 full below nofa: 131.5 vs 132.0 (+0.4%, 95% CI -0.7% to -0.1%), Wilcoxon p = 0.0086 over 20 seeds, Holm ok -> CONFIRMED
- H-A2 full below noxc: 131.5 vs 132.0 (+0.4%, 95% CI -0.7% to -0.1%), Wilcoxon p = 0.0021 over 20 seeds, Holm ok -> CONFIRMED
- H-A3 full below noswitch: 131.5 vs 154.5 (+17.5%, 95% CI -15.6% to -14.0%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-A4 full below told: 131.5 vs 131.3 (-0.1%, 95% CI -0.1% to +0.4%), Wilcoxon p = 0.68 over 20 seeds, Holm fail -> NOT CONFIRMED
- H-A5 full below nowindow: 131.5 vs 134.4 (+2.2%, 95% CI -3.0% to -1.1%), Wilcoxon p = 0.00035 over 20 seeds, Holm ok -> CONFIRMED

## H-A6 (descriptive, not confirmatory): ranked loss increase from removing each ingredient

- noswitch: +17.5%
- nowindow: +2.2%
- noxc: +0.4%
- nofa: +0.4%
- told: -0.1%