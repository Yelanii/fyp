# Rule v5 with real checkers (planner qwen2.5:1.5b; seeds 4100-4109)

Cache misses: {'qwen2.5:1.5b|T=0': 0, 'qwen2.5:1.5b|T=0.7': 0, 'qwen2.5:3b|T=0': 0, 'qwen2.5:3b|T=0.7': 0}

Total loss per task, mean over drop {85, 75}% x leak {1, 3} x seeds:

| Checker | T | calibrated f | never | always_x | v4 | v5_told | v5 | v5 learned f (median) | v5 failed tasks | v4 failed tasks | v5 leak | v4 leak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b | 0 | 0.143 | 83.6 | 88.4 | 76.1 | 77.2 | 75.3 | 0.171 | 0.0% | 0.9% | 8.2% | 9.2% |
| qwen2.5:1.5b | 0.7 | 0.149 | 83.6 | 88.7 | 76.1 | 76.8 | 75.3 | 0.201 | 0.0% | 0.9% | 8.2% | 9.2% |
| qwen2.5:3b | 0 | 0.050 | 83.6 | 83.4 | 75.8 | 75.8 | 75.2 | 0.139 | 0.0% | 1.3% | 8.3% | 8.1% |
| qwen2.5:3b | 0.7 | 0.057 | 83.6 | 85.5 | 75.2 | 77.2 | 75.4 | 0.168 | 0.0% | 1.0% | 8.4% | 8.1% |

## Pre-registered checks (PREREGISTRATION_v5.md, real-checker pilot)
- R-V1 v5 below v4: 75.3 vs 75.8 (-0.7%); 160 pairs p = 0.00089; per seed 8 of 10 lower, p = 0.032 -> MET
- R-V2 v5's learned f within 0.05 of the calibrated f: median error 0.080 -> NOT MET