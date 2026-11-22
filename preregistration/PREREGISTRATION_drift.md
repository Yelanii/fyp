# Pre-registration: drift test (gradual degradation and a checker that changes)

Written before any confirmatory seed is run, and committed to the repository before the confirmatory run.

## Why

Every simulator test so far let tool A drop at once and kept the checker's error rates fixed for the whole run. Two questions follow from this. What happens when degradation is gradual? And what happens when the checker's own reliability changes during a run? This test answers both on the simulator, with the rule as evaluated in the paper: v5, with the corrected check criterion and the default prior.

## Design

The simulator is as in the main test. There are three tools with prices 20, 24 and 30 and base success rates 0.95, 0.95 and 0.97. A run has 120 tasks of 5 steps. Half of failures are loud (rho = 0.5). A check costs 15% of the mean tool price, and up to R = 2 retries are allowed. Verdicts are fully repeated (pi = 1), as measured for the real checkers.

**Part G (gradual decline).**
- Tool A declines linearly from 0.95 to 0.85, 0.75 or 0.60 over 200 calls (scenario `ramp_<level>`, added by `apply_drift.py`).
- The decline starts at the step where the sudden drop `drop_<level>` would begin on the same seed.
- Checker catch rate q is 0.8 or 0.95; its false-alarm rate f is 0.15.
- The wrong-answer cost L is 1 or 3 tasks.
- This gives 12 conditions per seed.

**Part D (the checker changes).**
- Tool A drops at once to 0.85, 0.75 or 0.60 (scenario `drop_<level>`, as in the main test).
- The checker starts at q = 0.95 and f = 0.05.
- At a step drawn uniformly from 200 to 399 for each run (from its own random stream), one of two changes happens:
  - its false-alarm rate rises to 0.20 (`f_up`), or
  - its catch rate falls to 0.60 (`q_down`).
- L is 1 or 3. This gives 12 conditions per seed.
- Strategies that are told q and f are told the rates from before the change, as if the checker had been calibrated before it drifted.

**Strategies.** All are unchanged from the main test (`ereplan/v5_exp.py`, `STRATS`):
- `never`: never check;
- `cusum`: CUSUM;
- `v4`: the retrying rule told q and f;
- `v4_nocal`: the retrying rule without labels;
- `always_x`: cross-check every call;
- `v5_told`: the rule told q and f;
- `v5`: the rule, without labels.

**Seeds.**
- Confirmatory: 9600 to 9619 (20 seeds, not used before).
- Development: 1604 and 1605. These are a pipeline check only and are not used for any decision about the hypotheses.

**Metric.** Total loss per task. For each part, it is averaged over that part's conditions for each seed, which gives one value per seed and strategy, as in the main test.

## Hypotheses

**Non-inferiority.** We compute the 95% bootstrap confidence interval of the percentage difference in mean loss over seeds. A hypothesis is confirmed if the upper end of the interval is at most +3%, the margin of the main test.
- **H-G1 (part G):** the rule (`v5`) is within 3% of the same rule told q and f (`v5_told`).
- **H-D1 (part D):** the rule (`v5`) is within 3% of the same rule told the rates from before the change (`v5_told`).

**Superiority.** We use a one-sided Wilcoxon signed-rank test on seed means, with Holm's correction across these three hypotheses at alpha = 0.05.
- **H-G2 (part G):** the rule's loss is below that of the label-free retrying rule (`v4_nocal`).
- **H-G3 (part G):** the rule's loss is below that of never checking.
- **H-D2 (part D):** the rule's loss is below that of the label-free retrying rule (`v4_nocal`).

**Descriptive only:**
- the rule against `v4`, `cusum`, `always_x` and `never` in each part;
- results by level and by type of change;
- in part D, the rule's learned f and q at the end of the run.

## What the outcomes would mean

- **H-G1 to H-G3 confirmed:** the main findings do not depend on the drop being sudden.
- **H-G1 not confirmed:** learning without labels costs more under a gradual decline, where tool failures and checker errors are harder to tell apart.
- **H-D1 confirmed:** a rule that keeps learning its checker does no worse than one given a calibration that has gone stale.
- **H-D1 not confirmed:** the label-free rule pays more for the change than the stale calibration does. This would weigh against learning without labels when checkers change.
- **H-D2 not confirmed:** the cross-check's advantage over retrying does not survive a checker that changes.

Every result is reported, whether confirmed or not.

## Disclosure

- The test was designed after reviews of the draft asked about gradual degradation and about checkers whose reliability changes. No confirmatory seed (9600 to 9619) has been run.
- The development check (seeds 1604 and 1605) was run on the cloud machine after this file was written, to check the pipeline and the run time (336 runs in about 200 s on one process). After it, descriptive columns were added to the report (spend, and the cost of wrong answers kept and failed tasks), and a reduced version (one level, one q, one wrong-answer cost) was run once on the same seeds to check that code. The hypotheses were not changed after either run, and nothing else in the code changed.

## Code

- `run_drift.py` holds the analysis and is committed with this file. The confirmatory run is made once.
- `apply_drift.py` adds the `ramp_` scenario and the optional late checker rates (`Setting.q_late`, `Setting.f_late`) to `ereplan/config.py` and `ereplan/env.py`.
  - Both options are off unless a run asks for them, and they use their own random streams.
  - Before the confirmatory run, `python reproduce_paper.py` is run again to show that every earlier result is unchanged.
