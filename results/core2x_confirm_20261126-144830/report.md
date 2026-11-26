# Core 2x: published baselines with the cross-check (confirm; PREREGISTRATION_core2x.md)

Seeds 9700-9719; 8960 runs; 815 s. Unit: the seed (mean over 64 conditions). EREPLAN_NETPV=1.

| Strategy | total loss | spend | wrong kept | failed tasks | checks/task | cross-checks/task | switches/run |
|---|---|---|---|---|---|---|---|
| v5 | 145.2 | 116.2 | 12.5% | 0.1% | 0.49 | 0.05 | 0.9 |
| ssv | 175.3 | 146.1 | 3.3% | 17.1% | 5.45 | 0.27 | 1.6 |
| ssv_x | 162.6 | 149.6 | 5.1% | 0.3% | 5.27 | 0.83 | 0.4 |
| rdecusum | 156.7 | 120.5 | 13.5% | 2.4% | 0.53 | 0.00 | 2.1 |
| rdecusum_x | 157.4 | 112.2 | 18.2% | 0.2% | 0.36 | 0.05 | 0.5 |
| glrklucb | 175.7 | 138.3 | 3.9% | 22.5% | 5.66 | 0.00 | 7.8 |
| glrklucb_x | 159.9 | 146.6 | 5.2% | 0.4% | 5.29 | 0.72 | 6.7 |

## Pre-registered hypotheses (one-sided Wilcoxon over seeds, Holm across H-X1 to H-X3)

- H-X1 v5 < ssv_x: 145.2 vs 162.6 (-10.7%, 95% CI -12.3% to -9.2%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED
- H-X2 v5 < rdecusum_x: 145.2 vs 157.4 (-7.8%, 95% CI -8.8% to -6.8%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED
- H-X3 v5 < glrklucb_x: 145.2 vs 159.9 (-9.2%, 95% CI -10.0% to -8.4%), Wilcoxon p = 9.5e-07, Holm ok -> CONFIRMED

## Descriptive: what the cross-check changes for each baseline

- D1 ssv_x < ssv: 162.6 vs 175.3 (-7.2%, 95% CI -8.2% to -6.2%), Wilcoxon p = 9.5e-07
- D2 rdecusum_x < rdecusum: 157.4 vs 156.7 (+0.4%, 95% CI -0.4% to +1.2%), Wilcoxon p = 0.88
- D3 glrklucb_x < glrklucb: 159.9 vs 175.7 (-9.0%, 95% CI -9.4% to -8.6%), Wilcoxon p = 9.5e-07
- D4 v5 < ssv: 145.2 vs 175.3 (-17.2%, 95% CI -18.6% to -15.9%), Wilcoxon p = 9.5e-07
- D5 v5 < rdecusum: 145.2 vs 156.7 (-7.4%, 95% CI -8.3% to -6.4%), Wilcoxon p = 9.5e-07
- D6 v5 < glrklucb: 145.2 vs 175.7 (-17.4%, 95% CI -18.3% to -16.5%), Wilcoxon p = 9.5e-07
