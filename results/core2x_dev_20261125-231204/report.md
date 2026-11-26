# Core 2x: published baselines with the cross-check (dev; PREREGISTRATION_core2x.md)

Seeds 9690-9691; 896 runs; 203 s. Unit: the seed (mean over 64 conditions). EREPLAN_NETPV=1.

| Strategy | total loss | spend | wrong kept | failed tasks | checks/task | cross-checks/task | switches/run |
|---|---|---|---|---|---|---|---|
| v5 | 147.9 | 119.4 | 12.6% | 0.0% | 0.78 | 0.08 | 0.9 |
| ssv | 179.6 | 151.7 | 4.2% | 14.2% | 5.51 | 0.48 | 1.6 |
| ssv_x | 169.6 | 153.2 | 6.6% | 0.2% | 5.26 | 0.92 | 0.5 |
| rdecusum | 159.4 | 121.0 | 14.3% | 2.5% | 0.52 | 0.00 | 2.2 |
| rdecusum_x | 160.2 | 112.4 | 19.3% | 0.1% | 0.37 | 0.05 | 0.5 |
| glrklucb | 177.9 | 138.8 | 4.8% | 22.1% | 5.67 | 0.00 | 8.2 |
| glrklucb_x | 164.1 | 146.9 | 6.8% | 0.3% | 5.30 | 0.72 | 6.9 |

## Pre-registered hypotheses (one-sided Wilcoxon over seeds, Holm across H-X1 to H-X3)

- H-X1 v5 < ssv_x: 147.9 vs 169.6 (-12.8%, 95% CI -16.0% to -9.4%), Wilcoxon p = 0.25, Holm fail -> NOT CONFIRMED
- H-X2 v5 < rdecusum_x: 147.9 vs 160.2 (-7.7%, 95% CI -8.3% to -7.2%), Wilcoxon p = 0.25, Holm fail -> NOT CONFIRMED
- H-X3 v5 < glrklucb_x: 147.9 vs 164.1 (-9.9%, 95% CI -10.4% to -9.5%), Wilcoxon p = 0.25, Holm fail -> NOT CONFIRMED

## Descriptive: what the cross-check changes for each baseline

- D1 ssv_x < ssv: 169.6 vs 179.6 (-5.6%, 95% CI -9.6% to -1.5%), Wilcoxon p = 0.25
- D2 rdecusum_x < rdecusum: 160.2 vs 159.4 (+0.5%, 95% CI -1.3% to +2.3%), Wilcoxon p = 0.75
- D3 glrklucb_x < glrklucb: 164.1 vs 177.9 (-7.8%, 95% CI -8.6% to -6.9%), Wilcoxon p = 0.25
- D4 v5 < ssv: 147.9 vs 179.6 (-17.7%, 95% CI -18.0% to -17.3%), Wilcoxon p = 0.25
- D5 v5 < rdecusum: 147.9 vs 159.4 (-7.3%, 95% CI -8.4% to -6.1%), Wilcoxon p = 0.25
- D6 v5 < glrklucb: 147.9 vs 177.9 (-16.9%, 95% CI -17.2% to -16.6%), Wilcoxon p = 0.25
