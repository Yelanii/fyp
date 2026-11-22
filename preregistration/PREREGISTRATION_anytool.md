# Pre-registration: FR18, any tool can degrade (rule v6)

**Written:** 10 November 2026, before any multi-condition run. Unit tests only (`tests/test_v6.py`, seeds 7-59,
mechanism checks: v6 re-tests and switches back; no loss comparison with baselines was looked at).

## Why
On FreshQA (PREREGISTRATION_freshqa.md) "buy the fresher tool from the start" beat the rule. That baseline needs
to know in advance which tool will stay good. This test asks the complementary question the proposal named as the
fallback claim: **when it is not known which tool will degrade, does monitoring beat committing to any one tool?**

## Design
- **Scenarios (new, `ereplan/env.py`):** `any_one` (one of the three tools, chosen at random per run, drops to 60%
  at a random time), `any_two` (two random tools drop at unrelated times), `any_recover` (one random tool drops and
  is repaired 200 calls later). Tools and prices as always: A 20, B 24, C 30.
- **Checker:** q in {0.8, 0.95}, f = 0.15, verdicts repeat (pi = 1), the profile of the real checkers measured in
  this project. Wrong-answer cost {1, 3} tasks. Check price 15%. 12 conditions per seed.
- **Proposed rule: v6** (`ereplan/rule_v6.py`) = rule v5 plus re-testing a tool it has left (forgetting after 150
  calls, doubling each time the tool is left again). H = 150 was fixed before any run and is not tuned.
- **Comparators:** fixed tool A, B, C (never check; "buy tool X"); never check (can still switch on loud errors);
  CUSUM; cross-check everything; v4 (told q and f); v5.
- **Seeds:** smoke test 4900-4905 (bug-finding only). Test: **5200-5219**, run once.
- **Unit and tests:** the seed (mean over 12 conditions); one-sided Wilcoxon; 95% bootstrap CI.

## Hypotheses
Primary (Holm over the five):
- **H-N1a, b, c:** v6 has lower total loss than fixed tool A, than fixed tool B, and than fixed tool C.
- **H-N2:** v6 has lower total loss than never checking.
- **H-N3:** on `any_recover`, v6 has lower total loss than v5 (re-testing pays when a tool is repaired).

Secondary: v6 vs v5 over all scenarios (95% CI reported; re-testing should not cost more than 2%); v6 vs the best
fixed tool chosen in hindsight per scenario (descriptive: an unfair comparator, since it uses knowledge nobody has).

## Reading the outcomes
- H-N1 (all three) and H-N2 confirmed: when no tool is reliably better, the rule beats committing to any tool.
  Together with the FreshQA result this fixes the boundary of the claim.
- Any H-N1 not confirmed: a fixed tool is as good as monitoring even here; reported, and the contribution is then a
  boundary study only.
- H-N3 not confirmed: re-testing is not shown to help; v6 offers nothing over v5 and v5 remains the proposed rule.
- Stated limits: simulator only; drops are sudden and to 60%; cheap tool C never needs to be learned as "premium".

## Outcome (added after the run, 10 November 2026; results/anytool_confirm_20261110-213220)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-N1a v6 < fixed tool A | 148.6 vs 175.5 (-15.3%, CI -18.6% to -11.5%), p = 9.5e-06, 20 seeds | CONFIRMED |
| H-N1b v6 < fixed tool B | 148.6 vs 199.3 (-25.4%), p = 9.5e-07 | CONFIRMED |
| H-N1c v6 < fixed tool C | 148.6 vs 203.2 (-26.9%), p = 9.5e-07 | CONFIRMED |
| H-N2 v6 < never checking | 148.6 vs 149.1 (-0.3%, CI -2.4% to +1.6%), p = 0.52 | **NOT CONFIRMED** |
| H-N3 v6 < v5 on any_recover | 141.3 vs 141.2 (+0.1%), p = 0.61 | **NOT CONFIRMED** |

Secondary: v6 vs v5 overall +0.8% (CI +0.0% to +1.5%). As stated in advance, **v5 remains the proposed rule**;
re-testing (v6) is not shown to help and is kept only as a documented negative result.
Reading: when no tool is reliably better, an adaptive policy beats committing to any tool by 15-27%, and beats the
best fixed tool chosen in hindsight (175.5). But the gain comes from switching, not from paid checks: "never
check", which still switches on loud errors, does as well (half of all failures are loud in this simulator).
Descriptive split: at a wrong-answer cost of 3 tasks v5 is 0.9-1.7% below never; at 1 task, 0.9% below.
