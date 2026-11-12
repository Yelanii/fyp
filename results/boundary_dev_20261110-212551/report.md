# Boundary map: monitoring vs buying the better tool (dev), seeds 4950-4951

300 runs; 50 s. Cell = (v6 - fixed B) / fixed B; negative = the rule is cheaper.

| A degrades in | B +10% | B +20% | B +35% | B +50% | B +100% | break-even premium |
|---|---|---|---|---|---|---|
| 0% of runs | -2.2% | -9.0% | -16.9% | -26.0% | -42.3% | rule always cheaper |
| 25% of runs | -5.1% | -9.9% | -19.8% | -25.8% | -42.6% | rule always cheaper |
| 50% of runs | +4.4% | +1.1% | -5.9% | -10.7% | -23.3% | about +22% |
| 75% of runs | +5.0% | +0.0% | -3.9% | -7.3% | -18.4% | about +20% |
| 100% of runs | +11.6% | +7.3% | +1.7% | -1.4% | -13.4% | about +43% |

| A degrades in | never vs v6, B +10% | never vs v6, B +20% | never vs v6, B +35% | never vs v6, B +50% | never vs v6, B +100% |
|---|---|---|---|---|---|
| 0% | -3.4% | -3.2% | -3.9% | -1.2% | -1.3% |
| 25% | -1.1% | -2.9% | -0.9% | -1.9% | -0.9% |
| 50% | -6.3% | -3.5% | -3.0% | +2.6% | +14.2% |
| 75% | -3.0% | +2.1% | +1.6% | +7.1% | +18.5% |
| 100% | -0.4% | +9.7% | +8.4% | +5.5% | +19.0% |

## Pre-registered hypotheses (PREREGISTRATION_boundary.md)

- H-B1 monitoring region (B +50% or more, A degrades in 50% of runs or fewer): v6 below fixed B: 146.1 vs 207.1 (-29.4%), Wilcoxon p = 0.25 over 2 seeds, Holm fail -> **NOT CONFIRMED**
- H-B2 buying region (B +20% or less, A degrades in 75% of runs or more): fixed B below v6: 145.3 vs 153.9 (-5.5%), Wilcoxon p = 0.25 over 2 seeds, Holm fail -> **NOT CONFIRMED**