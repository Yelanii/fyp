# Part C: cross-check comparisons that are sometimes wrong (pre-registered stress test)

Seeds 8220-8229; q 0.95, pi 1, drop {85, 75}%, leak {1, 3}, f {0.05, 0.15}; 779 s.

| e (comparison error) | v4 | always_x | v5 | v5 vs v4 | v5 median learned f |
|---|---|---|---|---|---|
| 0 | 152.5 | 156.3 | 149.0 | -2.3% | 0.120 |
| 0.1 | 152.5 | 163.3 | 149.7 | -1.8% | 0.122 |
| 0.2 | 152.5 | 169.8 | 150.6 | -1.2% | 0.119 |

- H-C1 at e = 0.1, v5 below v4: 149.7 vs 152.5, p = 0.00098 over 10 seeds -> CONFIRMED