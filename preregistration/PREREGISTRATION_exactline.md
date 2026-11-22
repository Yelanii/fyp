# Pre-registration: the exact step cost in the switch line and decision value

**Written:** 20 November 2026, before the confirmatory run. The confirmatory run is done once, on the author's laptop.

## Why
A review of draft v0.9.2 (20 Nov 2026) pointed out that the switch line prices a tool at c/p per successful call
(plus wrong answers), which assumes a call is retried until it succeeds. In the paper's own failure model only loud
failures are retried, up to r_max times, and silent failures are accepted. The exact expected loss of one planned
step without a check is the loss of policy N in Theorem 1:

    l = (1 - p) rho,  s = (1 - p)(1 - rho),  calls = (1 - l^(R+1)) / (1 - l)
    cost = c * calls + L * s * calls + F * l^(R+1)

c/p over-counts calls (at p = 0.75, rho = 0.5: 1.33 instead of 1.14) and ignores the retry limit and the failed-task
cost. The rule's switching is its most important ingredient (ablation: +17.5% without it), so the size of this
approximation must be measured.

## Design (`run_exactline.py`, variant added by `apply_exactline.py`)
- **Evaluated rule:** the corrected rule (net protection value), `Rule_v5_x` with `EREPLAN_NETPV=1`, exactly as in
  the paper.
- **Variant:** `Rule_v5_exact`: identical, except that the exact step cost above replaces c/p + wrong answers in the
  switch line (both the current tool and the alternatives) and in the staying cost inside the decision value.
  The variant is off by default; no existing rule changes.
- **Also run:** never check; the retrying rule told q and f.
- **Grid:** the label-free-rule grid of the paper (64 conditions per seed: drop to 95/85/75/60%, q 0.8/0.95,
  wrong-answer cost 1x/3x a task, f 0.05/0.15, pi 0/1); check at 15% of the mean tool price.
- **Seeds:** 9300-9319, run once (5,120 runs). Unit: the seed.

## Hypotheses
- **H-E1 (equivalence).** The variant's loss is within +-1% of the evaluated rule's (the 95% paired bootstrap CI of
  the percentage difference lies inside -1% to +1%).
- **H-E2 (descriptive).** Two-sided Wilcoxon over the 20 seeds, variant vs evaluated.
- **H-E3.** The variant is within +3% of the retrying rule told q and f (upper bound of the 95% bootstrap CI).
- **Reported regardless of outcome:** loss, wrong answers kept, failed tasks and checks per task for every strategy;
  the difference in every (wrong-answer cost x degradation level) cell.

## What the outcomes would mean
- **H-E1 confirmed:** the approximation does not change the rule's loss beyond 1%; the paper keeps the evaluated
  rule, states the exact cost and reports this test.
- **H-E1 not confirmed, variant cheaper:** the approximation costs measurable loss; the paper reports the size and
  recommends the exact form.
- **H-E1 not confirmed, variant dearer:** the approximation happens to help; the paper reports it and does not
  claim the exact form is better.

## Disclosure
A development check on seeds 8000-8001 (cloud machine, 2 seeds, 512 runs) was run before this file was written, to
test the code. Its means were seen: variant 142.3 vs evaluated 142.2 (+0.07%); the variant checked more often (1.41
vs 0.52 per task) and kept fewer wrong answers (10.8% vs 13.0%). Those seeds are not used in the confirmatory test.
