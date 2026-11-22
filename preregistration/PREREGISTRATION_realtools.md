# Pre-registration: corrected rule with real checkers, and the cross-check assumptions on real tools

**Written:** 18 November 2026, before either run below. Both runs are done on the author's laptop.

## Why
A review of paper draft v0.6 (18 Nov 2026, methodological soundness 6.2/10) gave two main reasons:

1. "The real GSM8K agent experiment evaluating the proposed rule was not rerun using the corrected decision
   criterion."
2. "The label-free estimation approach relies on cross-check assumptions (A1-A3), particularly limited shared errors
   between tools, but the corresponding robustness validation is primarily simulated rather than empirically
   established with real alternative-tool pairs."

## Study R: the real-checker experiment, re-run with the corrected rule
- **Command:** `EREPLAN_NETPV=1` and
  `python -m ereplan.realagent v5 --seed-start 4300 --seeds 10 --setup-from results/realagent_persist_20261025-004642/rows.json`
- **Design:** identical to the 27 Oct experiment (`PREREGISTRATION_v5.md`, real-checker pilot):
  - the qwen2.5:1.5b agent on GSM8K;
  - real Qwen2.5 1.5B and 3B checkers at temperature 0 and 0.7;
  - tool A drops to 85 or 75%; wrong-answer cost 1x or 3x;
  - the rule (corrected, no labels), the same rule told q and f, and the retrying rule told the calibrated q and f.
- **Seeds:** **4300-4309**, run once.
- **Disclosure:** seed 4200 was used on 18 Nov on the cloud machine in replay-only mode. The only purpose was to count how many checker answers were missing from the cache (about 94 per seed). Its numbers were incomplete, because missing answers count as no alarm, and they are not used.
- **Hypotheses:**
  - **R-N1 (primary).** The rule has lower loss than the retrying rule told the calibrated q and f. One-sided
    Wilcoxon over the 10 seeds, alpha = 0.05. The unit is the seed; the test over seed-and-condition pairs that the
    report also prints is not used.
  - **R-N2.** The rule's learned f is within 0.05 of the calibrated f (median absolute error).
- **Reported regardless of outcome:** failed-task rates, and the number of cache misses (new live checker calls).

## Study M: the cross-check assumptions measured on real tool pairs
- **Driver:** `python measure_assumptions.py confirm`. The development check was `dev`: 10 problems and 20 FreshQA
  pairs. It was run on the cloud machine with a fake model only, to test the code; there are no real-model numbers
  from it.
- **Part 1 (GSM8K):**
  - 200 test problems (fixed shuffle, subset seed 11).
  - Three real solver services (`tools_live.SolverService`): qwen2.5:1.5b, qwen2.5:3b and phi4-mini, at
    temperature 0.
  - The checker llama3.1:8b judges the two Qwen solvers' worked solutions.
  - Final numbers are compared exactly, so A3 holds by construction here.
- **Part 2 (FreshQA):**
  - All 574 old/new knowledge-base pairs.
  - The comparator phi4-mini says whether the two entries give the same answer.
  - Its errors are counted against the dataset's change labels.
- **Pairs:** (flagged tool -> alternative) qwen2.5:1.5b -> phi4-mini and qwen2.5:3b -> phi4-mini are the two
  primary pairs, because they are cross-family as in the rule's design. qwen2.5:1.5b -> qwen2.5:3b is a
  same-family pair and is descriptive only.
- **Decisions:**
  - **M-A1 (shared mistakes).** For each primary pair, sigma = P(the two answers are equal | both wrong), with a
    Wilson 95% CI. If the upper bound is <= 0.9, the simulated robustness test (sigma up to 0.9) covers the real
    value. If not, the paper says the real value is outside the tested range.
  - **M-A2 (the alternative is the better guess).** For each primary pair, among answers that the checker flagged
    and where the two tools disagree: the share where the alternative is right is above 0.5 (one-sided binomial,
    alpha = 0.05).
  - **M-A3 (comparison errors).** The FreshQA comparator's error rate e, with a Wilson 95% CI. If the upper bound
    is <= 0.2, the simulated robustness test (e up to 0.2) covers it.
  - **Descriptive:** each solver's accuracy and loud-failure rate; the checker's q and f on real solutions; sigma
    for the same-family pair.

## What the outcomes would mean
- **R-N1 confirmed:** the real-checker result holds for the corrected rule.
- **R-N1 not confirmed:** the paper reports that the corrected rule is no better than the labelled retrying rule
  with real checkers. That would still support the claim of no labels at no measured cost if the difference is
  small.
- **M-A1 or M-A3 not covered:** the robustness result does not extend to real tools. The paper states the measured
  values and narrows the claim.
- **M-A2 not confirmed:** the cross-check's use of the alternative's answer is not justified for that pair. That
  is a real limitation of the method, and it will be reported.

## Run record (added 19 Nov 2026, after the run)
- Study M ran once, 18-19 Nov 2026, with `measure_assumptions.py` as committed before the run (all models on each
  problem in turn); output `results/assumptions_confirm_20261118-131727`, 94,739 s in total. A faster version that runs
  one model at a time was written on 18 Nov while the run was in progress; it was not used, and the committed script
  is the one that produced the results. Part of Part 1 overlapped with other work on the same laptop, which affects
  only the running time.
- The report's heading cites `PREREGISTRATION_assumptions.md`; that is a typo in the script for this file.
- Outcome: M-A1 covered for both primary pairs (sigma upper bounds 0.495 and 0.520); M-A2 confirmed for both
  (28/35, p = 0.00025; 25/29, p = 5.2e-05); M-A3 covered (e = 59/574 = 0.103, upper bound 0.130). Descriptive:
  the same-family pair gave 18/35 = 0.514 for A2 (p = 0.5), so A2 does not hold for that pair.

## Known limits
- The models are small (1.5B to 8B), because everything runs on a CPU.
- Part 2 uses unaudited change labels; at least one pair (fq42) looks mislabelled.
- 200 problems give wide intervals on sigma when few answers are wrong for both tools.
