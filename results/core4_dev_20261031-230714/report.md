# Core 4: shared mistakes in cross-checks (dev seeds 2600-2603)

3840 runs; 2257 s. 64 conditions x sigma (0.0, 0.3, 0.6).

| Strategy | loss, sigma 0.0 | loss, sigma 0.3 | loss, sigma 0.6 | f error, sigma 0.0 | f error, sigma 0.3 | f error, sigma 0.6 |
|---|---|---|---|---|---|---|
| never | 156.8 | 156.8 | 156.8 | - | - | - |
| v4 | 144.8 | 144.8 | 144.8 | - | - | - |
| always_x | 157.6 | 157.6 | 157.6 | - | - | - |
| v5 | 144.0 | 143.9 | 144.0 | +0.038 | +0.038 | +0.038 |
| v5_s | 144.1 | 144.0 | 144.1 | +0.038 | +0.038 | +0.038 |

## v5_s vs v5 by sigma (seed means)

- sigma 0.0: v5_s 144.1 vs v5 144.0 (+0.07%, CI +0.01% to +0.13%), p = 1
- sigma 0.3: v5_s 144.0 vs v5 143.9 (+0.07%, CI +0.00% to +0.13%), p = 0.94
- sigma 0.6: v5_s 144.1 vs v5 144.0 (+0.07%, CI +0.01% to +0.13%), p = 1
- sigma 0.0: v5 144.0 vs v4 144.8 (-0.56%)
- sigma 0.3: v5 143.9 vs v4 144.8 (-0.57%)
- sigma 0.6: v5 144.0 vs v4 144.8 (-0.54%)