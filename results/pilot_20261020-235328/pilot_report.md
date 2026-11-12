# Pilot report (e-Replan proof of concept)

**Decision: NO-GO (pivot)**  (pre-registered criteria, Table 3.16)

- Criterion 1 (>= 5% lower median cost per successful task than the best non-oracle baseline, paired Wilcoxon p < 0.05, in >= 2 of 3 scenarios): scenarios won = 0 -> not met
- Criterion 2 (no more false switches than that baseline): met
- Criterion 3 (harmless drift: no more checks than fixed-rate at equal or lower leak rate, where protection alone does not justify a check): met

## Per-scenario comparison with the best non-oracle baseline
| Scenario | Best baseline | Baseline median | Rule median | Change | Wilcoxon p | False sw. rule / base |
|---|---|---|---|---|---|---|
| S1_sudden | B4_cusum | 133.9 | 140.6 | +5.0% | 1 | 0.0 / 0.0 |
| S2_gradual | B4_cusum | 138.1 | 151.7 | +9.9% | 1 | 0.4 / 8.8 |
| S3_harmless | B4_cusum | 136.6 | 147.0 | +7.6% | 1 | 0.6 / 8.3 |

## Criterion 3 detail (S3 harmless drift)
| q | Check price | Rule checks/task | Fixed-rate checks/task | Rule leak | Fixed-rate leak | Met |
|---|---|---|---|---|---|---|
| 0.5 | 30% | 0.84 | 1.08 | 0.245 | 0.245 | True |

## All strategies (judging seeds 0-19, pooled over the four pilot settings)
### S1_sudden
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| B6_oracle | 130.4 | 129.2 | 0.00 | 0.0 | 0.125 | 0 |
| B4_cusum | 133.9 | 132.3 | 0.33 | 0.0 | 0.132 | 12 |
| Rule_leakaware | 134.3 | 133.3 | 0.74 | 0.0 | 0.129 | 18 |
| Rule_session | 137.9 | 135.8 | 1.39 | 0.0 | 0.120 | 20 |
| B2_never | 138.1 | 135.3 | 0.00 | 0.0 | 0.174 | 35 |
| Rule | 140.6 | 137.3 | 1.45 | 0.0 | 0.129 | 28 |
| B3_fixed | 141.1 | 139.0 | 1.05 | 0.0 | 0.153 | 26 |
| B1_always | 158.6 | 154.0 | 5.31 | 0.0 | 0.066 | 28 |
| B8_fixed_est | 211.2 | 171.5 | 0.30 | 0.0 | 0.460 | 320 |

### S2_gradual
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| B4_cusum | 138.1 | 137.1 | 0.48 | 8.8 | 0.149 | 12 |
| Rule_leakaware | 138.2 | 137.3 | 1.03 | 5.4 | 0.144 | 15 |
| B6_oracle | 138.8 | 136.6 | 0.73 | 0.0 | 0.148 | 1 |
| Rule_session | 147.3 | 144.1 | 2.05 | 2.5 | 0.152 | 47 |
| B3_fixed | 151.1 | 148.7 | 1.09 | 0.2 | 0.232 | 64 |
| Rule | 151.7 | 148.7 | 2.33 | 0.4 | 0.177 | 84 |
| B2_never | 155.2 | 147.0 | 0.00 | 0.4 | 0.277 | 90 |
| B1_always | 168.9 | 161.2 | 5.49 | 0.4 | 0.111 | 92 |
| B8_fixed_est | 197.8 | 164.4 | 0.30 | 0.0 | 0.417 | 296 |

### S3_harmless
| Strategy | Median cost/success | Loss/task | Checks/task | False sw./1000 | Leak rate | Median delay |
|---|---|---|---|---|---|---|
| B4_cusum | 136.6 | 134.1 | 0.45 | 8.3 | 0.154 | nan |
| Rule_leakaware | 138.1 | 135.0 | 1.02 | 8.1 | 0.151 | nan |
| B2_never | 145.2 | 139.4 | 0.00 | 0.8 | 0.266 | nan |
| B6_oracle | 145.5 | 141.6 | 2.48 | 0.0 | 0.168 | nan |
| B8_fixed_est | 146.3 | 140.7 | 0.27 | 0.0 | 0.269 | nan |
| Rule_session | 146.9 | 141.8 | 2.48 | 2.6 | 0.162 | nan |
| Rule | 147.0 | 142.2 | 2.55 | 0.6 | 0.172 | nan |
| B3_fixed | 149.3 | 142.5 | 1.09 | 1.0 | 0.235 | nan |
| B1_always | 158.0 | 153.8 | 5.49 | 0.6 | 0.106 | nan |

## Tuned configurations (seeds 50-59)
- Rule: Rule {"window": 30, "epsilon": 0.02, "k": 5}
- B1_always: B1_always {"window": 30}
- B2_never: B2_never {"window": 30}
- B3_fixed: B3_fixed {"window": 30, "rate": 0.2}
- B4_cusum: B4_cusum {"h": 6, "p1": 0.8}
- B8_fixed_est: B8_fixed_est {"rate": 0.05}
- B6_oracle: B6_oracle {}
- Rule_session: Rule {"window": 30, "epsilon": 0.02, "k": 3, "horizon_mode": "session"}
- Rule_leakaware: Rule_leakaware {"window": 60, "epsilon": 0.02, "k": 3}

Feasibility: about 0.86 CPU-seconds per 1,000 simulated tasks.

Rule_session and Rule_leakaware are exploratory variants added after the first pilot run (plan horizon = calls left in the run, capped at 50; switch line that also counts expected leak loss). They are not part of the go/no-go decision.