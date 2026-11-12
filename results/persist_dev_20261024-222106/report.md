# Part E development tuning (seeds 1500-1505; q 0.95, leak 3; f 0 / 0.05 / 0.15 x pi 0 / 1)

- b9_vrr {'window': 30, 'reverify_k': 1}: mean loss 161.75
- b9_vrr {'window': 30, 'reverify_k': 2}: mean loss 163.64
  -> chosen {'window': 30, 'reverify_k': 1}
- b10_pb {'gamma': 0.95, 'check_rate': 0.0}: mean loss 204.85
- b10_pb {'gamma': 0.95, 'check_rate': 0.2}: mean loss 195.68
- b10_pb {'gamma': 0.95, 'check_rate': 0.5}: mean loss 185.22
- b10_pb {'gamma': 0.98, 'check_rate': 0.0}: mean loss 210.49
- b10_pb {'gamma': 0.98, 'check_rate': 0.2}: mean loss 198.95
- b10_pb {'gamma': 0.98, 'check_rate': 0.5}: mean loss 182.37
- b10_pb {'gamma': 0.995, 'check_rate': 0.0}: mean loss 221.53
- b10_pb {'gamma': 0.995, 'check_rate': 0.2}: mean loss 208.80
- b10_pb {'gamma': 0.995, 'check_rate': 0.5}: mean loss 189.25
  -> chosen {'gamma': 0.98, 'check_rate': 0.5}
- b11_btm {'n_off': 20.0, 'horizon_mode': 'session', 'session_cap': 50}: mean loss 214.30
- b11_btm {'n_off': 100.0, 'horizon_mode': 'session', 'session_cap': 50}: mean loss 219.26
  -> chosen {'n_off': 20.0, 'horizon_mode': 'session', 'session_cap': 50}

12 s. Saved results/persist_dev_20261024-222106/tuned.json