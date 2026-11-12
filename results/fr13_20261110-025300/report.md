# FR13: gradual drift and cost-weight sensitivity (descriptive, not confirmatory)

1252 s total.

## Part A: gradual-drift scenario (S2_gradual), 20 seeds, descriptive

| Strategy | total loss | leak rate | failed tasks | checks/task |
|---|---|---|---|---|
| never | 148.3 | 25.4% | 0.2% | 0.00 |
| always | 188.8 | 7.1% | 18.6% | 5.94 |
| cusum | 148.9 | 11.7% | 1.6% | 0.55 |
| v4 | 137.6 | 14.5% | 0.3% | 0.12 |
| v5 | 137.4 | 14.3% | 0.1% | 0.12 |
| v5_1 | 137.6 | 14.3% | 0.1% | 0.12 |

Observation (descriptive, not a hypothesis test): Rule_v5_1's mean loss (137.6) vs. the best of the simpler baselines on this scenario (137.4) -- v5_1 is NOT the lowest here. Reported as observed, whichever way it comes out.

## Part B: sensitivity to cost weights (leak_mult x check_frac), S1_sudden, 20 seeds, descriptive

Total loss per task, mean over seeds. Rows: wrong-answer cost (leak_mult, in task-cost units). Columns: check price as a share of mean tool price (check_frac).

### v4

| leak_mult \ check_frac | 0.05 | 0.10 | 0.15 | 0.20 | 0.30 |
|---|---|---|---|---|---|
| 0.5 | 127.3 | 127.4 | 127.6 | 127.7 | 128.0 |
| 1.0 | 135.7 | 135.8 | 136.0 | 136.1 | 136.4 |
| 2.0 | 152.6 | 152.7 | 153.0 | 153.0 | 153.2 |
| 3.0 | 168.5 | 168.1 | 168.4 | 168.5 | 169.6 |
| 5.0 | 188.2 | 191.8 | 192.4 | 194.3 | 198.9 |

### v5

| leak_mult \ check_frac | 0.05 | 0.10 | 0.15 | 0.20 | 0.30 |
|---|---|---|---|---|---|
| 0.5 | 127.0 | 127.0 | 127.2 | 127.4 | 127.6 |
| 1.0 | 135.4 | 135.4 | 135.6 | 135.6 | 136.0 |
| 2.0 | 153.4 | 152.9 | 153.2 | 153.4 | 153.3 |
| 3.0 | 165.6 | 166.3 | 168.4 | 168.9 | 168.8 |
| 5.0 | 179.3 | 184.6 | 187.3 | 192.8 | 196.8 |

### v5_1

| leak_mult \ check_frac | 0.05 | 0.10 | 0.15 | 0.20 | 0.30 |
|---|---|---|---|---|---|
| 0.5 | 127.1 | 127.1 | 127.3 | 127.5 | 127.7 |
| 1.0 | 135.9 | 135.6 | 135.7 | 135.8 | 136.1 |
| 2.0 | 155.1 | 153.9 | 154.0 | 153.8 | 153.5 |
| 3.0 | 168.4 | 168.4 | 169.7 | 169.8 | 169.3 |
| 5.0 | 183.3 | 188.8 | 190.4 | 195.1 | 198.1 |

Cells where v5_1's mean loss is NOT below v4's (reported as a limit, not omitted): [(1.0, 0.05), (2.0, 0.05), (2.0, 0.1), (2.0, 0.15), (2.0, 0.2), (2.0, 0.3), (3.0, 0.1), (3.0, 0.15), (3.0, 0.2), (5.0, 0.2)].