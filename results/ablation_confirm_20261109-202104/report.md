# FR21 ablation: pre-registered test

Seeds 1800-1819; 3840 runs; 2654 s. Unit of analysis: the seed (mean over the 32 conditions of drop x q x f x pi). Metric: total loss per task.

## Mean outcomes per strategy

| Strategy | total loss | leak rate | failed tasks | checks/task | cross-checks/task | switches |
|---|---|---|---|---|---|---|
| full | 131.9 | 13.8% | 0.0% | 0.13 | 0.02 | 0.77 |
| nofa | 134.9 | 12.0% | 0.0% | 0.74 | 0.10 | 0.75 |
| noxc | 132.2 | 13.7% | 0.6% | 0.15 | 0.00 | 0.77 |
| noswitch | 156.1 | 18.3% | 1.0% | 2.23 | 0.45 | 0.00 |
| told | 131.7 | 13.5% | 0.0% | 0.18 | 0.02 | 0.77 |
| nowindow | 135.8 | 18.9% | 0.2% | 0.11 | 0.02 | 0.64 |

## Pre-registered hypotheses (PREREGISTRATION_ablation_v51.md)
- H-A1 full below nofa: 131.9 vs 134.9 (+2.3%, 95% CI -2.7% to -1.8%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-A2 full below noxc: 131.9 vs 132.2 (+0.2%, 95% CI -0.5% to +0.1%), Wilcoxon p = 0.0086 over 20 seeds, Holm ok -> CONFIRMED
- H-A3 full below noswitch: 131.9 vs 156.1 (+18.3%, 95% CI -16.1% to -14.9%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-A4 full below told: 131.9 vs 131.7 (-0.1%, 95% CI -0.2% to +0.4%), Wilcoxon p = 0.92 over 20 seeds, Holm fail -> NOT CONFIRMED
- H-A5 full below nowindow: 131.9 vs 135.8 (+3.0%, 95% CI -3.3% to -2.5%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED

## H-A6 (descriptive, not confirmatory): ranked loss increase from removing each ingredient

- noswitch: +18.3%
- nowindow: +3.0%
- nofa: +2.3%
- noxc: +0.2%
- told: -0.1%