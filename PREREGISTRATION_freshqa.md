# Pre-registration: FreshQA with two real judge families (FR16, FR17) -- the Core 1 confirmatory test

**Written:** 10 November 2026, after the development run below and before any run on seeds 2700-2719.

## What is being tested
The proposal's main claim on a testbed where degradation and checking are both real: FreshQA questions whose answers
really went stale between Nov 2025 and Apr 2026, judged by two small LLMs of different families (Phi-4 Mini,
Llama 3.1 8B; verdicts collected on the student's laptop at temperature 0 and cached, so this run calls no model).
The proposal states: "The main claim is accepted only if the rule beats simply using the better tool on FreshQA in
the pre-registered test; if it does not, this is reported as a negative result."

## What changed since the 1 Nov development findings (both conditions the proposal set)
1. The rule now learns the loud share rho (FR20, confirmed 10 Nov, PREREGISTRATION_rho.md).
2. The design varies how likely staleness is (tool A goes stale in 100 / 50 / 25% of runs) and the price gap
   (tool B costs 24 or 30; A costs 20).

## Development run (seeds 2500-2509, Phi-4 Mini only; results/freshqa_dev_20261110-202550) -- stated honestly
Mean loss: use_B 141.6; rho_noaudit 148.0; rho_mean 149.6; rho_cap 149.9; rho_lcb 153.7; v5 160.1; v4 161.0;
never 192.3. Learning rho cut v5's loss by about 6%, but **on development data the rule still loses to use_B
overall (+6%)**. It was ahead only where staleness is rare (25% of runs: 139.6 vs 141.6) and about level when B is
dearer (159.3 vs 157.3). So H-F1 below is expected to FAIL; it is tested anyway because the proposal promised it.

## Frozen design
- **Proposed rule:** `Rule_v5_rho` (cap mode, key `rho_cap`): the variant FR20's primary hypothesis confirmed. It was
  NOT the best on development data (rho_noaudit was, by 1.3%); it is kept so that "the rule" is the same object in
  every confirmatory test. rho_noaudit is run and reported descriptively.
- **Strategies:** never, use_B (buy the fresh tool from the start), always_x, v4 (told the judge's measured q, f),
  v5, rho_cap, rho_noaudit. All parameters as in earlier tests; nothing tuned on FreshQA.
- **Conditions per seed (24):** judge {Phi-4 Mini, Llama 3.1 8B} x stream {news, mixed} x stale in {100, 50, 25}%
  of runs x B price {24, 30}. Wrong answer = 3 tasks. `EREPLAN_FMAX=0.95`.
- **Seeds:** 2700-2719 (20, never used). Run once. (The old `confirm` range 2510-2529 in freshqa_real.py overlaps
  seeds used in exploration on 1 Nov and is therefore not used.)
- **Unit and tests:** the seed (mean over the 24 conditions); one-sided Wilcoxon; 95% bootstrap CI; Holm over
  H-F1 to H-F3.

## Hypotheses
- **H-F1 (the proposal's main claim):** rho_cap has lower total loss than use_B.
- **H-F2:** rho_cap has lower total loss than never checking.
- **H-F3:** rho_cap has lower total loss than v5 (learning rho helps with real verdicts).
- **H-F4 (secondary; subset chosen from development data, so weaker evidence):** where A goes stale in only 25% of
  runs, rho_cap has lower total loss than use_B. Tested alone at alpha 0.05, outside the Holm family.

## Reading the outcomes
- H-F1 confirmed: the main claim holds on real data.
- H-F1 not confirmed (expected): reported as a negative result. The claim is then limited to what H-F2 to H-F4
  support: monitoring beats not monitoring, learning rho improves the rule, and (only if H-F4 holds) the rule beats
  buying the better tool when degradation is unlikely. No re-run with other prices or staleness rates.
- Stated limit: when and whether A goes stale, question order and timeouts are simulated; the judges cannot detect
  staleness on fast-changing questions (J <= 0.06), so the rule's value here comes mainly from cross-checks and
  switching, not from the yes/no check.

## Outcome (added after the run, 10 November 2026; results/freshqa_confirm_20261110-204328)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-F1 rho_cap < use_B (main claim) | 154.5 vs 142.4 (+8.5%, CI +4.1% to +13.2%), p = 1, 20 seeds | **NOT CONFIRMED** |
| H-F2 rho_cap < never | 154.5 vs 194.1 (-20.4%, CI -24.3% to -16.6%), p = 9.5e-07 | CONFIRMED |
| H-F3 rho_cap < v5 | 154.5 vs 152.3 (+1.5%, CI -1.1% to +4.2%), p = 0.91 | **NOT CONFIRMED** |
| H-F4 rho_cap < use_B at 25% staleness | 140.5 vs 142.4 (-1.3%, CI -5.9% to +3.7%), p = 0.27 | **NOT CONFIRMED** |

Negative result, as the proposal said it would be reported. On FreshQA with real judges, simply buying the fresher
tool beats every adaptive rule overall. The rule was cheaper than use_B in only 2 of 12 cells (staleness 25% and B
at 30: news -3.3%, mixed -10.5%), which is descriptive only. The development gain from learning rho (about 6% over
v5 on seeds 2500-2509) did not replicate on fresh seeds. Both judge families give the same picture (rho_cap 154.0
and 155.1). What does hold: monitoring beats not monitoring by 20%, and retry-free rules (v5, rho) fail no tasks
while v4 fails 5.1%.
