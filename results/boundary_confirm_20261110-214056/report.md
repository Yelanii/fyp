# Boundary map: monitoring vs buying the better tool (confirm), seeds 5100-5119

3000 runs; 515 s. Cell = (v6 - fixed B) / fixed B; negative = the rule is cheaper.

| A degrades in | B +10% | B +20% | B +35% | B +50% | B +100% | break-even premium |
|---|---|---|---|---|---|---|
| 0% of runs | -6.1% | -12.5% | -20.2% | -26.8% | -43.1% | rule always cheaper |
| 25% of runs | -1.1% | -6.2% | -12.9% | -18.2% | -31.3% | rule always cheaper |
| 50% of runs | +1.1% | -3.6% | -8.8% | -14.0% | -25.4% | about +12% |
| 75% of runs | +2.9% | -1.4% | -5.4% | -9.2% | -18.9% | about +17% |
| 100% of runs | +3.3% | +0.2% | -2.7% | -6.7% | -15.7% | about +21% |

| A degrades in | never vs v6, B +10% | never vs v6, B +20% | never vs v6, B +35% | never vs v6, B +50% | never vs v6, B +100% |
|---|---|---|---|---|---|
| 0% | -1.7% | -1.6% | -1.8% | -2.0% | -1.1% |
| 25% | -1.0% | +0.0% | +2.2% | +5.1% | +7.6% |
| 50% | -2.9% | +0.2% | +4.2% | +14.3% | +15.0% |
| 75% | -1.8% | +1.3% | +2.3% | +11.2% | +15.4% |
| 100% | -1.0% | +2.9% | +3.6% | +11.6% | +18.9% |

## Pre-registered hypotheses (PREREGISTRATION_boundary.md)

- H-B1 monitoring region (B +50% or more, A degrades in 50% of runs or fewer): v6 below fixed B: 152.6 vs 209.9 (-27.3%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-B2 buying region (B +20% or less, A degrades in 75% of runs or more): fixed B below v6: 148.3 vs 150.0 (-1.2%), Wilcoxon p = 0.077 over 20 seeds, Holm fail -> **NOT CONFIRMED**