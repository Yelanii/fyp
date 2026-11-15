# S1 robustness: cross-check assumptions broken (confirm), seeds 6100-6119

10800 runs; 4478 s. Cell = mean total loss per task of v5 / change vs v4 without labels / change vs v4 told.

### only A degrades (reference)

| sigma \ e | e = 0.0 | e = 0.1 | e = 0.2 |
|---|---|---|---|
| 0.0 | 146.6 / -22.9% / -1.3% | 148.1 / -22.1% / -0.3% | 150.8 / -20.7% / +1.5% |
| 0.5 | 146.6 / -22.9% / -1.3% | 148.1 / -22.1% / -0.3% | 150.9 / -20.7% / +1.5% |
| 0.9 | 146.5 / -22.9% / -1.4% | 148.0 / -22.2% / -0.4% | 150.4 / -20.9% / +1.2% |

### A and B degrade independently

| sigma \ e | e = 0.0 | e = 0.1 | e = 0.2 |
|---|---|---|---|
| 0.0 | 157.5 / -21.8% / -0.2% | 158.5 / -21.3% / +0.5% | 157.4 / -21.9% / -0.2% |
| 0.5 | 157.5 / -21.8% / -0.2% | 158.4 / -21.3% / +0.4% | 157.4 / -21.9% / -0.2% |
| 0.9 | 157.3 / -21.9% / -0.3% | 158.2 / -21.5% / +0.3% | 157.4 / -21.9% / -0.2% |

### A and B degrade together (shared cause)

| sigma \ e | e = 0.0 | e = 0.1 | e = 0.2 |
|---|---|---|---|
| 0.0 | 166.1 / -20.5% / -0.4% | 166.9 / -20.1% / +0.1% | 167.8 / -19.6% / +0.6% |
| 0.5 | 166.0 / -20.5% / -0.5% | 166.7 / -20.2% / -0.1% | 167.6 / -19.7% / +0.5% |
| 0.9 | 166.0 / -20.5% / -0.5% | 166.7 / -20.2% / -0.1% | 167.6 / -19.7% / +0.5% |

Loss of cross-check every call (always_x), two-tool scenarios, by sigma at e = 0: sigma 0.0: 203.7, sigma 0.5: 203.7, sigma 0.9: 203.7

Median learned f, two-tool scenarios (true f = 0.15):

| sigma \ e | e = 0.0 | e = 0.1 | e = 0.2 |
|---|---|---|---|
| 0.0 | 0.194 | 0.188 | 0.180 |
| 0.5 | 0.192 | 0.188 | 0.182 |
| 0.9 | 0.196 | 0.191 | 0.182 |

| Strategy | all cells |
|---|---|
| never | 182.1 |
| v4 | 157.7 |
| v4_nocal | 200.1 |
| always_x | 199.3 |
| v5 | 157.7 |

## Pre-registered hypotheses (PREREGISTRATION_robustness.md)

- H-S1 v5 at sigma 0.9 within +2% of sigma 0 (e = 0): 161.6 vs 161.8 (-0.1%, 95% CI -0.2% to +0.0%) -> **CONFIRMED**
- H-S2 worst cell, v5 below v4 without labels: 162.5 vs 205.1 (-20.8%, 95% CI -22.5% to -18.8%), p = 9.5e-07 -> **CONFIRMED**
- H-S3 worst cell, v5 within +3% of v4 told: 162.5 vs 162.3 (+0.1%, 95% CI -0.6% to +0.9%) -> **CONFIRMED**