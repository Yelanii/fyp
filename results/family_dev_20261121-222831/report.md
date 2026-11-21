# Study F: model family or accuracy? (dev)

10 problems (201-210); temperature 0; 334 s.

| Alternative to qwen2.5:1.5b | accuracy | P(wrong given 1.5B wrong) | P(wrong) | error lift | A2: right on flagged disagreements |
|---|---|---|---|---|---|
| qwen2.5:3b (same family) | 0.600 | 0.800 | 0.400 | 2.00 | 0/1 = 0.000 (95% CI 0.000 to 0.793), p = 1 |
| llama3.2:3b (other family) | 0.600 | 0.500 | 0.333 | 1.50 | 1/1 = 1.000 (95% CI 0.207 to 1.000), p = 0.5 |
| phi4-mini (other family) | 0.800 | 0.000 | 0.000 | nan | 1/1 = 1.000 (95% CI 0.207 to 1.000), p = 0.5 |

Lift(qwen2.5:3b) - lift(llama3.2:3b): +0.75 (95% bootstrap CI -0.00 to +4.50; 9 problems valid for all three).