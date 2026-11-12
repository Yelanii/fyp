# Pilot report (e-Replan proof of concept)

**Decision: NO-GO (pivot)**  (pre-registered criteria, Table 3.16)

- Criterion 1 (>= 5% lower median cost per successful task than the best non-oracle baseline, paired Wilcoxon p < 0.05, in >= 2 of 3 scenarios): scenarios won = 0 -> not met
- Criterion 2 (no more false switches than that baseline): met
- Criterion 3 (harmless drift: no more checks than fixed-rate at equal or lower leak rate, where protection alone does not justify a check): not met

## Per-scenario comparison with the best non-oracle baseline
| Scenario | Best baseline | Baseline median | Rule median | Change | Wilcoxon p | False sw. rule / base |
|---|---|---|---|---|---|---|
| S1_sudden | B4_cusum | 133.9 | 155.1 | +15.9% | 1 | 0.0 / 0.0 |
| S2_gradual | B4_cusum | 138.1 | 189.6 | +37.3% | 1 | 0.0 / 8.8 |
| S3_harmless | B4_cusum | 136.6 | 144.0 | +5.4% | 1 | 0.0 / 8.3 |

## Criterion 3 detail (S3 harmless drift)
| q | Check price | Rule checks/task | Fixed-rate checks/task | Rule leak | Fixed-rate leak | Met |
|---|---|---|---|---|---|---|
| 0.5 | 30% | 0.12 | 1.62 | 0.272 | 0.245 | False |

## All strategies (judging seeds 0-19, pooled over the four pilot settings)
### S1_sudden
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| B6_oracle | 130.4 | 129.2 | 0.00 | 0.0 | 0.125 | 0 |
| B4_cusum | 133.9 | 132.3 | 0.33 | 0.0 | 0.132 | 12 |
| Rule_session | 146.3 | 141.4 | 0.86 | 0.0 | 0.180 | 73 |
| Rule | 155.1 | 149.7 | 1.52 | 0.0 | 0.212 | 118 |
| B1_always | 173.0 | 163.4 | 5.55 | 0.0 | 0.122 | 109 |
| B3_fixed | 183.4 | 159.0 | 1.71 | 0.0 | 0.284 | 206 |
| B2_never | 198.2 | 164.7 | 0.00 | 0.0 | 0.420 | 285 |
| B8_fixed_est | 211.2 | 171.5 | 0.30 | 0.0 | 0.460 | 320 |

### S2_gradual
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| B4_cusum | 138.1 | 137.1 | 0.48 | 8.8 | 0.149 | 12 |
| B6_oracle | 138.8 | 136.6 | 0.73 | 0.0 | 0.148 | 1 |
| Rule_session | 178.0 | 157.8 | 2.20 | 0.8 | 0.263 | 257 |
| Rule | 189.6 | 161.5 | 2.63 | 0.0 | 0.270 | 290 |
| B1_always | 194.0 | 173.1 | 5.83 | 0.0 | 0.189 | 290 |
| B2_never | 196.0 | 163.0 | 0.00 | 0.0 | 0.423 | 294 |
| B8_fixed_est | 197.8 | 164.4 | 0.30 | 0.0 | 0.417 | 296 |
| B3_fixed | 198.2 | 168.1 | 1.78 | 0.0 | 0.367 | 294 |

### S3_harmless
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| B4_cusum | 136.6 | 134.1 | 0.45 | 8.3 | 0.154 | nan |
| Rule | 144.0 | 139.8 | 1.23 | 0.0 | 0.222 | nan |
| Rule_session | 144.1 | 139.8 | 1.23 | 0.0 | 0.222 | nan |
| B2_never | 145.2 | 139.7 | 0.00 | 0.0 | 0.275 | nan |
| B6_oracle | 145.5 | 141.6 | 2.48 | 0.0 | 0.168 | nan |
| B8_fixed_est | 146.3 | 140.7 | 0.27 | 0.0 | 0.269 | nan |
| B3_fixed | 152.6 | 145.0 | 1.64 | 0.0 | 0.236 | nan |
| B1_always | 158.0 | 154.1 | 5.50 | 0.0 | 0.110 | nan |

## Tuned configurations (seeds 50-59)
- Rule: Rule {"window": 60, "epsilon": 0.02, "k": 5}
- B1_always: B1_always {"window": 60}
- B2_never: B2_never {"window": 60}
- B3_fixed: B3_fixed {"window": 60, "rate": 0.3}
- B4_cusum: B4_cusum {"h": 6, "p1": 0.8}
- B8_fixed_est: B8_fixed_est {"rate": 0.05}
- B6_oracle: B6_oracle {}
- Rule_session: Rule {"window": 60, "epsilon": 0.02, "k": 5, "horizon_mode": "session"}

Feasibility: about 0.62 CPU-seconds per 1,000 simulated tasks.

Rule_session is exploratory (plan horizon = calls left in the run, capped at 50) and is not part of the go/no-go decision.