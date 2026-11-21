# Exact step-cost test (confirm)

Seeds 9300-9319; 64 conditions per seed; 5120 runs; 4159 s.
Runs in which the two rules gave exactly the same loss: 4.7%.

| Strategy | total loss | wrong answers kept | failed tasks | checks/task |
|---|---|---|---|---|
| never check | 162.2 | 21.6% | 0.2% | 0.00 |
| retrying rule told q, f | 147.6 | 12.9% | 1.3% | 0.48 |
| rule as evaluated (c/p step cost) | 146.5 | 13.1% | 0.1% | 0.57 |
| rule with exact step cost | 146.4 | 11.4% | 0.1% | 1.31 |

## By wrong-answer cost and degradation level (total loss)

| wrong-answer cost | tool A drops to | as evaluated | exact step cost | difference |
|---|---|---|---|---|
| 1x task | 95% | 119.4 | 120.5 | +1.0% |
| 1x task | 85% | 130.8 | 131.4 | +0.4% |
| 1x task | 75% | 134.2 | 134.7 | +0.4% |
| 1x task | 60% | 135.9 | 136.5 | +0.4% |
| 3x task | 95% | 153.8 | 152.7 | -0.7% |
| 3x task | 85% | 161.6 | 163.3 | +1.1% |
| 3x task | 75% | 168.1 | 163.7 | -2.6% |
| 3x task | 60% | 168.6 | 168.6 | +0.0% |

## Pre-registered hypotheses

- H-E1 the approximation costs at most 1% (95% CI of exact vs evaluated within -1% to +1%): 146.4 vs 146.5 (-0.07%, 95% CI -0.51% to +0.33%) -> **CONFIRMED**
- H-E2 (descriptive) two-sided Wilcoxon over 20 seeds, exact vs evaluated: p = 0.78
- H-E3 the exact variant within +3% of the retrying rule told q and f (upper bound <= +3%): 146.4 vs 147.6 (-0.8%, 95% CI -1.5% to -0.2%) -> **CONFIRMED**