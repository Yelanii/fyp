# Confirmatory test of rule v4 (pre-registered B)

Seeds 1200-1219; 5760 runs; 1396 s. Metric: total loss incl. one task cost per failed task.

| f | Leak | never | always | cusum | v2 | v3 | v4 |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 133.1 | 137.1 | 129.1 | 131.0 | 130.0 | 130.1 |
| 0 | 3 | 182.2 | 144.1 | 160.7 | 143.6 | 146.1 | 145.9 |
| 0.05 | 1 | 133.1 | 170.0 | 136.3 | 158.5 | 153.2 | 129.6 |
| 0.05 | 3 | 182.2 | 175.7 | 164.4 | 179.1 | 178.5 | 169.2 |
| 0.15 | 1 | 133.1 | 203.3 | 148.7 | 189.1 | 182.8 | 130.8 |
| 0.15 | 3 | 182.2 | 211.3 | 177.7 | 217.3 | 216.4 | 162.4 |

## Pre-registered hypotheses
- H-v4a (f > 0) v4 < v3 by >= 5%: 148.0 vs 182.7 (-19.0%), p = 1.2e-98 -> CONFIRMED
- H-v4b (f > 0) v4 below never, always and CUSUM: never 157.6 (p = 5e-27); always 190.1 (p = 4.1e-99); cusum 156.8 (p = 2.8e-47) vs v4 148.0 -> CONFIRMED
- H-v4c (f = 0) v4 within 1% of v3: 138.0 vs 138.1 (-0.1%) -> CONFIRMED

Per condition with f > 0 (v4 minus best of never/always/CUSUM, %):

- drop 95%, leak 1: v4 119.8 vs best baseline never 116.9 (+2.5%)
- drop 95%, leak 3: v4 155.7 vs best baseline never 145.6 (+7.0%)
- drop 85%, leak 1: v4 134.4 vs best baseline never 136.8 (-1.8%)
- drop 85%, leak 3: v4 170.2 vs best baseline cusum 174.3 (-2.4%)
- drop 75%, leak 1: v4 132.9 vs best baseline never 142.5 (-6.7%)
- drop 75%, leak 3: v4 171.0 vs best baseline cusum 174.0 (-1.7%)
- drop 60%, leak 1: v4 133.8 vs best baseline never 136.2 (-1.8%)
- drop 60%, leak 3: v4 166.2 vs best baseline cusum 175.7 (-5.4%)