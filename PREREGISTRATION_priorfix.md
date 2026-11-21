# Pre-registration: the prior fix for the learned false-alarm rate

**Written** before any confirmatory run of `run_priorfix.py`. Both confirmatory parts are run once, on the
author's laptop.

## Why
On every testbed where the direction was recorded, the label-free rule's learned false-alarm rate f was too high:
- 0.163–0.169 against a true 0.15 on the simulator;
- 0.13–0.20 against 0.05–0.15 in the GSM8K agent;
- 0.125 against 0.046 on live tools (D1).

On live tools this made the rule check rarely, and it did not beat never checking.

**Candidate cause, found in the code after D1.** The checker memory states a weak Beta prior with mean 0.1 and
strength 2 for f, placed on f/FMAX. Each Beta parameter is floored at 1. With FMAX = 0.5, this turns Beta(0.4, 1.6)
into Beta(1, 1.6), whose mean is f = 0.186, not 0.1. With FMAX = 0.95 the mean is 0.334. With few checks, the
posterior stays near this prior.

## Design (`run_priorfix.py`)
- **New variant `v5_fix`:** the rule exactly as evaluated, except that the prior of f is Beta(1, FMAX/0.1 − 1) on
  f/FMAX. Its mean on the grid is 0.092.
  - The q prior, every other setting and the code path are unchanged. The option `f_prior_matched` is off by
    default, so no existing result changes.
- **Part 1, simulator:**
  - the label-free-rule grid of the paper (64 conditions per seed; FMAX 0.5; corrected criterion);
  - seeds 9400–9419;
  - strategies: v5, v5_fix, v5_told and v4.
- **Part 2, live tools:**
  - the cached D1 answers (`data/processed/d1_table.json`), with the same conditions and loss as D1;
  - seeds 7300–7319;
  - strategies: never, CUSUM, v4, cross-check every call, v5_told, v5, v5_fix and buy B.
  - No model is called.
- **Part 3, CostBench (`run_priorfix_cb.py`):**
  - the FR11 design: CostBench task routes and prices, with verdicts drawn at the measured error rates of the four
    real checkers;
  - f grid [0, 0.95], where the default prior's mean for f is 0.33;
  - 64 conditions per seed;
  - seeds 9500–9517;
  - strategies: v5, v5_fix, v5_told and v4.
- **Unit of analysis:** the seed.

## Hypotheses
**Simulator**
- **H-F1.** v5_fix has a lower bias of the learned f than v5. Measure: per seed, |median over runs of (learned f −
  true f)|. Test: one-sided Wilcoxon.
- **H-F2.** v5_fix costs at most 1% more than v5. Test: the upper bound of the 95% paired bootstrap CI of the
  percentage difference is at most +1%.

**Live tools** (Holm correction across H-F3 to H-F5)
- **H-F3.** v5_fix has a lower bias of the learned f than v5. Measure: per seed, |median over runs of (learned f −
  0.046)|, where 0.046 is Study M's calibrated f.
- **H-F4.** v5_fix has lower loss than v5.
- **H-F5.** v5_fix has lower loss than never checking.

All three use the one-sided Wilcoxon over 20 seeds.

**CostBench**
The bias is measured per seed as |median over runs of (learned f − true f)|, averaged over the checker profiles of
each group.
- **H-F6a.** For the two checkers with low f (qwen2.5:1.5b, f = 0.14; qwen2.5:3b, f = 0.05), v5_fix has a **lower**
  bias than v5. Test: one-sided Wilcoxon.
- **H-F6b.** For the two judges with high f (phi4-mini, f = 0.56; llama3.1:8b, f = 0.52), v5_fix has a **higher**
  bias than v5. The reason: both priors pull the estimate towards their mean, and the fixed prior's mean (0.1) is
  further from these judges' f than the default's (0.33). Test: one-sided Wilcoxon.
- **H-F7.** v5_fix costs at most 1% more than v5. Test: the upper bound of the 95% paired bootstrap CI is at most +1%.

**Reported regardless of outcome:** every strategy's loss, wrong answers kept, failed tasks, checks per task and
median learned f; and v5_fix against v5_told, v4, cross-check every call, CUSUM and buying B, each as a percentage
with a 95% bootstrap CI.

## Disclosure
- This test was designed after D1 and D1-cal (seeds 7100–7119 and 7200–7219) were seen.
- On D1-cal, a strong prior at the calibrated value removed the bias, and the rule was 0.7% below never checking,
  which was not significant.
- **Development check** on the cloud machine: simulator seeds 1600–1601, 512 runs, not used here.

  | | median learned f − true f | median absolute error | loss | checks per task |
  |---|---|---|---|---|
  | v5 | +0.016 | 0.021 | 142.3 | 0.65 |
  | v5_fix | +0.000 | 0.022 | 141.4 | 0.83 |

  Because the absolute error did not change, H-F1 and H-F3 were set on the bias (the signed error) rather than the
  absolute error. This choice was made after the development check and before any confirmatory run.
- The live-tool answers are the same as in D1. Only the seeds change.

## Revision before the CostBench confirmatory run
The first version of this file had one CostBench hypothesis: that the fixed prior lowers the bias, pooled over all
four checkers. A development run (seeds 1990–1991, 1,024 runs) gave these median learned f − true f values:

| Checker | v5 | v5_fix |
|---|---|---|
| qwen2.5:1.5b | +0.039 | −0.021 |
| qwen2.5:3b | +0.111 | +0.019 |
| phi4-mini | −0.208 | −0.343 |
| llama3.1:8b | −0.168 | −0.303 |

v5 checked 0.09 times per task and v5_fix 0.18. So the learned f is dominated by the prior: it moves towards the
prior mean, whichever side the true f is on. The pooled hypothesis therefore mixes two opposite effects.

It was replaced by H-F6a and H-F6b, which test this shrinkage explanation directly. The change was made after the
development run and before any confirmatory seed (9500–9517) was used.

## What the outcomes would mean
- **H-F1, H-F3, H-F6a and H-F6b confirmed:** the floored prior is a cause of the bias, and the paper reports it as a correction
  of its own method.
- **H-F4 or H-F5 not confirmed:** removing the bias is not enough to make paid checks pay on these live tools,
  where the checker catches only about half of the wrong solutions. Reported as such.
- **H-F2 or H-F7 not confirmed:** the fixed prior raises loss on the simulator or CostBench by more than 1%. Reported with its size and
  direction.
