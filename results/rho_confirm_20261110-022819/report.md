# FR20 confirmatory test: pre-registered test

Seeds 1900-1919; 7680 runs; 6371 s. Unit of analysis: the seed. Metric: total loss per task.

## Primary conditions (true rho in {0.0, 0.1, 0.3}; old fixed belief = 0.5, wrong)

| Strategy | total loss | leak rate | checks/task |
|---|---|---|---|
| fixed | 150.4 | 35.6% | 0.15 |
| told | 147.4 | 17.7% | 0.52 |
| rho_cap | 145.5 | 24.2% | 0.70 |
| rho_mean | 145.5 | 24.2% | 0.70 |
| rho_lcb | 149.1 | 22.2% | 0.70 |
| rho_noaudit | 145.4 | 25.9% | 0.48 |

## Sanity conditions (true rho = 0.5; the old belief happened to be right) -- descriptive only

| Strategy | total loss |
|---|---|
| fixed | 131.3 |
| told | 131.3 |
| rho_cap | 133.9 |
| rho_mean | 133.9 |
| rho_lcb | 138.8 |
| rho_noaudit | 133.5 |

## Pre-registered hypotheses (PREREGISTRATION_rho.md)
- H-R1 rho_cap below fixed (wrong, constant 0.5): 145.5 vs 150.4 (-3.2%, 95% CI -4.0% to -2.5%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-R2 rho_cap within 5% of told (oracle): 145.5 vs 147.4 (-1.2%, 95% CI upper -0.4%) -> CONFIRMED

## H-R3 (descriptive): ranked mean loss of the four rho-learning modes, primary conditions
- rho_noaudit: 145.4
- rho_cap: 145.5
- rho_mean: 145.5
- rho_lcb: 149.1

## H-R4 (descriptive): rho_cap's learned rho_hat, median |rho_hat - true rho| = 0.083

## Sanity check: at true rho = 0.5 (old belief correct), rho_cap vs fixed differ by 2.0% of fixed's loss (133.9 vs 131.3) -- expected small, descriptive only