# Study F: model family or accuracy? (confirm)

300 problems (201-500); temperature 0; 10919 s.

| Alternative to qwen2.5:1.5b | accuracy | P(wrong given 1.5B wrong) | P(wrong) | error lift | A2: right on flagged disagreements |
|---|---|---|---|---|---|
| qwen2.5:3b (same family) | 0.687 | 0.447 | 0.292 | 1.53 | 34/55 = 0.618 (95% CI 0.486 to 0.735), p = 0.052 |
| llama3.2:3b (other family) | 0.780 | 0.392 | 0.194 | 2.02 | 40/54 = 0.741 (95% CI 0.611 to 0.839), p = 0.00027 |
| phi4-mini (other family) | 0.860 | 0.192 | 0.084 | 2.28 | 43/52 = 0.827 (95% CI 0.703 to 0.906), p = 1e-06 |

Lift(qwen2.5:3b) - lift(llama3.2:3b): -0.47 (95% bootstrap CI -0.89 to -0.12; 278 problems valid for all three).

## Pre-registered decisions (PREREGISTRATION_family.md)
- H-F1 same-family errors are more related: lift(qwen2.5:3b) - lift(llama3.2:3b) > 0 with the 95% CI above 0 -> **NOT CONFIRMED**
- H-F2 llama3.2:3b is the better guess on flagged disagreements: 40/54, one-sided binomial p = 0.00027 -> **CONFIRMED**