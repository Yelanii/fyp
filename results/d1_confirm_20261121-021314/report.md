# D1: the rule on live model-backed tools with natural degradation (confirm), seeds 7100-7119

300 GSM8K problems (201-500, subset seed 11); 720 runs; 211 s.

Service accuracy on these problems: qwen2.5:3b 0.687, qwen2.5:1.5b 0.607, phi4-mini 0.860.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task |
|---|---|---|---|---|---|
| never | 72.5 | 30.7% | 3.5% | 0.00 | 0.00 |
| always | 80.4 | 8.3% | 11.1% | 1.22 | 0.00 |
| cusum | 71.8 | 32.0% | 4.2% | 0.07 | 0.00 |
| v4 | 72.6 | 13.8% | 21.2% | 1.32 | 0.00 |
| v4_nocal | 73.3 | 13.8% | 21.2% | 1.39 | 0.00 |
| always_x | 70.6 | 17.8% | 4.8% | 1.10 | 0.24 |
| v5_told | 71.5 | 24.7% | 4.2% | 0.41 | 0.08 |
| v5 | 73.4 | 26.5% | 4.0% | 0.13 | 0.02 |
| fix_B | 79.6 | 8.0% | 6.0% | 0.00 | 0.00 |

| B price | wrong-answer cost | never | always | cusum | v4 | v4_nocal | always_x | v5_told | v5 | fix_B |
|---|---|---|---|---|---|---|---|---|---|---|
| 45 | 100 | 55.7 | 64.9 | 55.4 | 60.6 | 60.9 | 57.2 | 56.8 | 56.8 | 60.3 |
| 52 | 100 | 57.1 | 71.7 | 55.6 | 62.9 | 63.8 | 59.6 | 58.5 | 58.8 | 68.4 |
| 62 | 200 | 88.5 | 87.4 | 87.9 | 81.3 | 82.0 | 80.8 | 83.9 | 87.2 | 87.9 |
| 74 | 200 | 88.7 | 97.7 | 88.2 | 85.6 | 86.4 | 84.9 | 86.9 | 90.7 | 101.7 |

Rule's learned f: median 0.125 (Study M calibration: 0.046).

## Pre-registered hypotheses (PREREGISTRATION_D1.md)

- H-L1 the rule (no labels) below the retrying rule without labels: 73.4 vs 73.3 (+0.1%), one-sided Wilcoxon p = 0.49, Holm fail -> **NOT CONFIRMED**
- H-L3 the rule below never checking: 73.4 vs 72.5 (+1.2%), one-sided Wilcoxon p = 0.99, Holm fail -> **NOT CONFIRMED**
- H-L2 the rule within +3% of the retrying rule told q and f: 73.4 vs 72.6 (+1.0%, 95% CI +0.2% to +2.0%) -> **CONFIRMED**
- Descriptive: the rule vs fix_B: 73.4 vs 79.6 (-7.8%, 95% CI -9.0% to -6.7%)
- Descriptive: the rule vs always: 73.4 vs 80.4 (-8.8%, 95% CI -10.7% to -6.8%)
- Descriptive: the rule vs always_x: 73.4 vs 70.6 (+3.9%, 95% CI +2.8% to +4.9%)
- Descriptive: the rule vs cusum: 73.4 vs 71.8 (+2.2%, 95% CI +1.2% to +3.1%)
- Descriptive: the rule vs v5_told: 73.4 vs 71.5 (+2.6%, 95% CI +1.8% to +3.4%)