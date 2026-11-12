# Part C: cross-check comparisons that are sometimes wrong (pre-registered stress test)

Seeds 1720-1729; q 0.95, pi 1, drop {85, 75}%, leak {1, 3}, f {0.05, 0.15}; 202 s.

| e (comparison error) | v4 | always_x | v5 | v5 vs v4 | v5 median learned f |
|---|---|---|---|---|---|
| 0 | 151.2 | 156.0 | 148.5 | -1.8% | 0.124 |
| 0.1 | 151.2 | 163.5 | 150.4 | -0.5% | 0.119 |
| 0.2 | 151.2 | 170.8 | 151.2 | -0.0% | 0.120 |

- H-C1 at e = 0.1, v5 below v4: 150.4 vs 151.2, p = 0.38 over 10 seeds -> NOT CONFIRMED