# FreshQA-grounded feasibility check (EXPLORATORY, not pre-registered)

Seeds 2300-2309; real FreshQA staleness (Nov 2025 -> Apr 2026); simulated checker q 0.95, f 0.15, repeating; wrong answer = 3 tasks; 160 runs; 74 s.

| Strategy | news (fast-changing) loss | mixed (all types) loss | news (fast-changing) vs never | mixed (all types) vs never | wrong answers kept (news) | failed tasks (news) | switches (news) |
|---|---|---|---|---|---|---|---|
| never | 348.5 | 266.9 | +0.0% | +0.0% | 66.7% | 0.0% | 0.0 |
| always | 208.5 | 209.1 | -40.2% | -21.6% | 1.3% | 54.7% | 4.4 |
| cusum | 208.8 | 195.6 | -40.1% | -26.7% | 20.2% | 5.7% | 3.8 |
| v4 | 328.6 | 231.1 | -5.7% | -13.4% | 60.1% | 1.9% | 0.1 |
| always_x | 170.5 | 173.9 | -51.1% | -34.8% | 3.1% | 0.0% | 1.0 |
| v5 | 190.7 | 171.0 | -45.3% | -35.9% | 14.6% | 0.0% | 1.2 |
| v5_1_noaudit | 211.3 | 174.4 | -39.4% | -34.7% | 20.5% | 0.0% | 1.5 |
| v5_1 | 204.9 | 171.8 | -41.2% | -35.6% | 18.2% | 0.0% | 1.3 |