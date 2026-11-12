# Core 2 tuning, round 2 (grids extended past round-1 edges; same development seeds)

16128 runs; 472 s.

## B13_ssv

- round-1 choice {'alpha': 0.2, 'beta': 0.1, 'qx': 0.02, 'eta': 0.05}: 175.8
- best round-2 setting {'alpha': 0.2, 'beta': 0.1, 'qx': 0.005, 'eta': 0.05}: 173.9
- worst round-2 setting {'alpha': 0.4, 'beta': 0.1, 'qx': 0.01, 'eta': 0.2}: 177.6
- FINAL: {'alpha': 0.2, 'beta': 0.1, 'qx': 0.005, 'eta': 0.05}

## B14_rdecusum

- round-1 choice {'A': 3.0, 'mu': 0.02, 'h': 1.0, 'p1': 0.75}: 158.2
- best round-2 setting {'A': 2.0, 'mu': 0.01, 'h': 1.0, 'p1': 0.75}: 154.5
- worst round-2 setting {'A': 2.0, 'mu': 0.0025, 'h': 1.0, 'p1': 0.65}: 175.6
- FINAL: {'A': 2.0, 'mu': 0.01, 'h': 1.0, 'p1': 0.75}

## B15_glrklucb

- round-1 choice {'alpha0': 0.1, 'check_rate': 0.4}: 181.8
- best round-2 setting {'alpha0': 0.03, 'check_rate': 1.0}: 176.8
- worst round-2 setting {'alpha0': 0.1, 'check_rate': 0.4}: 181.8
- FINAL: {'alpha0': 0.03, 'check_rate': 1.0}
