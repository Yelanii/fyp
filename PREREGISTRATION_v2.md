# Pre-registration: revised rule v2 (written 21 October 2026, 14:25 Sri Lanka time, before any v2 result on seeds 20–39)

## Why there is a v2
The pilot of the proposal rule (v1) was NO-GO (see `PILOT_FINDINGS.md`). It showed two design
problems:
- the switch line ignores the loss from silent failures that slip through ("leaks");
- the decision value almost never acts, because the plan horizon is only 5 calls.

v2 changes exactly these two things and nothing else.

## The v2 rule
1. **Leak-aware switch line.**
   - The cost of staying on a tool per call is `price / p + (1 − p)(1 − ρ) · L_leak`. The cost of the
     best alternative is computed the same way.
   - The line is the success rate p at which staying for the remaining horizon costs as much as
     switching (alternative cost + switch cost). It is found by bisection.
   - Code: `leak_aware_line` and `LeakAwareRule` in `ereplan/strategies.py`.
2. **Plan horizon u = calls left in the run, capped at 50** (not calls left in the current task),
   because the chosen tool is kept across tasks.
3. **Everything else is unchanged from v1.**
   - The same estimator, three zones, protection value, decision value and random audits.
   - The 95% range level is unchanged.

## The test (unchanged from the proposal, Table 3.16)
- **Settings:** q ∈ {0.5, 0.8}; check price 15% or 30% of the mean tool price; leak loss = one task's
  cost; scenarios S1–S3; three tools.
- **Strategies:** v2 rule, B1, B2, B3, B4, B8. B6 (oracle) and v1 are shown for reference only.
- **Tuning:** seeds 50–59, at most 8 configurations per strategy.
  - v2 tunes window ∈ {30, 60}, ε ∈ {0.02, 0.05} and k ∈ {3, 5}.
  - The session cap is fixed at 50, not tuned.
- **Judging: fresh seeds 20–39.** These were never used before. Test seeds 100–129 stay untouched.
- **GO criteria (identical to v1):**
  1. At least 5% lower median cost per successful task than the best non-oracle baseline, with
     paired Wilcoxon p < 0.05, in at least 2 of 3 scenarios.
  2. No more false switches than that baseline.
  3. Under harmless drift (S3), no more checks than fixed-rate checking at an equal or lower leak
     rate, in settings where protection alone does not justify a check.
  - The metric definitions, including "false switch" (judged against the price-only true line), are
    not changed.
- **Decision rule:**
  - If GO, continue the original project with v2.
  - If NO-GO, switch to the backup question, "When does checking pay off for tool agents?".
  - No further changes to the rule or the scenarios before the supervisor meeting.

## Command
`python -m ereplan.pilot --rule v2 --judge-seeds 20-39`
