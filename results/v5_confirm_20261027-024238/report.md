# Rule v5 pilot: pre-registered test

Seeds 1700-1719; 11520 runs; 4022 s. Unit of analysis: the seed (mean over the 64 conditions of drop x q x leak x f x pi). Metric: total loss per task (spend + leak loss x leaks + one task cost x failed tasks).

## Mean outcomes per strategy

| Strategy | told | total loss | spend | leak rate | failed tasks | checks/task | cross-checks/task |
|---|---|---|---|---|---|---|---|
| never | true | 161.2 | 108.4 | 21.4% | 0.1% | 0.00 | 0.00 |
| always | true | 174.2 | 141.9 | 2.7% | 20.8% | 5.53 | 0.00 |
| cusum | true | 153.6 | 120.6 | 12.2% | 2.4% | 0.50 | 0.00 |
| v4 | true | 147.1 | 115.6 | 13.1% | 1.2% | 0.46 | 0.00 |
| v4_nocal | none | 165.1 | 139.4 | 6.4% | 11.8% | 3.00 | 0.00 |
| v4_miscal | wrong | 149.1 | 121.4 | 11.4% | 2.7% | 0.94 | 0.00 |
| always_x | true | 156.8 | 145.7 | 4.4% | 0.2% | 5.26 | 0.70 |
| v5_told | true | 146.2 | 127.7 | 9.1% | 0.1% | 2.15 | 0.24 |
| v5 | none | 145.5 | 117.4 | 12.5% | 0.1% | 0.79 | 0.08 |

## By wrong-answer cost (leak weight) and persistence (mean total loss)

| Strategy | leak 1 | leak 3 | pi = 0 | pi = 1 |
|---|---|---|---|---|
| never | 134.9 | 187.5 | 161.2 | 161.2 |
| always | 170.9 | 177.5 | 157.5 | 190.8 |
| cusum | 138.6 | 168.6 | 149.5 | 157.7 |
| v4 | 130.6 | 163.6 | 145.5 | 148.7 |
| v4_nocal | 144.9 | 185.3 | 156.5 | 173.7 |
| v4_miscal | 130.6 | 167.7 | 145.3 | 153.0 |
| always_x | 151.4 | 162.3 | 156.7 | 157.0 |
| v5_told | 131.0 | 161.3 | 146.0 | 146.3 |
| v5 | 130.2 | 160.9 | 145.5 | 145.5 |

## By degradation level (mean total loss)

| Strategy | 95% | 85% | 75% | 60% |
|---|---|---|---|---|
| never | 134.6 | 170.0 | 181.4 | 158.8 |
| always | 164.1 | 174.0 | 176.7 | 181.9 |
| cusum | 146.4 | 156.2 | 155.0 | 156.8 |
| v4 | 138.0 | 151.6 | 148.4 | 150.4 |
| v4_nocal | 157.8 | 166.9 | 166.5 | 169.1 |
| v4_miscal | 141.3 | 152.1 | 150.6 | 152.6 |
| always_x | 143.5 | 155.5 | 165.6 | 162.9 |
| v5_told | 136.5 | 150.1 | 147.6 | 150.4 |
| v5 | 137.0 | 150.1 | 147.0 | 148.1 |

## Pre-registered hypotheses (PREREGISTRATION_v5.md)
- H-V1 v5 below v4 by >= 3%: 145.5 vs 147.1 (-1.0%, 95% CI -1.4% to -0.6%), Wilcoxon p = 0.00035 over 20 seeds, Holm ok -> NOT CONFIRMED
- H-V2 v5 below v4_nocal by >= 5%: 145.5 vs 165.1 (-11.8%, 95% CI -12.4% to -11.2%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-V3 v5 below always_x by >= 0%: 145.5 vs 156.8 (-7.2%, 95% CI -8.2% to -6.3%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-V4 v5 (no labels) within 3% of v5_told (told q and f): 145.5 vs 146.2 (-0.4%, 95% CI upper +0.3%) -> CONFIRMED
- H-V5 persistence barely matters for v5: loss(pi = 1) - loss(pi = 0) = +0.00 (0.0% of its loss; need <= 2%), vs v4 +3.23 (v5 smaller: p = 9.5e-07) -> CONFIRMED
- H-V6 v5 learns f without labels: median |f_hat - f| at the end of a run = 0.028 (need <= 0.03) -> CONFIRMED. Descriptive: median |q_hat - q| = 0.368
- H-V7 v5 below v4 told wrong values: 145.5 vs 149.1 (-2.4%), p = 9.5e-07 -> CONFIRMED

## Where the difference comes from (descriptive)
- Cross-check policy (v5_told vs v4, both told q and f): 146.2 vs 147.1
- Learning instead of being told (v5 vs v5_told): 145.5 vs 146.2