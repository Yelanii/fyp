# Pre-registration: D1-power, a high-power replication on the live tools

**Written** before any run of `run_d1power.py` on the real D1 answers. The confirmatory run is made once, on the
author's laptop.

## Why
The live-tool tests each used 20 seeds: D1 (seeds 7100-7119), D1-cal (7200-7219) and the live part of the prior fix
(7300-7319). Reviews of the draft named this as limited statistical power.

The differences between the checking policies and never checking were small, so 20 seeds could not separate some of
them from chance:
- the rule with a labelled calibration prior (`v5_cal`) against never checking: -0.7% (95% CI -1.8% to +0.6%,
  p = 0.16, D1-cal);
- the same rule told q and f against never checking: -1.4% (D1) and -0.8% (prior fix), both descriptive.

## Design (`run_d1power.py`)
- **Unchanged from D1:**
  - the cached answers (`data/processed/d1_table.json`; no model is called);
  - the services and prices, the four conditions, the loss, and the retry behaviour;
  - the code path (`ereplan/agent_live.run_one`).
- **Strategies:**
  - never check;
  - always check and retry;
  - CUSUM;
  - the retrying rule told q and f (`v4`);
  - cross-check every call (`always_x`);
  - the same rule told q and f (`v5_told`);
  - the rule as evaluated (`v5`);
  - the rule with the corrected prior (`v5_fix`, as in the prior-fix test);
  - the label-light rule (`v5_cal`, as in D1-cal: the Study M labelled calibration as the prior of the checker
    memory);
  - buying B.
- **Seeds:** 7400-7599, 200 new seeds, run once. 4 conditions per seed.
- **Unit of analysis:** the seed (loss averaged over its 4 conditions).

## Sample size (power analysis, fixed before the run)
- **Starting point:** in D1-cal, the 95% CI of v5_cal against never checking had a half-width of about 1.2 points
  with 20 seeds. That gives a standard error of about 0.6 points.
- **Assumption:** the standard error falls with the square root of the number of seeds.
- **With 200 seeds:** the standard error is about 0.19 points.
- **Power for H-P1:**
  - about 90% at a one-sided alpha of 0.0125 (the strictest Holm level for four hypotheses), if the true difference
    is -0.7%;
  - about 80% at alpha 0.05, if it is -0.5%.
- **What 200 seeds buys:** a tool to separate a real difference of about half a percent from chance. If the true
  difference is zero, more seeds do not make it look real.

## Hypotheses (one-sided Wilcoxon over the 200 seeds; Holm across H-P1 to H-P4)
- **H-P1.** The label-light rule (`v5_cal`) has lower loss than never checking.
- **H-P2.** The label-light rule has lower loss than the retrying rule told q and f. Both have the same labelled
  information; one cross-checks a flag, the other retries.
- **H-P3.** Cross-checking every call has lower loss than never checking.
- **H-P4.** Cross-checking every call has lower loss than the retrying rule told q and f.

**Reported regardless of outcome:**
- `v5`, `v5_fix`, `v5_told`, CUSUM, always check and buying B against never checking, each as a percentage with a 95%
  bootstrap CI;
- `v5_cal` against `always_x`;
- the per-condition losses;
- wrong answers kept, failed tasks, checks and cross-checks per task, and the median learned f;
- the per-seed standard deviation of the loss.

## Disclosure
- Designed after D1, D1-cal and the prior fix had been seen. The direction of every hypothesis matches what those
  runs showed. This test asks whether the differences hold with enough seeds to tell.
- **Seeds vary only the order of the 300 problems and the time of the silent swap.** The problems and the cached
  answers are the same in every run. Inference is therefore about these services on these problems, not about other
  tasks or models.
- The development check (`dev`, seeds 7010-7014) was run on the cloud machine only, on a synthetic answer table.

## What the outcomes would mean
- **H-P1 confirmed:** on live tools with a weak checker, the label-light rule beats never checking, by a small
  margin.
- **H-P1 not confirmed:** with this checker, paid checks by the rule do not beat never checking even with ten times
  the seeds. The paper reports this as the edge of the region where monitoring pays.
- **H-P3 and H-P4 confirmed:** resolving flags by cross-checking pays on live tools, both against never checking and
  against retrying.
