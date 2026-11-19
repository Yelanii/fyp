# Cross-check assumptions measured on real tools (confirm)

200 GSM8K problems (subset seed 11); 574 FreshQA pairs; temperature 0; 94739 s.

## Part 1: GSM8K solver pairs (exact numeric comparison, so e = 0 by construction)

| Model | accuracy | loud (no number) |
|---|---|---|
| qwen2.5:1.5b | 0.535 | 0.020 |
| qwen2.5:3b | 0.660 | 0.030 |
| phi4-mini | 0.850 | 0.050 |

Checker llama3.1:8b on the cheap solvers' answers (not loud):

| Flagged tool | catch rate q | false-alarm rate f |
|---|---|---|
| qwen2.5:1.5b | 36/89 = 0.404 (95% CI 0.309 to 0.508) | 4/107 = 0.037 (95% CI 0.015 to 0.092) |
| qwen2.5:3b | 32/62 = 0.516 (95% CI 0.394 to 0.636) | 7/132 = 0.053 (95% CI 0.026 to 0.105) |

| Pair (flagged, alternative) | A1: both wrong and agree (sigma) | A2: alternative right when they disagree, all | A2: same, only when the checker flagged |
|---|---|---|---|
| qwen2.5:1.5b -> phi4-mini | 4/16 = 0.250 (95% CI 0.102 to 0.495) | 71/87 = 0.816 (95% CI 0.722 to 0.884) | 28/35 = 0.800 (95% CI 0.641 to 0.900), one-sided binomial p = 0.00025 |
| qwen2.5:3b -> phi4-mini | 4/15 = 0.267 (95% CI 0.109 to 0.520) | 42/57 = 0.737 (95% CI 0.610 to 0.834) | 25/29 = 0.862 (95% CI 0.694 to 0.945), one-sided binomial p = 5.2e-05 |
| qwen2.5:1.5b -> qwen2.5:3b | 6/40 = 0.150 (95% CI 0.071 to 0.291) | 46/100 = 0.460 (95% CI 0.366 to 0.557) | 18/35 = 0.514 (95% CI 0.356 to 0.670), one-sided binomial p = 0.5 |

## Part 2: FreshQA comparator (phi4-mini) against the dataset's change labels

| Case | comparator wrong |
|---|---|
| answer changed, comparator says 'same' | 13/89 = 0.146 (95% CI 0.087 to 0.234) |
| answer unchanged, comparator says 'different' | 46/485 = 0.095 (95% CI 0.072 to 0.124) |
| all pairs (e) | 59/574 = 0.103 (95% CI 0.081 to 0.130) |

Caveat: the change labels are not hand-checked; at least one changed-labelled pair (fq42) has entries with the same meaning, which would count as a comparator error here although the comparator is right.

## Pre-registered decisions (PREREGISTRATION_assumptions.md)
- M-A1 qwen2.5:1.5b -> phi4-mini: sigma upper 95% bound 0.495 -> **COVERED by the robustness test (<= 0.9)**
- M-A1 qwen2.5:3b -> phi4-mini: sigma upper 95% bound 0.520 -> **COVERED by the robustness test (<= 0.9)**
- M-A2 qwen2.5:1.5b -> phi4-mini: alternative right in 28/35 flagged disagreements, p = 0.00025 -> **CONFIRMED**
- M-A2 qwen2.5:3b -> phi4-mini: alternative right in 25/29 flagged disagreements, p = 5.2e-05 -> **CONFIRMED**
- M-A3 FreshQA comparator error: upper 95% bound 0.130 -> **COVERED by the robustness test (<= 0.2)**
- Descriptive, same-family pair qwen2.5:1.5b -> qwen2.5:3b: sigma 6/40 = 0.150 (95% CI 0.071 to 0.291)