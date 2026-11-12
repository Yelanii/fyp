# Part E3: persistence with real checkers (planner qwen2.5:1.5b; seeds 4000-4009)

Total loss per task (spend + leak loss x leaks + one task cost x failed tasks), mean over drop {85, 75}% x leak {1, 3} x seeds:

| Checker | T | f told | never | always | v4 | v4_ind | always: failed tasks | in-loop re-flag after a false alarm |
|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b | 0 | 0.143 | 82.3 | 107.2 | 76.3 | 79.8 | 31.0% | 1.000 (2867/2867) |
| qwen2.5:1.5b | 0.7 | 0.149 | 82.3 | 106.6 | 76.3 | 78.5 | 26.7% | 0.920 (2552/2774) |
| qwen2.5:3b | 0 | 0.050 | 82.3 | 94.7 | 75.8 | 82.1 | 17.6% | 1.000 (2124/2124) |
| qwen2.5:3b | 0.7 | 0.057 | 82.3 | 96.6 | 75.7 | 82.4 | 17.2% | 0.825 (2123/2573) |

## Pre-registered checks (PREREGISTRATION_persistence.md, part E3)
- R-E3a (T = 0, both checkers pooled, 80 pairs): v4 76.1 vs v4_ind 81.0 (-6.1%), p = 3.2e-12 -> MET
- R-E3b (T = 0.7, both checkers pooled, 80 pairs): v4 76.0 vs v4_ind 80.4 (-5.5%), p = 1.6e-12 -> MET