# FreshQA with real judges (confirm): seeds 2700-2719; judges phi4-mini@plain, llama3.1:8b@plain

3360 runs; 1016 s. Conditions per seed and judge: stream {news, mixed} x tool A goes stale in {100, 50, 25}% of runs x price of tool B {24, 30} (A costs 20). Wrong answer = 3 tasks. Metric: total loss per task.

| Strategy | all | stale 100% | 50% | 25% | B at 24 | B at 30 | news | mixed | wrong kept | failed | checks/task |
|---|---|---|---|---|---|---|---|---|---|---|---|
| never | 194.1 | 276.3 | 180.4 | 125.7 | 187.5 | 200.8 | 221.3 | 167.0 | 22.2% | 0.1% | 0.00 |
| use_B | 142.4 | 142.4 | 142.4 | 142.4 | 126.6 | 158.2 | 142.4 | 142.4 | 0.0% | 0.0% | 0.00 |
| always_x | 254.8 | 275.7 | 252.0 | 236.7 | 237.5 | 272.0 | 276.7 | 232.8 | 4.7% | 0.3% | 5.42 |
| v4 | 156.8 | 169.3 | 156.6 | 144.4 | 141.0 | 172.5 | 159.3 | 154.3 | 3.1% | 5.1% | 0.18 |
| v5 | 152.3 | 173.5 | 150.4 | 132.9 | 135.8 | 168.8 | 156.6 | 147.9 | 4.5% | 0.0% | 0.13 |
| rho_cap | 154.5 | 168.5 | 154.6 | 140.5 | 140.7 | 168.3 | 158.4 | 150.7 | 3.8% | 0.0% | 0.15 |
| rho_noaudit | 154.0 | 167.6 | 154.2 | 140.3 | 140.0 | 168.0 | 158.1 | 150.0 | 3.7% | 0.0% | 0.14 |

## Pre-registered hypotheses (PREREGISTRATION_freshqa.md)

- H-F1 rho_cap below use_B: 154.5 vs 142.4 (+8.5%, 95% CI +4.1% to +13.2%), Wilcoxon p = 1 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-F2 rho_cap below never: 154.5 vs 194.1 (-20.4%, 95% CI -24.3% to -16.6%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-F3 rho_cap below v5: 154.5 vs 152.3 (+1.5%, 95% CI -1.1% to +4.2%), Wilcoxon p = 0.91 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-F4 (secondary) where tool A goes stale in only 25% of runs, rho_cap below use_B: 140.5 vs 142.4 (-1.3%, 95% CI -5.9% to +3.7%), p = 0.27 -> **NOT CONFIRMED**

## Per judge (descriptive)

| Judge | never | use_B | always_x | v4 | v5 | rho_cap | rho_noaudit |
|---|---|---|---|---|---|---|---|
| phi4-mini@plain | 194.1 | 142.4 | 255.4 | 156.9 | 152.5 | 154.0 | 153.6 |
| llama3.1:8b@plain | 194.1 | 142.4 | 254.1 | 156.7 | 152.1 | 155.1 | 154.4 |

## rho_cap vs use_B by cell (descriptive; negative = the rule is cheaper)

| stream | stale in | B price | rule | use_B | diff |
|---|---|---|---|---|---|
| news | 100% | 24 | 156.8 | 126.6 | +23.9% |
| news | 100% | 30 | 195.8 | 158.2 | +23.7% |
| news | 50% | 24 | 139.6 | 126.6 | +10.3% |
| news | 50% | 30 | 168.7 | 158.2 | +6.6% |
| news | 25% | 24 | 136.4 | 126.6 | +7.8% |
| news | 25% | 30 | 153.0 | 158.2 | -3.3% |
| mixed | 100% | 24 | 141.1 | 126.6 | +11.5% |
| mixed | 100% | 30 | 180.2 | 158.2 | +13.9% |
| mixed | 50% | 24 | 139.3 | 126.6 | +10.1% |
| mixed | 50% | 30 | 170.7 | 158.2 | +7.9% |
| mixed | 25% | 24 | 131.2 | 126.6 | +3.6% |
| mixed | 25% | 30 | 141.6 | 158.2 | -10.5% |