# Pre-registration: D1, the rule on live model-backed tools with natural silent degradation

**Written:** 20 November 2026, before any D1 run with real models and before the Study M2 report (which covers the
same problems) was produced. The confirmatory run is done once, on the author's laptop.

## Why
Reviews of the paper (v0.8.1 and v0.8.2, 19 Nov 2026) said the real-world validation is narrow: the GSM8K agent's
faults are injected into calculator steps, and CostBench uses drawn verdicts. D1 tests the rule where the tools, the
degradation, the loud failures, the checker and the cross-check are all real model behaviour.

## Design (`ereplan/agent_live.py`)
- **Problems:** GSM8K test problems 201-500 of the subset-seed-11 shuffle (the problems of Study M2). Each task is
  one problem, answered by one call to a solver service.
- **Services (tools_live.SolverService, temperature 0):**
  - **A** (price 20): qwen2.5:3b until a seeded point in the run, uniform between 1/4 and 1/2 of the run, then
    silently **qwen2.5:1.5b**. The swap raises no error; A's wrong answers are the models' own mistakes.
  - **B** (price 45, 52, 62 or 74): phi4-mini.
- **Loud failure:** a solution with no usable final number (real, not drawn).
- **Checker:** llama3.1:8b judges the whole worked solution (price 15% of the mean service price).
- **Cross-check:** the problem is solved by the other service and the final numbers are compared exactly.
- **Retries:** every service and the checker are deterministic, so a retry returns the same answer and the same
  verdict. This is the measured behaviour at temperature 0, not a modelling choice.
- **Answers are produced once** (`python -m ereplan.agent_live prepare`) and cached, so every strategy and seed sees
  the same answers. New model calls: llama3.1:8b on phi4-mini's 300 solutions; the rest is shared with Study M2.
- **Conditions (wrong-answer cost L, price of B):** (100, 45), (100, 52), (200, 62), (200, 74). They were chosen
  from Study M's accuracies (problems 1-200) so that A is the better buy before its swap and B after it, by the
  per-call cost of the paper's switch line. 4 conditions per seed.
- **Rule's priors and the told rates:** from Study M (problems 1-200, disjoint): A advertised 0.660, B 0.850;
  told q = 68/151, f = 11/239 (llama3.1:8b on the Qwen solvers); loud share rho = 0.10.
- **Strategies:** never check; always check and retry; CUSUM; the retrying rule told q and f; the retrying rule
  without labels; cross-check every call; the same rule told q and f; the rule (no labels, corrected criterion);
  buying B from the start.
- **Loss:** (spending + L x wrong answers kept + one mean service price x failed tasks) / tasks.
- **Seeds:** 7100-7119, run once. Unit: the seed (loss averaged over its 4 conditions).

## Hypotheses
- **H-L1.** The rule has lower loss than the retrying rule without labels (one-sided Wilcoxon, Holm with H-L3).
- **H-L3.** The rule has lower loss than never checking (one-sided Wilcoxon, Holm with H-L1).
- **H-L2.** The rule is within +3% of the retrying rule told q and f (upper bound of the 95% paired bootstrap CI).
- **Reported regardless of outcome:** the rule against buying B, always check, cross-check every call, CUSUM and
  the same rule told q and f (percentage and 95% CI); every strategy's wrong answers kept, failed tasks and checks
  per task; the rule's learned f against Study M's f; each service's accuracy on these problems.

## Disclosure
- The development check (`run dev`, seeds 7000-7004) was run on the cloud machine only on a synthetic answer
  table and with a fake model for `prepare`, to test the code. There are no real-model numbers from it.
- Study M's results (problems 1-200) were known when the priors and prices were set.
- Changes from the D1 design draft (16 Nov 2026): no function-calling wrapper (each task is a single service call,
  so a planner model would only forward the problem); one environment (E1, maths) instead of two; no
  simulator-prediction hypothesis (H-D5). These cuts were made for time, before any D1 result.

## Commit timing (added 20 Nov 2026, 22:20, before any D1 run with real models)
This file and `ereplan/agent_live.py` were written on 20 Nov 2026 between 00:00 and 00:45 and are unchanged since,
but they were committed only after the Study M2 report (20 Nov, about 21:15) had been seen. That report covers the
same 300 problems and shows the services' accuracies on them: qwen2.5:3b 0.687, qwen2.5:1.5b 0.607, phi4-mini 0.860,
and the checker's q and f on the two Qwen services. The design, prices, conditions, seeds and hypotheses were not
changed after seeing it. One consequence is stated in advance: the accuracy drop at the swap on these problems
(0.687 to 0.607) is smaller than in Study M (0.660 to 0.535), so in the condition (L = 100, price of B = 52) moving
to B may not pay even after the swap. No D1 strategy loss has been computed on real answers.

## What the outcomes would mean
- **H-L1 and H-L3 confirmed, H-L2 confirmed:** the simulator findings carry over to real tools with natural
  degradation.
- **H-L3 not confirmed:** with these services, paid checks do not pay against never checking; reported as such.
- **Buying B cheaper than the rule:** as on FreshQA, monitoring does not pay here; reported with the size.

## Known limits
- Small models (1.5B to 8B), one task type, prices and wrong-answer costs set by us.
- The degradation is natural in kind (a model swap) but we choose when it happens.
- The checker is weak on whole solutions (Study M: q about 0.45, f about 0.05).
