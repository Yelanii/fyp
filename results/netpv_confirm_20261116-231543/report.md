# Net protection value test (confirm)

Seeds 8100-8119; 64 conditions per seed; 6400 runs; 3268 s.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task |
|---|---|---|---|---|
| never check | 158.4 | 20.1% | 0.2% | 0.00 |
| retrying rule told q, f | 147.4 | 12.9% | 1.2% | 0.44 |
| rule v5 told q, f (gross PV) | 146.3 | 8.9% | 0.1% | 2.13 |
| rule v5 (gross PV, as evaluated so far) | 146.5 | 12.4% | 0.1% | 0.68 |
| rule v5 with net PV (corrected) | 146.8 | 12.9% | 0.1% | 0.52 |

## By wrong-answer cost and degradation level (total loss)

| wrong-answer cost | tool A drops to | v5 (gross) | v5_net (corrected) | difference |
|---|---|---|---|---|
| 1x task | 95% | 120.8 | 120.8 | -0.0% |
| 1x task | 85% | 134.0 | 134.1 | +0.1% |
| 1x task | 75% | 133.9 | 133.8 | -0.1% |
| 1x task | 60% | 132.1 | 132.2 | +0.1% |
| 3x task | 95% | 154.9 | 156.0 | +0.7% |
| 3x task | 85% | 167.3 | 167.9 | +0.3% |
| 3x task | 75% | 167.0 | 167.7 | +0.4% |
| 3x task | 60% | 162.2 | 162.0 | -0.2% |

## Pre-registered hypotheses

- H-P1 corrected rule not worse than the evaluated rule (upper bound of 95% CI <= +1%): 146.8 vs 146.5 (+0.2%, 95% CI -0.0% to +0.4%) -> **CONFIRMED**
- H-P2 corrected rule lower than the evaluated rule: Wilcoxon p = 0.93 over 20 seeds -> **NOT CONFIRMED**
- H-P3 corrected rule within +3% of the retrying rule told q and f (upper bound of 95% CI <= +3%): 146.8 vs 147.4 (-0.4%, 95% CI -0.9% to +0.1%) -> **CONFIRMED**