# Core 2 tuning of the outside baselines (development seeds 2400-2403)

46848 runs; 1773 s. Choice = lowest mean total loss over all 64 conditions.

## B13_ssv (48 settings)

| rank | setting | mean loss |
|---|---|---|
| 1 | {'alpha': 0.2, 'beta': 0.1, 'qx': 0.02, 'eta': 0.05} | 175.8 |
| 2 | {'alpha': 0.02, 'beta': 0.1, 'qx': 0.02, 'eta': 0.05} | 175.9 |
| 3 | {'alpha': 0.05, 'beta': 0.1, 'qx': 0.02, 'eta': 0.05} | 175.9 |
| 4 | {'alpha': 0.1, 'beta': 0.1, 'qx': 0.02, 'eta': 0.05} | 175.9 |
| 5 | {'alpha': 0.2, 'beta': 0.05, 'qx': 0.02, 'eta': 0.05} | 175.9 |
| worst | {'alpha': 0.1, 'beta': 0.2, 'qx': 0.05, 'eta': 0.05} | 200.7 |

## B14_rdecusum (120 settings)

| rank | setting | mean loss |
|---|---|---|
| 1 | {'A': 3.0, 'mu': 0.02, 'h': 1.0, 'p1': 0.75} | 158.2 |
| 2 | {'A': 3.0, 'mu': 0.02, 'h': 2.0, 'p1': 0.75} | 158.2 |
| 3 | {'A': 3.0, 'mu': 0.02, 'h': 4.0, 'p1': 0.75} | 158.2 |
| 4 | {'A': 6.0, 'mu': 0.02, 'h': 1.0, 'p1': 0.75} | 158.4 |
| 5 | {'A': 6.0, 'mu': 0.02, 'h': 2.0, 'p1': 0.75} | 158.4 |
| worst | {'A': 6.0, 'mu': 0.5, 'h': 4.0, 'p1': 0.85} | 172.6 |

## B15_glrklucb (12 settings)

| rank | setting | mean loss |
|---|---|---|
| 1 | {'alpha0': 0.1, 'check_rate': 0.4} | 181.8 |
| 2 | {'alpha0': 0.3, 'check_rate': 0.4} | 183.5 |
| 3 | {'alpha0': 1.0, 'check_rate': 0.4} | 185.2 |
| 4 | {'alpha0': 0.1, 'check_rate': 0.2} | 185.5 |
| 5 | {'alpha0': 0.3, 'check_rate': 0.2} | 188.0 |
| worst | {'alpha0': 1.0, 'check_rate': 0.1} | 191.1 |

## Reference on the same seeds (rules not tuned)

- never: 165.7
- v4: 146.9
- v5: 146.5