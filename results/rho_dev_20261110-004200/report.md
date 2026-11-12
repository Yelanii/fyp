# FR20 confirmatory test: development smoke test (not a test of the hypotheses)

Seeds 1850-1855; 2304 runs; 1946 s. Unit of analysis: the seed. Metric: total loss per task.

## Primary conditions (true rho in {0.0, 0.1, 0.3}; old fixed belief = 0.5, wrong)

| Strategy | total loss | leak rate | checks/task |
|---|---|---|---|
| fixed | 151.4 | 36.1% | 0.13 |
| told | 150.1 | 19.1% | 0.57 |
| rho_cap | 146.2 | 24.6% | 0.75 |
| rho_mean | 146.3 | 24.7% | 0.75 |
| rho_lcb | 151.5 | 21.3% | 0.81 |
| rho_noaudit | 146.0 | 27.0% | 0.41 |

## Sanity conditions (true rho = 0.5; the old belief happened to be right) -- descriptive only

| Strategy | total loss |
|---|---|
| fixed | 132.0 |
| told | 132.0 |
| rho_cap | 135.1 |
| rho_mean | 135.0 |
| rho_lcb | 140.4 |
| rho_noaudit | 134.5 |

## Pre-registered hypotheses (PREREGISTRATION_rho.md)
- H-R1 rho_cap below fixed (wrong, constant 0.5): 146.2 vs 151.4 (-3.4%, 95% CI -4.4% to -2.3%), Wilcoxon p = 0.016 over 6 seeds, Holm ok -> CONFIRMED
- H-R2 rho_cap within 5% of told (oracle): 146.2 vs 150.1 (-2.5%, 95% CI upper -1.3%) -> CONFIRMED

## H-R3 (descriptive): ranked mean loss of the four rho-learning modes, primary conditions
- rho_noaudit: 146.0
- rho_cap: 146.2
- rho_mean: 146.3
- rho_lcb: 151.5

## H-R4 (descriptive): rho_cap's learned rho_hat, median |rho_hat - true rho| = 0.078

## Sanity check: at true rho = 0.5 (old belief correct), rho_cap vs fixed differ by 2.3% of fixed's loss (135.1 vs 132.0) -- expected small, descriptive only