# Pilot report (e-Replan proof of concept)

Rule version judged: v2 (leak-aware switch line, session horizon capped at 50; PREREGISTRATION_v2.md)

**Decision: NO-GO (pivot)**  (pre-registered criteria, Table 3.16)

- Criterion 1 (>= 5% lower median cost per successful task than the best non-oracle baseline, paired Wilcoxon p < 0.05, in >= 2 of 3 scenarios): scenarios won = 0 -> not met
- Criterion 2 (no more false switches than that baseline): not met
- Criterion 3 (harmless drift: no more checks than fixed-rate at equal or lower leak rate, where protection alone does not justify a check): met

## Per-scenario comparison with the best non-oracle baseline
| Scenario | Best baseline | Baseline median | Rule median | Change | Wilcoxon p | False sw. rule / base |
|---|---|---|---|---|---|---|
| S1_sudden | B4_cusum | 134.0 | 134.9 | +0.7% | 0.621 | 0.3 / 0.2 |
| S2_gradual | B4_cusum | 139.4 | 138.9 | -0.3% | 0.445 | 6.3 / 6.9 |
| S3_harmless | B4_cusum | 136.6 | 135.6 | -0.7% | 0.389 | 8.0 / 8.3 |

## Criterion 3 detail (S3 harmless drift)
| q | Check price | Rule checks/task | Fixed-rate checks/task | Rule leak | Fixed-rate leak | Met |
|---|---|---|---|---|---|---|
| 0.5 | 30% | 0.11 | 1.12 | 0.181 | 0.257 | True |

## All strategies (judging seeds 20-39, pooled over the four pilot settings)
### S1_sudden
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| B6_oracle | 128.6 | 128.6 | 0.00 | 0.0 | 0.117 | 0 |
| B4_cusum | 134.0 | 133.0 | 0.39 | 0.2 | 0.132 | 19 |
| Rule | 134.9 | 133.4 | 0.69 | 0.3 | 0.127 | 19 |
| Rule_v1 | 138.3 | 136.2 | 1.35 | 0.0 | 0.121 | 30 |
| B2_never | 140.8 | 138.1 | 0.00 | 0.0 | 0.195 | 54 |
| B3_fixed | 141.5 | 139.8 | 1.11 | 0.0 | 0.155 | 30 |
| B1_always | 158.2 | 153.8 | 5.29 | 0.0 | 0.065 | 26 |
| B8_fixed_est | 231.9 | 174.4 | 0.32 | 0.0 | 0.476 | 348 |

### S2_gradual
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| Rule | 138.9 | 137.0 | 0.92 | 6.3 | 0.143 | 16 |
| B6_oracle | 139.0 | 136.3 | 0.74 | 0.0 | 0.146 | 2 |
| B4_cusum | 139.4 | 136.9 | 0.49 | 6.9 | 0.150 | 21 |
| Rule_v1 | 153.9 | 148.5 | 2.34 | 0.0 | 0.173 | 81 |
| B3_fixed | 156.3 | 150.7 | 1.16 | 0.4 | 0.250 | 123 |
| B2_never | 159.8 | 150.3 | 0.00 | 0.4 | 0.312 | 140 |
| B1_always | 168.1 | 161.4 | 5.50 | 0.0 | 0.111 | 71 |
| B8_fixed_est | 190.8 | 162.1 | 0.30 | 0.0 | 0.405 | 298 |

### S3_harmless
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| Rule | 135.6 | 134.6 | 0.92 | 8.0 | 0.146 | nan |
| B4_cusum | 136.6 | 134.5 | 0.50 | 8.3 | 0.152 | nan |
| B6_oracle | 146.6 | 142.0 | 2.62 | 0.0 | 0.167 | nan |
| B2_never | 147.2 | 139.9 | 0.00 | 0.0 | 0.278 | nan |
| Rule_v1 | 148.0 | 142.7 | 2.60 | 0.2 | 0.180 | nan |
| B8_fixed_est | 148.0 | 140.7 | 0.28 | 0.0 | 0.271 | nan |
| B3_fixed | 151.7 | 143.6 | 1.13 | 0.0 | 0.251 | nan |
| B1_always | 158.9 | 153.9 | 5.50 | 0.2 | 0.109 | nan |

## Tuned configurations (seeds 50-59)
- Rule: Rule_leakaware {"window": 60, "epsilon": 0.02, "k": 3, "horizon_mode": "session", "session_cap": 50}
- B1_always: B1_always {"window": 30}
- B2_never: B2_never {"window": 30}
- B3_fixed: B3_fixed {"window": 30, "rate": 0.2}
- B4_cusum: B4_cusum {"h": 6, "p1": 0.8}
- B8_fixed_est: B8_fixed_est {"rate": 0.05}
- B6_oracle: B6_oracle {}
- Rule_v1: Rule {"window": 30, "epsilon": 0.02, "k": 5}

Feasibility: about 1.28 CPU-seconds per 1,000 simulated tasks.

Rule_v1 is the proposal rule, shown for reference only; the judged 'Rule' is v2.