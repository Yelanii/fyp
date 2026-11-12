# Pre-registration: FR11, CostBench with checker error rates taken from real checkers

**Written:** 10 November 2026, before any run of this design (not even a smoke test).

## Why
FR11 asks for CostBench tasks "with checker error rates taken from real checkers". The two CostBench studies so far
(PREREGISTRATION_costbench_v5.md and part 2) used a synthetic grid (q in {0.8, 0.95}, f in {0.05, 0.15}, pi in
{0, 1}). This test replaces that grid with the four checker profiles actually measured in this project.

## The four real checker profiles (all measured earlier, at temperature 0; nothing is re-measured here)
| Profile | Catch rate q | False-alarm rate f | Persistence pi | Source |
|---|---|---|---|---|
| Qwen2.5 1.5B, recompute judge, arithmetic steps | 0.981 | 0.143 | 1.0 | `judge_calibration_qwen2.5_1.5b.json`; part E3 (re-flag 2867/2867) |
| Qwen2.5 3B, recompute judge, arithmetic steps | 0.990 | 0.050 | 1.0 | part E3 `rows.json` setup block (re-flag 2124/2124) |
| Phi-4 Mini, plain yes/no judge, FreshQA (all questions) | 0.807 | 0.556 | 1.0 | `freshqa_judge_phi4-mini_plain.json` |
| Llama 3.1 8B, plain yes/no judge, FreshQA (all questions) | 0.759 | 0.516 | 1.0 | `freshqa_judge_llama3.1_8b_plain.json` |

**Stated limit (in advance):** the RATES are real, but they were measured on other tasks (arithmetic and question
answering). No model judged CostBench outputs themselves; this cloud machine cannot run Ollama. So this is
"CostBench with realistic checker quality", not "a real checker on CostBench". Whether these rates transfer to
CostBench outputs is untested.

## Design
- Code: `ereplan/costbench_v5.py` unchanged (same world, same nine strategies, all parameters frozen); a thin
  driver `run_fr11.py`. `EREPLAN_FMAX=0.95` so rule v5 can represent f above 0.5 (as in the FreshQA runs).
- Conditions per seed (128): 4 profiles x drop {95, 85, 75, 60}% x wrong-answer cost {1, 3} x price gap
  {native, X 20% cheaper} x check price {5%, 15%} of a tool call.
- Seeds: smoke test 1990-1991 (bug-finding only). Test: **2800-2817** (18, never used), run once.
- Metric and unit: total loss per task; the seed (mean over the 128 conditions); one-sided Wilcoxon; 95% bootstrap CI.

## Hypotheses
Primary (Holm over H-RC1 and H-RC3):
- **H-RC1** v5 (no labels) has lower total loss than v4_nocal (no labels).
- **H-RC3** v5 has lower total loss than always_x.
- **H-RC2** v5 (no labels) is equivalent to v4 told the true q and f: 95% CI of the difference within +/-3%.

Secondary, descriptive (no verdict): total loss of every strategy per profile, including **never**; v5's learned
f and q error per profile. Expectation stated in advance, not a hypothesis: with the two FreshQA judges
(q - f about 0.25, more than half of correct outputs flagged) a check carries little information, so the best
any rule can do may be to stop checking; if v5 does not beat `never` there, that is reported as a limit.

## Reading the outcomes
- H-RC1-3 confirmed: the CostBench part-2 claim (v5 without labels matches v4 with labels and beats v4 without)
  holds at real checker quality.
- Any not confirmed: reported as such; the synthetic-grid result is then not shown to carry over to real checker
  quality. No re-run with other profiles or prices.

## Outcome (added after the run, 10 November 2026; results/fr11_confirm_20261110-202709)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-RC1 v5 < v4_nocal | 111.0 vs 128.1 (-13.3%, CI -14.2% to -12.4%), p = 3.8e-06, 18 seeds | CONFIRMED |
| H-RC3 v5 < always_x | 111.0 vs 147.2 (-24.6%, CI -25.6% to -23.5%), p = 3.8e-06 | CONFIRMED |
| H-RC2 v5 equivalent to v4 told, +/-3% | 111.0 vs 110.9 (+0.1%, CI -0.2% to +0.4%) | CONFIRMED |

Descriptive limits: v5 beats never checking by only 1.2-3.0% per profile (2.3% Qwen 1.5B, 3.0% Qwen 3B, 1.3% Phi-4
Mini, 1.2% Llama 3.1 8B); its learned rates are poor (median error of f 0.11-0.15, of q 0.26-0.49). So the rule
decides well without estimating the checker well, and the gain over the no-label alternative comes mostly from
avoiding v4_nocal's repeated false alarms (15.3% failed tasks vs 0.1%).
