# Pre-registration: FR21/C5 ablation of rule v5.1

**Written:** 9 November 2026, before any multi-condition run of the ablation variants. `tests/test_ablation_v51.py`
(unit tests only, synthetic/tiny settings, no condition grid) existed before this document; no condition-grid or
seed-grid result has been looked at before writing this.

## Why
The proposal's C5 promises an ablation of rule v5.1 (FR19): remove one of its five ingredients at a time and show
each removal raises total loss. This tests that promise directly, rather than relying on the unit tests (which
check mechanism, not loss).

## The five ingredients and how each is removed (`ereplan/ablation_v51.py`)
1. **False-alarm term** -- `Rule_v5_1_nofa`: `fa_cost` forced to 0 in the check decision.
2. **Persistence handling (cross-check)** -- `Rule_v5_1_noxc`: `crosscheck = False`; a flag is resolved by a plain
   retry (rule v4's way) instead of a cross-check.
3. **Switching** -- `Rule_v5_1_noswitch`: `decide()` always called with `allow_switch=False`.
4. **Label-free learning** -- `Rule_v5_1_told`: checker memory replaced by `_FixedMemoryS`, a point mass at the
   told (q, f); third source and audit also disabled (nothing left for them to calibrate).
5. **Change detection** -- no new class; `Rule_v5_1` itself run with `window=1_000_000` so its estimator never
   forgets and cannot react to a change.

**Design choice stated in advance:** removing ingredient 2 is implemented as switching off cross-checking
entirely (reverting to plain retry), not as "cross-check but assume no shared mistakes," because persistence
protection in v5.1 is a property of cross-checking itself (PREREGISTRATION_v5.md, H-V5) -- there is no smaller
sub-mechanism to isolate. This mirrors the matching design note already in `ablation_v51.py` and needs the same
supervisor sign-off flagged for Rule_v5_1's own design choices (see README decision log).

## Design
- **Simulator:** unchanged; `ablation_v51.py` only subclasses `Rule_v5_1`. `test_ablation_v51.py`'s 6 unit tests
  (reproducibility, mechanism checks per variant) pass before this run.
- **Conditions (32):** drop in {95, 85, 75, 60}%; q_true in {0.8, 0.95} (q_assumed = q_true, i.e. the full rule's
  own prior starts correct -- the ablation is about the five ingredients, not miscalibration); false_alarm (f) in
  {0.05, 0.15}; fa_persistence (pi) in {0, 1}. Fixed across all conditions: check_frac 0.15, leak_mult 1.0,
  xc_shared 0.4 (shared mistakes are common enough for the false-alarm and persistence ingredients to matter),
  third_source_frac 0.3, audit_frac 0.05, third_shared 0.02 (all proposal defaults), n_tasks 200.
- **Seeds:** development 1750-1755 (smoke test only, to find bugs; nothing tuned on it; a change after the smoke
  test is allowed only to fix a bug, and would be reported). Test: **1800-1819**, run once, not re-run.
- **Strategies:** `full` = Rule_v5_1; `nofa`, `noxc`, `noswitch`, `told` = the four classes above; `nowindow` =
  Rule_v5_1 with window=1,000,000 (ingredient 5).
- **Metric:** total loss per task (spend + leak loss x leaks + one task's cost x failed tasks), as in all prior
  pre-registrations in this repo.
- **Unit of analysis:** the seed (mean over the 32 conditions); n = 20. Paired one-sided Wilcoxon signed-rank
  tests (alternative: full < ablated); Holm correction over the 5 primary tests; 95% bootstrap CI of the percentage
  difference.

## Hypotheses
**Primary** (Holm-corrected over the five):
- **H-A1:** full has lower total loss than `nofa`.
- **H-A2:** full has lower total loss than `noxc`.
- **H-A3:** full has lower total loss than `noswitch`.
- **H-A4:** full has lower total loss than `told`.
- **H-A5:** full has lower total loss than `nowindow`.

No minimum effect-size margin is pre-specified for these (unlike H-V1/H-V2 in PREREGISTRATION_v5.md): C5 asks only
that removing an ingredient *raises* loss, not by how much. The bootstrap CI is reported for every hypothesis so a
statistically significant but practically tiny rise can be read as such, honestly, rather than hidden behind a
single pass/fail mark.

**Secondary (descriptive, no confirmatory claim):**
- **H-A6:** the five ablations are NOT equally harmful; report the ranked mean loss increase, so the most load-
  bearing ingredient(s) can be identified. This is exploratory and is reported as such.

## How results will be read
- All five primary hypotheses confirmed: FR19's five ingredients each contribute to the loss reduction, as C5
  claims; a direct, defensible ablation result for the report.
- Any primary hypothesis NOT confirmed: that ingredient's contribution could not be demonstrated at these
  conditions/seeds and would be reported as a negative result, not omitted or re-run with different conditions
  to force significance. A plausible reason would be investigated and reported (e.g., ingredient 5 depends on a
  scenario containing an actual change -- `drop_x` scenarios here all contain one sudden mid-run drop, so this
  risk is judged low, but is noted here in advance rather than discovered and rationalised after the fact).
- H-A6 is read descriptively only; it does not get a CONFIRMED/NOT CONFIRMED verdict.

## What is NOT claimed
This ablation does not re-test FR19's own primary claims (rule v5.1 beating rule v5/v4/the cross-check baseline --
that is PREREGISTRATION_v5.md's and FR19's own confirmatory work, not repeated here) and does not validate the
sigma-hat estimator's absolute accuracy in full simulation (flagged as an open limitation in the README decision
log, 6 Nov 2026 entry) -- only that removing each named ingredient from the already-built rule raises loss.

## Outcome (added after the run, 9 November 2026; results/ablation_confirm_20261109-202104)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-A1 full < no false-alarm term | 131.9 vs 134.9 (+2.3%), p = 9.5e-07 | CONFIRMED |
| H-A2 full < no cross-check | 131.9 vs 132.2 (+0.2%), p = 0.0086 | CONFIRMED (tiny effect) |
| H-A3 full < no switching | 131.9 vs 156.1 (+18.3%), p = 9.5e-07 | CONFIRMED |
| H-A4 full < told q and f | 131.9 vs 131.7 (-0.1%), p = 0.92 | NOT CONFIRMED |
| H-A5 full < no change detection | 131.9 vs 135.8 (+3.0%), p = 9.5e-07 | CONFIRMED |

H-A4 read correctly: being told q and f is no better than learning them, so label-free learning costs nothing here; it
is a convenience (no labelled calibration), not a source of lower loss.
