# FR20 confirmatory test: pre-registered test

Seeds 9000-9019; 7680 runs; 25526 s. Unit of analysis: the seed. Metric: total loss per task.

## Primary conditions (true rho in {0.0, 0.1, 0.3}; old fixed belief = 0.5, wrong)

| Strategy | total loss | leak rate | checks/task |
|---|---|---|---|
| fixed | 152.5 | 37.8% | 0.11 |
| told | 146.3 | 18.6% | 0.34 |
| rho_cap | 145.8 | 25.6% | 0.47 |
| rho_mean | 145.8 | 25.6% | 0.47 |
| rho_lcb | 149.4 | 22.5% | 0.56 |
| rho_noaudit | 146.6 | 28.8% | 0.22 |

## Sanity conditions (true rho = 0.5; the old belief happened to be right) -- descriptive only

| Strategy | total loss |
|---|---|
| fixed | 131.6 |
| told | 131.6 |
| rho_cap | 134.2 |
| rho_mean | 134.2 |
| rho_lcb | 139.4 |
| rho_noaudit | 133.8 |

## Pre-registered hypotheses (PREREGISTRATION_rho.md)
- H-R1 rho_cap below fixed (wrong, constant 0.5): 145.8 vs 152.5 (-4.4%, 95% CI -5.2% to -3.6%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-R2 rho_cap within 5% of told (oracle): 145.8 vs 146.3 (-0.4%, 95% CI upper +0.6%) -> CONFIRMED

## H-R3 (descriptive): ranked mean loss of the four rho-learning modes, primary conditions
- rho_cap: 145.8
- rho_mean: 145.8
- rho_noaudit: 146.6
- rho_lcb: 149.4

## H-R4 (descriptive): rho_cap's learned rho_hat, median |rho_hat - true rho| = 0.106

## Sanity check: at true rho = 0.5 (old belief correct), rho_cap vs fixed differ by 2.0% of fixed's loss (134.2 vs 131.6) -- expected small, descriptive only