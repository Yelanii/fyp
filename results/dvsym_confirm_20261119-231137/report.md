# Decision-value symmetry test (confirm)

Seeds 9100-9119; 64 conditions per seed; 5120 runs; 2406 s.
Runs in which the two rules gave exactly the same loss: 4.2%.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task |
|---|---|---|---|---|
| never check | 159.2 | 20.3% | 0.3% | 0.00 |
| retrying rule told q, f | 146.3 | 12.4% | 1.3% | 0.46 |
| rule as evaluated (DV asymmetric) | 145.3 | 12.3% | 0.1% | 0.52 |
| rule with symmetric DV | 145.6 | 10.8% | 0.1% | 1.27 |

## By wrong-answer cost and degradation level (total loss)

| wrong-answer cost | tool A drops to | as evaluated | symmetric DV | difference |
|---|---|---|---|---|
| 1x task | 95% | 116.8 | 118.2 | +1.2% |
| 1x task | 85% | 132.3 | 132.9 | +0.4% |
| 1x task | 75% | 133.1 | 133.4 | +0.3% |
| 1x task | 60% | 134.4 | 134.9 | +0.4% |
| 3x task | 95% | 150.9 | 150.9 | +0.1% |
| 3x task | 85% | 162.2 | 163.8 | +1.0% |
| 3x task | 75% | 165.2 | 164.5 | -0.4% |
| 3x task | 60% | 167.6 | 166.1 | -0.9% |

## Pre-registered hypotheses

- H-D1 the asymmetry costs at most 1% (95% CI of symmetric vs evaluated within -1% to +1%): 145.6 vs 145.3 (+0.21%, 95% CI -0.40% to +0.79%) -> **CONFIRMED**
- H-D2 (descriptive) two-sided Wilcoxon over 20 seeds, symmetric vs evaluated: p = 0.39
- H-D3 the evaluated rule within +3% of the retrying rule told q and f (upper bound <= +3%): 145.3 vs 146.3 (-0.6%, 95% CI -1.1% to -0.2%) -> **CONFIRMED**