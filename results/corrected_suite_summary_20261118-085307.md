# Corrected-rule suite: hypothesis lines from every report

All runs used EREPLAN_NETPV=1 (corrected check criterion) and fresh seeds. In these reports, `v5` (and every
rule built on it) is the corrected rule.

## sim  (v5_confirm_20261117-141451_netpv)

Seeds 8200-8219; 14080 runs; 16985 s. Unit of analysis: the seed (mean over the 64 conditions of drop x q x leak x f x pi). Metric: total loss per task (spend + leak loss x leaks + one task cost x failed tasks).
- H-V1 v5 below v4 by >= 3%: 144.8 vs 145.8 (-0.7%, 95% CI -1.1% to -0.2%), Wilcoxon p = 0.0036 over 20 seeds, Holm ok -> NOT CONFIRMED
- H-V2 v5 below v4_nocal by >= 5%: 144.8 vs 165.8 (-12.7%, 95% CI -13.5% to -11.9%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-V3 v5 below always_x by >= 0%: 144.8 vs 157.5 (-8.1%, 95% CI -8.9% to -7.2%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-V4 v5 (no labels) within 3% of v5_told (told q and f): 144.8 vs 144.0 (+0.5%, 95% CI upper +1.2%) -> CONFIRMED
- H-V5 persistence barely matters for v5: loss(pi = 1) - loss(pi = 0) = +0.12 (0.1% of its loss; need <= 2%), vs v4 +3.00 (v5 smaller: p = 9.5e-07) -> CONFIRMED
- H-V6 v5 learns f without labels: median |f_hat - f| at the end of a run = 0.041 (need <= 0.03) -> NOT CONFIRMED. Descriptive: median |q_hat - q| = 0.376
- H-V7 v5 below v4 told wrong values: 144.8 vs 148.1 (-2.2%), p = 1.9e-06 -> CONFIRMED

## stress  (v5_stress_20261117-142756_netpv)

Seeds 8220-8229; q 0.95, pi 1, drop {85, 75}%, leak {1, 3}, f {0.05, 0.15}; 779 s.
- H-C1 at e = 0.1, v5 below v4: 149.7 vs 152.5, p = 0.00098 over 10 seeds -> CONFIRMED

## bayes  (bayes_confirm_20261117-154016_netpv)

Seeds 8240-8259; 6720 runs; 4336 s. Two tools, single-step tasks, no retries; 48 conditions (drop x q x leak x f). Unit: the seed. Metric: total loss per task.
- H-B1 (sanity) Bayes has the lowest mean loss among never, always, cusum, v4: never 34.58, always 28.70, cusum 28.77, v4 27.37 vs Bayes 26.82 -> CONFIRMED
- H-B2 v4 within 5% of Bayes-optimal: regret +2.0% (95% CI +1.5% to +2.5%) -> CONFIRMED
- H-B3 v4 captures >= 80% of the achievable saving over never-check: 93% -> CONFIRMED

## core2  (core2_confirm_20261117-173234_netpv)

Seeds 8300-8319; 12800 runs; 6736 s. Unit: the seed (mean over 64 conditions).
- H-O1 v5 < ssv: 147.6 vs 175.5 (-15.9%, 95% CI -17.4% to -14.6%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED
- H-O2 v5 < rdecusum: 147.6 vs 159.6 (-7.6%, 95% CI -8.6% to -6.6%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED
- H-O3 v5 < glrklucb: 147.6 vs 175.3 (-15.8%, 95% CI -16.7% to -14.9%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED
- H-O4.1 v4 < ssv: 148.7 vs 175.5 (-15.3%, 95% CI -16.6% to -14.0%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED
- H-O4.2 v4 < rdecusum: 148.7 vs 159.6 (-6.8%, 95% CI -7.7% to -6.0%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED
- H-O4.3 v4 < glrklucb: 148.7 vs 175.3 (-15.2%, 95% CI -16.0% to -14.3%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED

## cb15  (costbench_v5_confirm_20261117-181237_netpv)

- H-CB1 v5 below v4_nocal: 111.7 vs 110.2 (+1.4%, 95% CI +0.6% to +2.2%), Wilcoxon p = 1 over 18 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB2 v5 below always_x: 111.7 vs 124.9 (-10.6%, 95% CI -11.5% to -9.7%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CB3 v5 below v4: 111.7 vs 111.4 (+0.3%, 95% CI +0.0% to +0.5%), Wilcoxon p = 0.98 over 18 seeds, Holm fail -> **NOT CONFIRMED**
- H-CB4 v4 below v2: 111.4 vs 121.0 (-8.0%, 95% CI -8.9% to -7.0%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CB5 v5 (no labels) within 3% of v5_told: 111.7 vs 110.5 (+1.1%, 95% CI upper +1.6%) -> **CONFIRMED**

## cb5  (costbench_v5_cheap_20261117-182202_netpv)

Seeds 8360-8377; 128 conditions per seed; 20736 runs; 557 s.
- H-CC1 v5 below v4_nocal: 109.9 vs 115.7 (-5.0%, 95% CI -6.5% to -3.6%), Wilcoxon p = 7.6e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CC3 v5 below always_x: 109.9 vs 115.9 (-5.1%, 95% CI -6.2% to -4.1%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-CC2 v5 (no labels) equivalent to v4 told q and f, within +/-3%: 109.9 vs 110.0 (-0.1%, 95% CI -0.4% to +0.2%) -> **CONFIRMED**

## fr11  (fr11_confirm_20261117-183020_netpv)

Seeds 8400-8417; 128 conditions per seed; 20736 runs; 491 s.
- H-RC1 v5 below v4_nocal: 111.4 vs 128.2 (-13.1%, 95% CI -14.1% to -11.8%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-RC3 v5 below always_x: 111.4 vs 144.1 (-22.7%, 95% CI -24.0% to -21.3%), Wilcoxon p = 3.8e-06 over 18 seeds, Holm ok -> **CONFIRMED**
- H-RC2 v5 equivalent to v4 told q and f, within +/-3%: 111.4 vs 111.4 (+0.0%, 95% CI -0.3% to +0.3%) -> **CONFIRMED**

## robust  (robustness_confirm_20261117-212216_netpv)

- H-S1 v5 at sigma 0.9 within +2% of sigma 0 (e = 0): 161.4 vs 161.4 (+0.0%, 95% CI -0.1% to +0.1%) -> **CONFIRMED**
- H-S2 worst cell, v5 below v4 without labels: 164.4 vs 202.3 (-18.7%, 95% CI -20.3% to -17.0%), p = 9.5e-07 -> **CONFIRMED**
- H-S3 worst cell, v5 within +3% of v4 told: 164.4 vs 165.1 (-0.4%, 95% CI -1.3% to +0.6%) -> **CONFIRMED**

## freshqa  (freshqa_confirm_20261117-222920_netpv)

- H-F1 rho_cap below use_B: 160.0 vs 142.4 (+12.3%, 95% CI +8.4% to +16.3%), Wilcoxon p = 1 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-F2 rho_cap below never: 160.0 vs 214.1 (-25.3%, 95% CI -29.8% to -20.2%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-F3 rho_cap below v5: 160.0 vs 159.6 (+0.3%, 95% CI -4.0% to +4.3%), Wilcoxon p = 0.71 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-F4 (secondary) where tool A goes stale in only 25% of runs, rho_cap below use_B: 146.0 vs 142.4 (+2.5%, 95% CI -3.2% to +7.9%), p = 0.86 -> **NOT CONFIRMED**

## anytool  (anytool_confirm_20261117-225549_netpv)

- H-N1a v6 below fixed tool A: 146.8 vs 170.0 (-13.6%, 95% CI -18.0% to -8.8%), Wilcoxon p = 0.00043 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N1b v6 below fixed tool B: 146.8 vs 187.9 (-21.9%, 95% CI -26.1% to -16.6%), Wilcoxon p = 6.7e-06 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N1c v6 below fixed tool C: 146.8 vs 222.4 (-34.0%, 95% CI -39.0% to -28.2%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-N2 v6 below never checking: 146.8 vs 147.4 (-0.4%, 95% CI -2.3% to +1.5%), Wilcoxon p = 0.51 over 20 seeds, Holm fail -> **NOT CONFIRMED**
- H-N3 on any_recover, v6 below v5: 143.1 vs 141.9 (+0.9%, 95% CI -0.7% to +2.8%), Wilcoxon p = 0.73 over 20 seeds, Holm fail -> **NOT CONFIRMED**

## boundary  (boundary_confirm_20261117-230438_netpv)

- H-B1 monitoring region (B +50% or more, A degrades in 50% of runs or fewer): v6 below fixed B: 153.5 vs 208.6 (-26.4%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> **CONFIRMED**
- H-B2 buying region (B +20% or less, A degrades in 75% of runs or more): fixed B below v6: 148.9 vs 148.6 (+0.2%), Wilcoxon p = 0.59 over 20 seeds, Holm fail -> **NOT CONFIRMED**

## ablation  (ablation_confirm_20261118-014709_netpv)

Seeds 8900-8919; 3840 runs; 9750 s. Unit of analysis: the seed (mean over the 32 conditions of drop x q x f x pi). Metric: total loss per task.
- H-A1 full below nofa: 131.5 vs 132.0 (+0.4%, 95% CI -0.7% to -0.1%), Wilcoxon p = 0.0086 over 20 seeds, Holm ok -> CONFIRMED
- H-A2 full below noxc: 131.5 vs 132.0 (+0.4%, 95% CI -0.7% to -0.1%), Wilcoxon p = 0.0021 over 20 seeds, Holm ok -> CONFIRMED
- H-A3 full below noswitch: 131.5 vs 154.5 (+17.5%, 95% CI -15.6% to -14.0%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-A4 full below told: 131.5 vs 131.3 (-0.1%, 95% CI -0.1% to +0.4%), Wilcoxon p = 0.68 over 20 seeds, Holm fail -> NOT CONFIRMED
- H-A5 full below nowindow: 131.5 vs 134.4 (+2.2%, 95% CI -3.0% to -1.1%), Wilcoxon p = 0.00035 over 20 seeds, Holm ok -> CONFIRMED

## rho  (rho_confirm_20261118-085301_netpv)

Seeds 9000-9019; 7680 runs; 25526 s. Unit of analysis: the seed. Metric: total loss per task.
- H-R1 rho_cap below fixed (wrong, constant 0.5): 145.8 vs 152.5 (-4.4%, 95% CI -5.2% to -3.6%), Wilcoxon p = 9.5e-07 over 20 seeds, Holm ok -> CONFIRMED
- H-R2 rho_cap within 5% of told (oracle): 145.8 vs 146.3 (-0.4%, 95% CI upper +0.6%) -> CONFIRMED
