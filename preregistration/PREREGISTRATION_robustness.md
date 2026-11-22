# Pre-registration: does the cross-check survive when its assumptions fail? (S1)

**Written:** 13 November 2026, before any run of this design. Runs on the author's laptop.

## Why
The IEEE Access review of draft v0.2 (12 Nov 2026) rated methodological soundness 4/10. Its main objection: the
cross-check treats "two tools agree after a flag" as evidence of a false alarm without establishing when this is
valid. The inference needs three assumptions (paper v0.3, Section IV):
- **A1** two wrong answers rarely agree (shared-mistake rate sigma is small);
- **A2** when the answers disagree, the alternative is more likely right;
- **A3** the comparison of two answers is reliable (comparison error rate e is small).

Theory already in the project (CORE4_2026-10-31.md, Proposition 3): a shared mistake does not change the loss of
the cross-check step itself, because both branches keep a wrong answer. Sigma can only hurt through what the rule
learns. Until now this was tested only on 4 development seeds, up to sigma = 0.6, and never together with e.
This test breaks A1 and A3 deliberately, on fresh seeds, up to sigma = 0.9.

## Revision before the confirmatory run (13 Nov 2026, after the smoke test)
The first design used the `drop_*` scenarios, where only tool A degrades. The smoke test (seeds 6000-6001) gave
bit-identical results at sigma = 0 and sigma = 0.9. Reason: a shared mistake needs the flagged answer AND the
alternative to be wrong on the same step, and in those scenarios the alternative is healthy, so it almost never
happened. The design could not test A1. It was revised before any confirmatory seed was used.

This also qualifies the 31 Oct development result in CORE4 ("sigma makes no difference to loss"): it was measured in
the same `drop_*` scenarios, where shared mistakes could barely occur, so it is not evidence that sigma is harmless.

## Design (revised)
- Code: `ereplan/v5_exp.py` unchanged; driver `run_robustness.py`. Simulator settings `xc_shared` (sigma) and
  `xc_noise` (e), both existing since 31 Oct and 27 Oct.
- Scenarios: `drop_0.75` (only A degrades: reference, where sigma can barely act); `alt_S3_indep` (A and B degrade
  at unrelated times); `alt_S4_common` (shared cause: A and B degrade together, the setting where shared mistakes
  are most plausible).
- Conditions per seed (108): scenario (3) x sigma {0, 0.5, 0.9} x e {0, 0.1, 0.2} x q {0.8, 0.95} x wrong-answer
  cost {1, 3}. Fixed: f = 0.15, pi = 1 (the real-checker profile), check price 15%.
- Strategies: never; v4 told q and f (retries); v4 without labels; cross-check every call; v5 (the proposed rule,
  no labels).
- Seeds: smoke test 6000-6001 (bug-finding only). Test: **6100-6119**, run once.
- Metric: total loss per task. Unit: the seed. One-sided paired Wilcoxon; 95% bootstrap CI.

## Hypotheses (two-tool-degradation scenarios pooled: alt_S3_indep and alt_S4_common)
- **H-S1 (A1, equivalence):** with e = 0, v5's loss at sigma = 0.9 is within +2% of its loss at sigma = 0
  (upper 95% CI bound of the change <= +2%).
- **H-S2 (worst case still useful):** at sigma = 0.9 and e = 0.2, v5 has lower loss than v4 without labels.
- **H-S3 (worst case, non-inferiority):** at sigma = 0.9 and e = 0.2, v5 is within +3% of v4 told q and f
  (upper 95% CI bound <= +3%).
H-S2 is a one-sided Wilcoxon test at alpha 0.05. H-S1 and H-S3 are judged by their 95% bootstrap intervals, as
equivalence and non-inferiority tests.

Descriptive: the full scenario x sigma x e map of v5 against each baseline; v5's learned f against the true f.

## Reading the outcomes
- All confirmed: the cross-check is robust to both broken assumptions in this simulator, and Proposition 3 holds
  empirically. The paper can state its assumptions and show they are not critical.
- H-S1 not confirmed: shared mistakes do hurt, through learning; the paper must say so and give the sigma at which
  the rule stops paying.
- H-S2 or H-S3 not confirmed: there is a region where the cross-check should not be used; the map shows where, and
  the paper reports it as a limitation.
