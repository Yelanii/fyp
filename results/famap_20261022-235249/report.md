# Check-worth map with false alarms (pre-registered A)

Seeds 1300-1309; 4200 runs; 710 s. Metric: total loss incl. one task cost per failed task.
Median saving of the best checking strategy vs never checking (%), by drop:

| Leak | f | 95% | 90% | 85% | 80% | 75% | 70% | 60% |
|---|---|---|---|---|---|---|---|---|
| 1 | 0 | -1.6 | -0.6 | +2.7 | +7.1 | +7.5 | +6.9 | +3.5 |
| 1 | 0.05 | -3.0 | -0.4 | +1.6 | +6.1 | +6.9 | +6.6 | +2.4 |
| 1 | 0.15 | -4.4 | -1.1 | +0.7 | +6.0 | +5.9 | +5.6 | +1.8 |
| 3 | 0 | +7.3 | +22.7 | +28.1 | +30.1 | +29.3 | +23.6 | +19.3 |
| 3 | 0.05 | -8.3 | +7.8 | +17.3 | +23.3 | +20.3 | +16.8 | +8.8 |
| 3 | 0.15 | -9.9 | +6.2 | +14.0 | +21.8 | +21.1 | +16.4 | +6.9 |

## Pre-registered hypotheses
- H-FA1 hump survives at f = 0.05, leak 3: peak at 80% (+23.3%), 95% -8.3%, 60% +8.8% -> CONFIRMED
- H-FA2 false alarms shrink the value of checking (f = 0.15 vs 0, both leak levels) -> CONFIRMED

Which strategy is cheapest per cell (count):

- f = 0: cusum 9, v2 8, always 5, never 4, v4 2
- f = 0.05: v4 13, cusum 7, never 6, always 2
- f = 0.15: v4 22, never 6