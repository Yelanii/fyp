# FR21 ablation: development smoke test (not a test of the hypotheses)

Seeds 1750-1755; 1152 runs; 794 s. Unit of analysis: the seed (mean over the 32 conditions of drop x q x f x pi). Metric: total loss per task.

## Mean outcomes per strategy

| Strategy | total loss | leak rate | failed tasks | checks/task | cross-checks/task | switches |
|---|---|---|---|---|---|---|
| full | 131.0 | 13.5% | 0.0% | 0.12 | 0.01 | 0.75 |
| nofa | 133.5 | 11.8% | 0.0% | 0.62 | 0.07 | 0.75 |
| noxc | 131.4 | 13.2% | 0.6% | 0.16 | 0.00 | 0.75 |
| noswitch | 154.6 | 18.5% | 1.0% | 2.07 | 0.42 | 0.00 |
| told | 130.6 | 12.9% | 0.0% | 0.18 | 0.02 | 0.75 |
| nowindow | 135.4 | 18.9% | 0.2% | 0.10 | 0.01 | 0.58 |

## Pre-registered hypotheses (PREREGISTRATION_ablation_v51.md)
- H-A1 full below nofa: 131.0 vs 133.5 (+1.9%, 95% CI -2.1% to -1.7%), Wilcoxon p = 0.016 over 6 seeds, Holm fail -> NOT CONFIRMED
- H-A2 full below noxc: 131.0 vs 131.4 (+0.3%, 95% CI -0.6% to -0.0%), Wilcoxon p = 0.078 over 6 seeds, Holm fail -> NOT CONFIRMED
- H-A3 full below noswitch: 131.0 vs 154.6 (+18.0%, 95% CI -15.8% to -14.7%), Wilcoxon p = 0.016 over 6 seeds, Holm fail -> NOT CONFIRMED
- H-A4 full below told: 131.0 vs 130.6 (-0.3%, 95% CI -0.0% to +0.7%), Wilcoxon p = 0.92 over 6 seeds, Holm fail -> NOT CONFIRMED
- H-A5 full below nowindow: 131.0 vs 135.4 (+3.4%, 95% CI -4.1% to -2.4%), Wilcoxon p = 0.016 over 6 seeds, Holm fail -> NOT CONFIRMED

## H-A6 (descriptive, not confirmatory): ranked loss increase from removing each ingredient

- noswitch: +18.0%
- nowindow: +3.4%
- nofa: +1.9%
- noxc: +0.3%
- told: -0.3%