# Rule v5 with real checkers (planner qwen2.5:1.5b; seeds 4000-4009)

**REPLAY PREVIEW** from saved answers; answers missing from the cache count as no alarm. Cache misses: {'qwen2.5:1.5b|T=0': 58, 'qwen2.5:1.5b|T=0.7': 434, 'qwen2.5:3b|T=0': 44, 'qwen2.5:3b|T=0.7': 403}

Total loss per task, mean over drop {85, 75}% x leak {1, 3} x seeds:

| Checker | T | calibrated f | never | always_x | v4 | v5_told | v5 | v5 learned f (median) | v5 failed tasks | v4 failed tasks | v5 leak | v4 leak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b | 0 | 0.143 | 82.3 | 86.9 | 76.3 | 76.9 | 75.5 | 0.166 | 0.1% | 0.8% | 8.8% | 10.0% |
| qwen2.5:1.5b | 0.7 | 0.149 | 82.3 | 87.8 | 76.3 | 77.4 | 75.8 | 0.174 | 0.1% | 0.6% | 8.8% | 10.2% |
| qwen2.5:3b | 0 | 0.050 | 82.3 | 81.6 | 75.8 | 76.7 | 75.3 | 0.116 | 0.1% | 1.3% | 8.5% | 8.8% |
| qwen2.5:3b | 0.7 | 0.057 | 82.3 | 84.7 | 75.7 | 78.0 | 75.5 | 0.147 | 0.1% | 1.0% | 8.8% | 8.6% |

## Pre-registered checks (PREREGISTRATION_v5.md, real-checker pilot)
- R-V1 v5 below v4: 75.5 vs 76.0 (-0.6%); 160 pairs p = 0.0043; per seed 6 of 10 lower, p = 0.22 -> NOT MET
- R-V2 v5's learned f within 0.05 of the calibrated f: median error 0.041 -> MET