# Rule v5 with real checkers (planner qwen2.5:1.5b; seeds 4300-4309)

Cache misses: {'qwen2.5:1.5b|T=0': 0, 'qwen2.5:1.5b|T=0.7': 0, 'qwen2.5:3b|T=0': 0, 'qwen2.5:3b|T=0.7': 0}

Total loss per task, mean over drop {85, 75}% x leak {1, 3} x seeds:

| Checker | T | calibrated f | never | always_x | v4 | v5_told | v5 | v5 learned f (median) | v5 failed tasks | v4 failed tasks | v5 leak | v4 leak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b | 0 | 0.143 | 79.7 | 86.7 | 75.9 | 75.7 | 74.7 | 0.195 | 0.1% | 0.6% | 8.6% | 9.5% |
| qwen2.5:1.5b | 0.7 | 0.149 | 79.7 | 88.1 | 75.9 | 76.1 | 74.8 | 0.191 | 0.1% | 0.7% | 9.0% | 9.2% |
| qwen2.5:3b | 0 | 0.050 | 79.7 | 82.3 | 75.6 | 75.8 | 74.9 | 0.132 | 0.1% | 1.7% | 8.7% | 7.5% |
| qwen2.5:3b | 0.7 | 0.057 | 79.7 | 84.1 | 75.7 | 76.5 | 75.0 | 0.190 | 0.1% | 1.3% | 8.8% | 8.1% |

## Pre-registered checks (PREREGISTRATION_v5.md, real-checker pilot)
- R-V1 v5 below v4: 74.8 vs 75.8 (-1.2%); 160 pairs p = 0.014; per seed 7 of 10 lower, p = 0.08 -> NOT MET
- R-V2 v5's learned f within 0.05 of the calibrated f: median error 0.067 -> NOT MET