# Pre-registration: FR20 confirmatory test (learning the loud-failure share rho)

**Written:** 9 November 2026, before any multi-condition run. `ereplan/rule_rho.py` (`LoudShareRule` and its
three mode variants) was built 31 Oct 2026 and renamed 6 Nov 2026; it had no confirmatory test of its own before
this document. `tests/test_rho_belief.py` (5 unit tests, synthetic/isolated, no condition grid) was added 9 Nov
2026, immediately before writing this document, to support the mismatch design below; it is not itself a test of
the hypotheses here.

## Why
Rules v4 and v5 (and FR19's rule v5.1) all assume a fixed share of failures are "loud" (seen for free, e.g. an
error message) versus silently wrong: rho, defaulted to 0.5. `ereplan/rule_rho.py`'s own module docstring notes
the motivating case: on FreshQA-grounded runs, stale answers are always silent (rho = 0), so a rule that still
assumes rho = 0.5 misreads the absence of error messages as health, checks rarely, and keeps many wrong answers.
FR20 (`LoudShareRule`, registry name `Rule_v5_rho`) learns rho from checked calls instead of assuming it. This is
a different mechanism from FR19/rule v5.1 (which is about a third source and shared mistakes) and has not yet
been tested across a condition grid against a FIXED-but-wrong rho assumption -- only in isolated unit tests
(`test_rho_belief.py`) that check the plumbing, not loss.

## A new mechanism needed to test this honestly
Until today, `ereplan/runner.py`'s `run()` passed one `Setting` object to both the environment (which generates
failures at the TRUE rho) and the strategy (whose belief starts from that same object's rho) -- so there was no
way to simulate "the rule wrongly assumes rho = 0.5 while failures are actually mostly silent," which is exactly
the motivating scenario. A 3-line, additive change to `run()` (9 Nov 2026) adds an optional `rho_belief` override
in `params`: when given, the STRATEGY is constructed with `s.with_(rho=rho_belief)` while the ENVIRONMENT keeps
the original `s` (true rho). `rho_belief` defaults to `None`, which reproduces the old behaviour exactly (checked
by the full existing test suite, 62/62 passing unchanged before this addition, 67/67 after adding the 5 new
`test_rho_belief.py` tests). This is the mechanism `run_rho.py` uses below.

## Design
- **Primary conditions (48), true rho deliberately mismatched with the old fixed assumption:** true rho in
  {0.0, 0.1, 0.3} (all more silent than the old default); drop in {95, 85, 75, 60}%; q_true = q_assumed in
  {0.8, 0.95}; false_alarm in {0.05, 0.15}. Fixed: check_frac 0.15, leak_mult 1.0, xc_shared 0 (FR20 is tested in
  isolation from FR19's shared-mistake mechanism), n_tasks 200. All strategies given the WRONG starting/fixed
  belief rho_belief = 0.5 (the old default) except `told` (given the true rho directly, as an oracle upper
  bound).
- **Sanity conditions (16), reported separately and descriptively only, no confirmatory claim:** the same grid at
  true rho = 0.5 (i.e. the old assumption happens to be right). The expectation stated in advance: here learning
  should neither help nor hurt materially, since there is nothing wrong to learn away from.
- **Seeds:** development 1850-1855 (6 seeds, smoke test only, nothing tuned). Test: **1900-1919** (20 seeds), run
  once.
- **Strategies:**

  | Key | Class | rho belief | Learns? |
  |---|---|---|---|
  | fixed | Rule_v5_x | 0.5 (wrong in primary conditions) | no |
  | told | Rule_v5_x | true rho (oracle) | no |
  | rho_cap | Rule_v5_rho | starts 0.5, cap mode (never exceeds 0.5) | yes |
  | rho_mean | Rule_v5_rho_mean | starts 0.5, posterior-mean mode | yes |
  | rho_lcb | Rule_v5_rho_lcb | starts 0.5, lower-credible-bound mode | yes |
  | rho_noaudit | Rule_v5_rho_noaudit | starts 0.5, cap mode, no extra audits | yes |

- **Metric:** total loss per task, as in all prior pre-registrations here.
- **Unit of analysis:** the seed (mean over the 48 primary conditions, or the 16 sanity conditions separately);
  n = 20. Paired one-sided Wilcoxon signed-rank tests; Holm correction over the two primary hypotheses; 95%
  bootstrap CI of the percentage difference.

## Hypotheses
**Primary** (Holm-corrected over the two, primary conditions only):
- **H-R1:** rho_cap (FR20's proposal default mode) has lower total loss than fixed (the old, wrong, constant
  rho = 0.5 assumption).
- **H-R2:** rho_cap is within 5% of told (the oracle, upper 95% bootstrap bound <= +5%) -- learning the loud
  share costs little relative to being handed it directly.

**Secondary (descriptive, no confirmatory claim):**
- **H-R3:** rank rho_cap, rho_mean, rho_lcb, rho_noaudit by mean loss, to see whether the cap, the extra audits,
  or neither matters much in practice.
- **H-R4:** accuracy diagnostic -- median |rho_hat - true rho| at the end of a run, for rho_cap, reported with no
  pass mark (descriptive, like H-V6 in PREREGISTRATION_v5.md).
- **Sanity check (true rho = 0.5 conditions):** |loss(rho_cap) - loss(fixed)| as a fraction of fixed's loss, to
  confirm learning does not materially hurt when the old assumption already happened to be correct. Reported
  descriptively; a result outside a small band (say 5%) would be investigated and reported, not hidden.

## How results will be read
- H-R1 and H-R2 confirmed: FR20's rho-learning mechanism removes the need for a correct hardcoded rho assumption
  without a material extra cost -- the direct motivating claim for FR20.
- H-R1 not confirmed: the fixed default of 0.5 is not actually harmful enough in this grid to matter, which would
  undercut FR20's stated motivation and would be reported as such, not re-run with a more extreme true-rho value
  to force significance (any change to the grid after seeing results would itself be reported).
- H-R2 not confirmed: learning rho has a real cost relative to being told it directly; worth reporting honestly
  alongside FR19's own label-free-learning ablation result (H-A4, PREREGISTRATION_ablation_v51.md), which found
  the opposite for q and f.

## Outcome (added after the run, 10 November 2026; results/rho_confirm_20261110-022819)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-R1 rho_cap < fixed wrong rho | 145.5 vs 150.4 (-3.2%, CI -4.0% to -2.5%), p = 9.5e-07, 20 seeds | CONFIRMED |
| H-R2 rho_cap within 5% of told | 145.5 vs 147.4 (-1.2%, CI upper -0.4%) | CONFIRMED |

Descriptive: rho_noaudit 145.4, rho_mean 145.5, rho_lcb 149.1; median error of rho_hat 0.083; when the old belief was
right (rho = 0.5) learning cost +2.0%. **Limit found later:** on FreshQA with real judges the gain did not carry
over (PREREGISTRATION_freshqa.md, H-F3 not confirmed).
