# Pre-registration: D1-cal, the rule with a labelled calibration prior on live tools

**Written** before any run of `run_d1cal.py` on the real D1 answers. The confirmatory run is made once, on the
author's laptop.

## Why
In D1 (`PREREGISTRATION_D1.md`, seeds 7100-7119), the rule without labels over-estimated the checker's false-alarm
rate: the median learned value was 0.125, against 0.046 calibrated. As a result it checked 0.13 times per task, and
did not beat never checking (73.4 vs 72.5). The same rule given the calibrated rates as fixed values did better
(71.5).

The rule already needs a one-off labelled sample to check assumption A2. This test asks whether giving the rule a
labelled calibration as the **prior** of its checker memory fixes the problem on live tools. With a prior, unlike
with fixed values, the rule still updates the rates from its own cross-checks.

## Design (`run_d1cal.py`)
- **Unchanged from D1:** the same cached answers (`data/processed/d1_table.json`), services, prices, conditions,
  loss, retry behaviour and code path (`ereplan/agent_live.run_one`).
- **New strategy `v5_cal`:** the rule (`Rule_v5_x`, corrected criterion) with Beta priors on its checker memory taken
  from the Study M labelled calibration (problems 1-200, disjoint from D1's problems 201-500):
  - q mean 68/151 with weight 151 (wrong solutions labelled);
  - f mean 11/239 with weight 239 (right solutions labelled).
- **Descriptive variant `v5_cal_small`:** the same means with one fifth of the weight (about 78 labelled solutions in
  total).
- **Also run:** never check, CUSUM, the retrying rule told q and f (`v4`), cross-check every call, the same rule told
  q and f, the rule without labels, and buying B.
- **Seeds:** 7200-7219, new and run once. 4 conditions per seed. Unit of analysis: the seed (loss averaged over its
  4 conditions).

## Hypotheses (one-sided Wilcoxon over the 20 seeds, Holm across the two)
- **H-C1.** The calibrated rule has lower loss than never checking.
- **H-C2.** The calibrated rule has lower loss than the retrying rule told q and f. Both rules have the same labelled
  information; one cross-checks a flag, the other retries.

**Reported regardless of outcome**, each as a percentage with a 95% bootstrap CI:
- the calibrated rule against the rule without labels, the same rule told q and f, cross-check every call, CUSUM,
  buying B and `v5_cal_small`;
- `v5_cal_small` against never checking;
- the median learned f and the checks per task of every rule.

## Disclosure
- This test was designed **after** the D1 results were seen, because of the bias reported there.
- On D1's seeds 7100-7119, the same rule told q and f cost 71.5, against 72.5 for never checking and 72.6 for the
  retrying rule told q and f. So the direction of H-C1 and H-C2 is expected from D1; the test asks whether it holds
  on new seeds, with a prior rather than fixed values.
- The answers and problems are the same as in D1. Only the seeds change, and with them the problem order and the
  time of the silent swap.
- The development check (`dev`, seeds 7010-7014) was run on the cloud machine only, on a synthetic answer table.
- The prior weight is the size of the Study M calibration; no other weight was tried on real answers.

## What the outcomes would mean
- **H-C1 and H-C2 confirmed:** with a labelled calibration (the same kind of sample A2 already needs), the rule beats
  never checking and the retrying rule on live tools. The paper then recommends a label-light rule, not a
  label-free one.
- **H-C1 not confirmed:** even calibrated, paid checks do not pay against never checking on these live tools.
  Reported as such.
- **H-C2 not confirmed:** cross-checking does not beat retrying at equal information on these tools. Reported as
  such.
