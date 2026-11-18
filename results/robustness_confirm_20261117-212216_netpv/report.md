# S1 robustness: cross-check assumptions broken (confirm), seeds 8500-8519

10800 runs; 10308 s. Cell = mean total loss per task of v5 / change vs v4 without labels / change vs v4 told.

### only A degrades (reference)

| sigma \ e | e = 0.0 | e = 0.1 | e = 0.2 |
|---|---|---|---|
| 0.0 | 150.7 / -21.5% / -0.9% | 150.5 / -21.6% / -1.1% | 152.2 / -20.7% / +0.1% |
| 0.5 | 150.7 / -21.5% / -0.9% | 150.5 / -21.6% / -1.1% | 152.2 / -20.7% / +0.1% |
| 0.9 | 150.7 / -21.5% / -0.9% | 150.5 / -21.6% / -1.1% | 152.2 / -20.7% / +0.1% |

### A and B degrade independently

| sigma \ e | e = 0.0 | e = 0.1 | e = 0.2 |
|---|---|---|---|
| 0.0 | 157.4 / -21.0% / -3.0% | 159.2 / -20.0% / -1.8% | 159.3 / -20.0% / -1.7% |
| 0.5 | 157.6 / -20.9% / -2.8% | 159.2 / -20.0% / -1.8% | 159.3 / -20.0% / -1.7% |
| 0.9 | 157.6 / -20.9% / -2.8% | 159.2 / -20.0% / -1.8% | 159.3 / -20.0% / -1.7% |

### A and B degrade together (shared cause)

| sigma \ e | e = 0.0 | e = 0.1 | e = 0.2 |
|---|---|---|---|
| 0.0 | 165.5 / -19.5% / -1.5% | 167.4 / -18.5% / -0.3% | 169.7 / -17.4% / +1.0% |
| 0.5 | 165.4 / -19.5% / -1.5% | 167.4 / -18.6% / -0.4% | 169.9 / -17.3% / +1.1% |
| 0.9 | 165.3 / -19.6% / -1.6% | 167.2 / -18.6% / -0.5% | 169.4 / -17.5% / +0.9% |

Loss of cross-check every call (always_x), two-tool scenarios, by sigma at e = 0: sigma 0.0: 200.1, sigma 0.5: 199.8, sigma 0.9: 199.7

Median learned f, two-tool scenarios (true f = 0.15):

| sigma \ e | e = 0.0 | e = 0.1 | e = 0.2 |
|---|---|---|---|
| 0.0 | 0.163 | 0.168 | 0.167 |
| 0.5 | 0.163 | 0.169 | 0.169 |
| 0.9 | 0.166 | 0.169 | 0.169 |

| Strategy | all cells |
|---|---|
| never | 181.2 |
| v4 | 160.7 |
| v4_nocal | 198.8 |
| always_x | 199.5 |
| v5 | 159.1 |

## Pre-registered hypotheses (PREREGISTRATION_robustness.md)

- H-S1 v5 at sigma 0.9 within +2% of sigma 0 (e = 0): 161.4 vs 161.4 (+0.0%, 95% CI -0.1% to +0.1%) -> **CONFIRMED**
- H-S2 worst cell, v5 below v4 without labels: 164.4 vs 202.3 (-18.7%, 95% CI -20.3% to -17.0%), p = 9.5e-07 -> **CONFIRMED**
- H-S3 worst cell, v5 within +3% of v4 told: 164.4 vs 165.1 (-0.4%, 95% CI -1.3% to +0.6%) -> **CONFIRMED**