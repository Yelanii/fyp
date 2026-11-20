# Cross-check assumptions on real tools, extension (confirm)

Problems 201-500 of the subset-seed-11 shuffle; temperature 0; 77336 s.

### New problems only (confirmatory) (300 problems)

| Model | accuracy | loud |
|---|---|---|
| qwen2.5:1.5b | 0.607 | 0.037 |
| qwen2.5:3b | 0.687 | 0.020 |
| phi4-mini | 0.860 | 0.060 |

| Flagged tool | catch rate q | false-alarm rate f |
|---|---|---|
| qwen2.5:1.5b | 55/107 = 0.514 (95% CI 0.420 to 0.607) | 9/182 = 0.049 (95% CI 0.026 to 0.091) |
| qwen2.5:3b | 56/88 = 0.636 (95% CI 0.532 to 0.729) | 6/206 = 0.029 (95% CI 0.013 to 0.062) |

| Pair (flagged, alternative) | A1: sigma | A2: alternative right, flagged disagreements |
|---|---|---|
| qwen2.5:1.5b -> phi4-mini | 3/19 = 0.158 (95% CI 0.055 to 0.376) | 43/52 = 0.827 (95% CI 0.703 to 0.906), one-sided binomial p = 1e-06 |
| qwen2.5:3b -> phi4-mini | 7/20 = 0.350 (95% CI 0.181 to 0.567) | 41/50 = 0.820 (95% CI 0.692 to 0.902), one-sided binomial p = 2.8e-06 |
| qwen2.5:1.5b -> qwen2.5:3b | 9/46 = 0.196 (95% CI 0.107 to 0.332) | 34/55 = 0.618 (95% CI 0.486 to 0.735), one-sided binomial p = 0.052 |

### Study M and M2 pooled (descriptive) (500 problems)

| Model | accuracy | loud |
|---|---|---|
| qwen2.5:1.5b | 0.578 | 0.030 |
| qwen2.5:3b | 0.676 | 0.024 |
| phi4-mini | 0.856 | 0.056 |

| Flagged tool | catch rate q | false-alarm rate f |
|---|---|---|
| qwen2.5:1.5b | 91/196 = 0.464 (95% CI 0.396 to 0.534) | 13/289 = 0.045 (95% CI 0.026 to 0.075) |
| qwen2.5:3b | 88/150 = 0.587 (95% CI 0.507 to 0.662) | 13/338 = 0.038 (95% CI 0.023 to 0.065) |

| Pair (flagged, alternative) | A1: sigma | A2: alternative right, flagged disagreements |
|---|---|---|
| qwen2.5:1.5b -> phi4-mini | 7/35 = 0.200 (95% CI 0.100 to 0.359) | 71/87 = 0.816 (95% CI 0.722 to 0.884), one-sided binomial p = 9.8e-10 |
| qwen2.5:3b -> phi4-mini | 11/35 = 0.314 (95% CI 0.186 to 0.480) | 66/79 = 0.835 (95% CI 0.739 to 0.901), one-sided binomial p = 5.4e-10 |
| qwen2.5:1.5b -> qwen2.5:3b | 15/86 = 0.174 (95% CI 0.109 to 0.268) | 52/90 = 0.578 (95% CI 0.475 to 0.675), one-sided binomial p = 0.085 |

## Pre-registered decisions (PREREGISTRATION_assumptions_ext.md), new problems only
- M2-A1 qwen2.5:1.5b -> phi4-mini: sigma upper 95% bound 0.376 -> **COVERED (<= 0.9)**
- M2-A2 qwen2.5:1.5b -> phi4-mini: alternative right in 43/52 flagged disagreements, p = 1e-06 -> **CONFIRMED**
- M2-A1 qwen2.5:3b -> phi4-mini: sigma upper 95% bound 0.567 -> **COVERED (<= 0.9)**
- M2-A2 qwen2.5:3b -> phi4-mini: alternative right in 41/50 flagged disagreements, p = 2.8e-06 -> **CONFIRMED**
- Descriptive, same-family pair: sigma 9/46 = 0.196 (95% CI 0.107 to 0.332); A2 34/55 = 0.618 (95% CI 0.486 to 0.735), p = 0.052