# FreshQA with real judges (confirm): seeds 8600-8619; judges phi4-mini@plain, llama3.1:8b@plain

3360 runs; 4017 s. Conditions per seed and judge: stream {news, mixed} x tool A goes stale in {100, 50, 25}% of runs x price of tool B {24, 30} (A costs 20). Wrong answer = 3 tasks. Metric: total loss per task.

| Strategy | all | stale 100% | 50% | 25% | B at 24 | B at 30 | news | mixed | wrong kept | failed | checks/task |
|---|---|---|---|---|---|---|---|---|---|---|---|
| never | 214.1 | 273.8 | 227.7 | 140.7 | 205.9 | 222.2 | 250.2 | 178.0 | 27.1% | 0.1% | 0.00 |
| use_B | 142.4 | 142.4 | 142.4 | 142.4 | 126.6 | 158.3 | 142.4 | 142.4 | 0.0% | 0.2% | 0.00 |
| always_x | 257.6 | 273.7 | 260.9 | 238.1 | 239.8 | 275.4 | 281.9 | 233.2 | 5.3% | 0.4% | 5.41 |
| v4 | 163.6 | 173.6 | 164.3 | 152.9 | 148.8 | 178.3 | 164.2 | 163.0 | 3.4% | 5.7% | 0.20 |
| v5 | 159.6 | 170.2 | 161.8 | 146.8 | 146.4 | 172.7 | 162.6 | 156.6 | 3.9% | 0.1% | 0.13 |
| rho_cap | 160.0 | 170.4 | 163.6 | 146.0 | 148.8 | 171.2 | 163.0 | 157.0 | 3.8% | 0.1% | 0.16 |
| rho_noaudit | 157.2 | 166.8 | 160.1 | 144.6 | 145.6 | 168.7 | 157.8 | 156.6 | 3.2% | 0.1% | 0.13 |

## Pre-registered hypotheses (PREREGISTRATION_freshqa.md)

- H-F1 rho_cap below use_B: 160.0 vs 142.4 (+12.3%, 95% CI +8.4% to +16.3%), Wilcoxon p = 1 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-F2 rho_cap below never: 160.0 vs 214.1 (-25.3%, 95% CI -29.8% to -20.2%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-F3 rho_cap below v5: 160.0 vs 159.6 (+0.3%, 95% CI -4.0% to +4.3%), Wilcoxon p = 0.71 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-F4 (secondary) where tool A goes stale in only 25% of runs, rho_cap below use_B: 146.0 vs 142.4 (+2.5%, 95% CI -3.2% to +7.9%), p = 0.86 -> **NOT CONFIRMED**

## Per judge (descriptive)

| Judge | never | use_B | always_x | v4 | v5 | rho_cap | rho_noaudit |
|---|---|---|---|---|---|---|---|
| phi4-mini@plain | 214.1 | 142.4 | 259.2 | 163.2 | 161.4 | 160.5 | 157.4 |
| llama3.1:8b@plain | 214.1 | 142.4 | 256.0 | 164.0 | 157.7 | 159.5 | 157.0 |

## rho_cap vs use_B by cell (descriptive; negative = the rule is cheaper)

| stream | stale in | B price | rule | use_B | diff |
|---|---|---|---|---|---|
| news | 100% | 24 | 160.9 | 126.6 | +27.1% |
| news | 100% | 30 | 190.0 | 158.3 | +20.0% |
| news | 50% | 24 | 153.3 | 126.6 | +21.1% |
| news | 50% | 30 | 181.2 | 158.3 | +14.5% |
| news | 25% | 24 | 141.2 | 126.6 | +11.5% |
| news | 25% | 30 | 151.4 | 158.3 | -4.3% |
| mixed | 100% | 24 | 149.1 | 126.6 | +17.8% |
| mixed | 100% | 30 | 181.8 | 158.3 | +14.9% |
| mixed | 50% | 24 | 148.0 | 126.6 | +16.9% |
| mixed | 50% | 30 | 172.0 | 158.3 | +8.7% |
| mixed | 25% | 24 | 140.4 | 126.6 | +10.9% |
| mixed | 25% | 30 | 150.8 | 158.3 | -4.7% |