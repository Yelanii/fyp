# Pre-registration: Study M2, the cross-check assumptions on 300 more problems

**Written:** 19 November 2026, before the run. The run is done once, on the author's laptop.

## Why
A review of paper draft v0.8.1 (19 Nov 2026, methodological soundness 6.5/10) said:

> "the cross-check assumptions are validated using relatively small samples: only 29-35 flagged disagreements
> support the principal alternative-tool accuracy findings, while the shared-error estimates have wide confidence
> intervals based on only 15-16 joint-error cases."

Study M (`PREREGISTRATION_realtools.md`, 200 problems) met all five of its checks. Study M2 repeats its GSM8K part
on new problems, so that the confirmatory result rests on data never seen before and the pooled estimates are
tighter.

## Design
- **Driver:** `python measure_assumptions_ext.py confirm`. The pipeline check `dev` (5 problems) was run on the cloud
  machine with a fake model only; there are no real-model numbers from it.
- **Problems:** problems 201-500 of the same fixed shuffle of the GSM8K test set (subset seed 11). Problems 1-200
  were Study M and are not used in the confirmatory decisions.
- **Models, prompts, checker, comparison:** identical to Study M: solver services qwen2.5:1.5b, qwen2.5:3b and
  phi4-mini (temperature 0); checker llama3.1:8b on the two Qwen solvers' solutions; exact numeric comparison.
- **Order:** one model at a time over all 300 problems, then the checker. At temperature 0 with the answer cache,
  the order changes the running time only.
- **Pairs:** as in Study M. Primary: qwen2.5:1.5b -> phi4-mini and qwen2.5:3b -> phi4-mini. Descriptive:
  qwen2.5:1.5b -> qwen2.5:3b.
- **FreshQA comparator (A3):** not repeated; Study M used all 574 pairs.

## Decisions (new 300 problems only)
- **M2-A1.** For each primary pair, sigma = P(the two answers are equal | both wrong), with a Wilson 95% CI. Covered
  by the robustness test if the upper bound is <= 0.9.
- **M2-A2.** For each primary pair, among flagged answers where the two tools disagree, the alternative is right in
  more than half: one-sided binomial test against 0.5, alpha = 0.05.

## Reported regardless of outcome
- The same tables for the 300 new problems and for all 500 problems pooled (pooled = descriptive, because the first
  200 have been seen).
- The same-family pair's sigma and A2.
- Each solver's accuracy and loud-failure rate; the checker's q and f.

## What the outcomes would mean
- **Both confirmed again:** the Study M result replicates on new data; the paper reports both and the pooled
  intervals.
- **M2-A2 not confirmed for a pair:** Study M's A2 result did not replicate for that pair; the paper reports this
  and narrows the claim.
- **M2-A1 not covered:** real shared mistakes exceed the tested range for that pair; the paper says so.

## Known limits
- Same three small solvers and one maths dataset. More problems narrow the intervals but do not widen the range of
  tools tested.
