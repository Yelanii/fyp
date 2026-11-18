# Rule v5 pilot: pre-registered test

Seeds 8200-8219; 14080 runs; 16985 s. Unit of analysis: the seed (mean over the 64 conditions of drop x q x leak x f x pi). Metric: total loss per task (spend + leak loss x leaks + one task cost x failed tasks).

## Mean outcomes per strategy

| Strategy | told | total loss | spend | leak rate | failed tasks | checks/task | cross-checks/task |
|---|---|---|---|---|---|---|---|
| never | true | 159.5 | 108.6 | 20.6% | 0.1% | 0.00 | 0.00 |
| always | true | 173.0 | 141.1 | 2.6% | 20.7% | 5.52 | 0.00 |
| cusum | true | 152.0 | 120.7 | 11.6% | 2.1% | 0.48 | 0.00 |
| v4 | true | 145.8 | 115.3 | 12.6% | 1.2% | 0.45 | 0.00 |
| v4_nocal | none | 165.8 | 140.3 | 5.9% | 12.1% | 3.02 | 0.00 |
| v4_miscal | wrong | 148.1 | 121.6 | 10.7% | 2.8% | 0.95 | 0.00 |
| always_x | true | 157.5 | 145.8 | 4.6% | 0.2% | 5.26 | 0.70 |
| v5_told | true | 144.0 | 124.2 | 9.7% | 0.0% | 1.76 | 0.20 |
| v5 | none | 144.8 | 115.8 | 12.7% | 0.0% | 0.53 | 0.05 |
| v5_rho | none | 145.6 | 117.4 | 12.3% | 0.0% | 0.49 | 0.05 |
| v5_rho_noaudit | none | 145.3 | 117.0 | 12.3% | 0.0% | 0.45 | 0.04 |

## By wrong-answer cost (leak weight) and persistence (mean total loss)

| Strategy | leak 1 | leak 3 | pi = 0 | pi = 1 |
|---|---|---|---|---|
| never | 134.1 | 184.8 | 159.5 | 159.5 |
| always | 169.8 | 176.2 | 156.3 | 189.7 |
| cusum | 137.6 | 166.3 | 147.8 | 156.2 |
| v4 | 129.6 | 161.9 | 144.3 | 147.3 |
| v4_nocal | 146.0 | 185.6 | 157.3 | 174.3 |
| v4_miscal | 129.7 | 166.4 | 143.9 | 152.2 |
| always_x | 151.8 | 163.2 | 157.3 | 157.7 |
| v5_told | 129.1 | 159.0 | 144.0 | 144.1 |
| v5 | 129.1 | 160.4 | 144.7 | 144.8 |
| v5_rho | 129.2 | 161.9 | 145.6 | 145.6 |
| v5_rho_noaudit | 129.1 | 161.5 | 145.3 | 145.3 |

## By degradation level (mean total loss)

| Strategy | 95% | 85% | 75% | 60% |
|---|---|---|---|---|
| never | 128.2 | 165.6 | 179.9 | 164.1 |
| always | 165.1 | 170.0 | 177.0 | 179.9 |
| cusum | 140.8 | 154.6 | 155.3 | 157.2 |
| v4 | 132.4 | 148.7 | 149.4 | 152.6 |
| v4_nocal | 159.9 | 166.1 | 167.5 | 169.7 |
| v4_miscal | 137.5 | 149.4 | 152.1 | 153.4 |
| always_x | 144.8 | 155.0 | 167.3 | 162.9 |
| v5_told | 132.1 | 146.6 | 147.3 | 150.2 |
| v5 | 131.2 | 148.8 | 148.5 | 150.6 |
| v5_rho | 132.3 | 149.3 | 149.5 | 151.3 |
| v5_rho_noaudit | 132.3 | 149.2 | 149.2 | 150.6 |

## Pre-registered hypotheses (PREREGISTRATION_v5.md)
- H-V1 v5 below v4 by >= 3%: 144.8 vs 145.8 (-0.7%, 95% CI -1.1% to -0.2%), Wilcoxon p = 0.0036 over 20 seeds, Holm ok -> NOT CONFIRMED
- H-V2 v5 below v4_nocal by >= 5%: 144.8 vs 165.8 (-12.7%, 95% CI -13.5% to -11.9%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-V3 v5 below always_x by >= 0%: 144.8 vs 157.5 (-8.1%, 95% CI -8.9% to -7.2%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-V4 v5 (no labels) within 3% of v5_told (told q and f): 144.8 vs 144.0 (+0.5%, 95% CI upper +1.2%) -> CONFIRMED
- H-V5 persistence barely matters for v5: loss(pi = 1) - loss(pi = 0) = +0.12 (0.1% of its loss; need <= 2%), vs v4 +3.00 (v5 smaller: p = 9.5e-07) -> CONFIRMED
- H-V6 v5 learns f without labels: median |f_hat - f| at the end of a run = 0.041 (need <= 0.03) -> NOT CONFIRMED. Descriptive: median |q_hat - q| = 0.376
- H-V7 v5 below v4 told wrong values: 144.8 vs 148.1 (-2.2%), p = 1.9e-06 -> CONFIRMED

## Where the difference comes from (descriptive)
- Cross-check policy (v5_told vs v4, both told q and f): 144.0 vs 145.8
- Learning instead of being told (v5 vs v5_told): 144.8 vs 144.0