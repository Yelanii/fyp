# Rule v5 pilot: development smoke test (not a test of the hypotheses)

Seeds 1600-1605; 3456 runs; 1454 s. Unit of analysis: the seed (mean over the 64 conditions of drop x q x leak x f x pi). Metric: total loss per task (spend + leak loss x leaks + one task cost x failed tasks).

## Mean outcomes per strategy

| Strategy | told | total loss | spend | leak rate | failed tasks | checks/task | cross-checks/task |
|---|---|---|---|---|---|---|---|
| never | true | 153.6 | 108.8 | 18.1% | 0.2% | 0.00 | 0.00 |
| always | true | 174.2 | 141.3 | 2.8% | 21.0% | 5.53 | 0.00 |
| cusum | true | 152.6 | 120.9 | 11.6% | 2.5% | 0.54 | 0.00 |
| v4 | true | 145.1 | 115.0 | 12.4% | 1.4% | 0.47 | 0.00 |
| v4_nocal | none | 164.9 | 139.1 | 5.9% | 12.1% | 3.12 | 0.00 |
| v4_miscal | wrong | 147.7 | 121.3 | 10.6% | 3.2% | 1.04 | 0.00 |
| always_x | true | 157.6 | 145.5 | 4.7% | 0.4% | 5.26 | 0.69 |
| v5_told | true | 145.0 | 127.8 | 8.3% | 0.2% | 2.22 | 0.26 |
| v5 | none | 142.7 | 118.4 | 11.0% | 0.2% | 0.91 | 0.10 |

## By wrong-answer cost (leak weight) and persistence (mean total loss)

| Strategy | leak 1 | leak 3 | pi = 0 | pi = 1 |
|---|---|---|---|---|
| never | 131.3 | 175.9 | 153.6 | 153.6 |
| always | 170.7 | 177.7 | 157.4 | 191.0 |
| cusum | 138.3 | 167.0 | 148.5 | 156.8 |
| v4 | 129.1 | 161.2 | 143.6 | 146.6 |
| v4_nocal | 143.8 | 185.9 | 157.0 | 172.8 |
| v4_miscal | 129.4 | 166.0 | 143.0 | 152.3 |
| always_x | 151.8 | 163.5 | 157.5 | 157.8 |
| v5_told | 129.9 | 160.2 | 145.1 | 145.0 |
| v5 | 128.4 | 157.0 | 142.8 | 142.6 |

## By degradation level (mean total loss)

| Strategy | 95% | 85% | 75% | 60% |
|---|---|---|---|---|
| never | 126.3 | 159.5 | 164.9 | 163.8 |
| always | 170.5 | 173.9 | 173.6 | 178.7 |
| cusum | 145.9 | 155.4 | 154.8 | 154.3 |
| v4 | 131.6 | 149.3 | 150.6 | 149.0 |
| v4_nocal | 161.0 | 166.6 | 163.9 | 168.0 |
| v4_miscal | 138.7 | 151.0 | 150.0 | 150.9 |
| always_x | 146.5 | 155.0 | 162.7 | 166.5 |
| v5_told | 132.4 | 149.5 | 148.2 | 150.1 |
| v5 | 129.5 | 146.4 | 147.8 | 147.3 |

## Pre-registered hypotheses (PREREGISTRATION_v5.md)
- H-V1 v5 below v4 by >= 3%: 142.7 vs 145.1 (-1.6%, 95% CI -2.5% to -0.5%), Wilcoxon p = 0.047 over 6 seeds, Holm ok -> NOT CONFIRMED
- H-V2 v5 below v4_nocal by >= 5%: 142.7 vs 164.9 (-13.4%, 95% CI -15.0% to -11.9%), Wilcoxon p = 0.016 over 6 seeds, Holm ok -> CONFIRMED
- H-V3 v5 below always_x by >= 0%: 142.7 vs 157.6 (-9.5%, 95% CI -11.5% to -7.5%), Wilcoxon p = 0.016 over 6 seeds, Holm ok -> CONFIRMED
- H-V4 v5 (no labels) within 3% of v5_told (told q and f): 142.7 vs 145.0 (-1.6%, 95% CI upper -0.6%) -> CONFIRMED
- H-V5 persistence barely matters for v5: loss(pi = 1) - loss(pi = 0) = -0.15 (0.1% of its loss; need <= 2%), vs v4 +2.93 (v5 smaller: p = 0.016) -> CONFIRMED
- H-V6 v5 learns f without labels: median |f_hat - f| at the end of a run = 0.026 (need <= 0.03) -> CONFIRMED. Descriptive: median |q_hat - q| = 0.341
- H-V7 v5 below v4 told wrong values: 142.7 vs 147.7 (-3.3%), p = 0.031 -> CONFIRMED

## Where the difference comes from (descriptive)
- Cross-check policy (v5_told vs v4, both told q and f): 145.0 vs 145.1
- Learning instead of being told (v5 vs v5_told): 142.7 vs 145.0