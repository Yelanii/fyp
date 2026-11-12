# Real-agent validation (qwen2.5:1.5b)

Tasks kept: 100; judge catch rate obvious 0.98, subtle 1.00, false alarms 0.14; strategies told q = 0.98. Judge used: recompute.

Total loss per task (Amendment 2: spend + leak loss x leaks + one task cost x failed tasks):

| Drop | Leak loss | never | always | cusum | v2 | v3 | v4 |
|---|---|---|---|---|---|---|---|
| 85% | 1 | 67.6 | 107.7 | 76.0 | 82.4 | 74.3 | 68.6 |
| 85% | 3 | 86.0 | 107.8 | 82.8 | 107.9 | 97.7 | 77.8 |
| 75% | 1 | 74.1 | 110.0 | 78.0 | 81.5 | 74.8 | 70.2 |
| 75% | 3 | 100.1 | 110.2 | 84.8 | 109.1 | 98.8 | 78.6 |

Same runs, pre-registered metric (failed tasks cost nothing extra):

| Drop | Leak loss | never | always | cusum | v2 | v3 | v4 |
|---|---|---|---|---|---|---|---|
| 85% | 1 | 67.6 | 88.2 | 74.1 | 77.9 | 72.6 | 68.0 |
| 85% | 3 | 86.0 | 88.4 | 80.9 | 89.7 | 85.5 | 77.2 |
| 75% | 1 | 73.9 | 90.2 | 76.0 | 77.3 | 73.1 | 69.6 |
| 75% | 3 | 100.0 | 90.3 | 82.8 | 90.8 | 86.6 | 78.1 |

Share of tasks: leaked (silent wrong answer) / failed (known failure), pooled:

- never: leaked 16.4%, failed 0.1%
- always: leaked 0.1%, failed 28.9%
- cusum: leaked 5.1%, failed 2.9%
- v2: leaked 2.4%, failed 16.7%
- v3: leaked 3.3%, failed 10.4%
- v4: leaked 8.3%, failed 0.8%

## Pre-registered checks
- R1 judge catches subtle less than obvious: 1.00 vs 0.98 -> not met
- R2 v3 < v2: mean 86.4 vs 95.2, p = 9.02e-06 -> met
- R3 v3 below always and never: 86.4 vs 108.9 and 82.0 -> not met
- R4 always worse than never in >= 2 of 4 conditions: 4 of 4 -> met

## Pre-registered checks for rule v4 (PREREGISTRATION_falsealarm.md, part C)
- R5 v4 (73.8) below every other strategy: never 82.0 p = 5.6e-06; always 108.9 p = 9.1e-13; cusum 80.4 p = 6.1e-07; v2 95.2 p = 1.8e-12; v3 86.4 p = 4.9e-10 -> met
- R6 v4 below never-check in >= 3 of 4 conditions: 3 of 4 -> met
- Seeds 3000-3009