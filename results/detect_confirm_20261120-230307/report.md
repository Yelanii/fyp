# N1 detectability test (confirm), seeds 9200-9219

7200 runs; 2244 s. Gap = (rule - buy B) / buy B; negative = the rule is cheaper.

## Mean gap over the grid

| detectability (q, f) | q - f | rho = 0.5 | rho = 0 |
|---|---|---|---|
| high (0.95, 0.15) | 0.80 | -11.8% | -3.5% |
| mid (0.85, 0.35) | 0.50 | -10.9% | -0.9% |
| low (0.8, 0.55) | 0.25 | -10.3% | +0.5% |

## Break-even premium of tool B (rule cheaper above it)

| detectability | rho | A degrades in 25% | A degrades in 50% | A degrades in 100% |
|---|---|---|---|---|
| high | 0.5 | rule always cheaper | about +11% | about +33% |
| high | 0.0 | about +12% | about +27% | about +67% |
| mid | 0.5 | rule always cheaper | about +12% | about +40% |
| mid | 0.0 | about +25% | about +39% | about +75% |
| low | 0.5 | rule always cheaper | about +13% | about +43% |
| low | 0.0 | about +22% | about +44% | about +84% |

## Gap by cell

| detectability | rho | A degrades in | B +10% | B +20% | B +35% | B +50% | B +100% |
|---|---|---|---|---|---|---|---|
| high | 0.5 | 25% | -2.4% | -7.0% | -14.6% | -20.7% | -35.9% |
| high | 0.5 | 50% | +0.7% | -4.2% | -11.5% | -16.2% | -29.2% |
| high | 0.5 | 100% | +5.4% | +2.5% | -0.3% | -4.2% | -13.1% |
| high | 0.0 | 25% | +0.5% | -1.5% | -7.1% | -11.5% | -23.8% |
| high | 0.0 | 50% | +5.9% | +1.3% | -1.4% | -7.3% | -17.3% |
| high | 0.0 | 100% | +11.6% | +13.0% | +7.9% | +4.0% | -7.6% |
| mid | 0.5 | 25% | -2.3% | -6.9% | -13.9% | -19.7% | -35.0% |
| mid | 0.5 | 50% | +0.8% | -4.0% | -10.6% | -14.9% | -27.6% |
| mid | 0.5 | 100% | +6.3% | +3.4% | +1.1% | -2.0% | -11.9% |
| mid | 0.0 | 25% | +4.5% | +1.6% | -3.2% | -11.2% | -25.2% |
| mid | 0.0 | 50% | +10.2% | +5.2% | +1.2% | -3.7% | -17.0% |
| mid | 0.0 | 100% | +17.4% | +16.3% | +12.3% | +5.4% | -5.3% |
| low | 0.5 | 25% | -1.6% | -6.2% | -13.3% | -19.4% | -34.4% |
| low | 0.5 | 50% | +1.5% | -3.2% | -9.7% | -14.3% | -27.1% |
| low | 0.5 | 100% | +6.8% | +3.7% | +1.7% | -1.4% | -11.3% |
| low | 0.0 | 25% | +4.2% | +0.9% | -5.3% | -8.1% | -24.8% |
| low | 0.0 | 50% | +12.2% | +5.8% | +3.8% | -2.6% | -15.7% |
| low | 0.0 | 100% | +24.4% | +18.4% | +12.8% | +9.6% | -4.6% |

## Pre-registered hypotheses (PREREGISTRATION_detect.md)

- N1-1 at rho = 0.5, the gap is larger (worse for the rule) at low than at high detectability: -10.3% vs -11.8% (difference +1.5 points), one-sided Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- N1-2 at rho = 0, the gap is larger at low than at high detectability: +0.5% vs -3.5% (difference +4.0 points), one-sided Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- N1-3 at high detectability, the gap is larger with no loud failures (rho = 0) than with rho = 0.5: -3.5% vs -11.8% (difference +8.4 points), one-sided Wilcoxon p = 1.9e-06 over 20 seeds, Holm ok -> **CONFIRMED**
- N1-4 (descriptive) rho = 0.5: gap high -11.8%, mid -10.9%, low -10.3% -> increases with falling detectability
- N1-4 (descriptive) rho = 0.0: gap high -3.5%, mid -0.9%, low +0.5% -> increases with falling detectability