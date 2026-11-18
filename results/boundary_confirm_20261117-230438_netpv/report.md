# Boundary map: monitoring vs buying the better tool (confirm), seeds 8800-8819

3000 runs; 526 s. Cell = (v6 - fixed B) / fixed B; negative = the rule is cheaper.

| A degrades in | B +10% | B +20% | B +35% | B +50% | B +100% | break-even premium |
|---|---|---|---|---|---|---|
| 0% of runs | -4.6% | -10.1% | -18.1% | -25.0% | -41.3% | rule always cheaper |
| 25% of runs | -0.1% | -5.4% | -12.6% | -18.8% | -33.4% | rule always cheaper |
| 50% of runs | +3.0% | -1.1% | -5.9% | -11.3% | -23.3% | about +17% |
| 75% of runs | -1.8% | -5.6% | -11.6% | -16.4% | -27.6% | rule always cheaper |
| 100% of runs | +4.9% | +1.9% | -2.0% | -6.3% | -16.0% | about +27% |

| A degrades in | never vs v6, B +10% | never vs v6, B +20% | never vs v6, B +35% | never vs v6, B +50% | never vs v6, B +100% |
|---|---|---|---|---|---|
| 0% | +0.2% | -0.8% | -1.2% | -1.1% | -1.3% |
| 25% | -1.1% | -0.6% | +1.8% | +5.4% | +6.6% |
| 50% | -0.7% | +4.0% | +8.2% | +10.1% | +12.5% |
| 75% | -0.2% | +1.6% | +6.7% | +11.4% | +14.7% |
| 100% | -3.4% | +2.9% | +5.9% | +15.7% | +17.1% |

## Pre-registered hypotheses (PREREGISTRATION_boundary.md)

- H-B1 monitoring region (B +50% or more, A degrades in 50% of runs or fewer): v6 below fixed B: 153.5 vs 208.6 (-26.4%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-B2 buying region (B +20% or less, A degrades in 75% of runs or more): fixed B below v6: 148.9 vs 148.6 (+0.2%), Wilcoxon p = 0.59 over 20 seeds, Holm fail -> **NOT CONFIRMED**