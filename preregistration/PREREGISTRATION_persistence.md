# Pre-registration, part E: the cost of persistent false alarms (FR14) and baselines from the closest works (FR10)

Written 24 October 2026, 22:20 Colombo time, **before** the development tuning (seeds 1500–1505) and before any
test run (seeds 1400–1419). Code: `ereplan/litbaselines.py`, `ereplan/persistence_exp.py`; changes to
`config.py`, `env.py` and `runner.py`.

## Why
The literature review v3 (24 October) restated the gaps:
- **G2:** verifier false rejection and judge repeatability are already reported (VP-CONTROL Table III; VRR-Stop
  App. H.4; Norman et al. 2026). What is not quantified is what *persistent* false rejections cost inside a
  priced check-and-switch loop.
- **G1:** must be shown against baselines modelled on the closest works, not only generic ones.

## What was built and seen before writing this
- **Persistence dial pi** (`Setting.fa_persistence`): the chance that a retry, or a re-check of the same output,
  repeats the previous verdict.
  - pi = 1 and pi = 0 reproduce the old persistent and independent cases exactly (unit test).
  - The re-flag rate is pi + (1 − pi) f (unit test).
  - The real checkers map to the dial as follows:

    | Checker | Re-flag rate | Implied pi |
    |---|---|---|
    | qwen2.5:1.5b, T = 0 | 0.989 | about 0.99 |
    | qwen2.5:1.5b, T = 0.7 (f = 0.14) | 0.838 | about 0.81 |
    | qwen2.5:3b, T = 0 | 1.000 | 1.0 |
    | qwen2.5:3b, T = 0.7 (f = 0.05) | 0.763 | about 0.75 |

    The levels 0.8 and 1.0 below match these.
- **Rule_v4_pi:** rule v4 with an assumed persistence pi_hat in its false-alarm cost.
  - g = pi_hat + (1 − pi_hat) f.
  - FA = p̂ f [g^r_max · task cost + (1 + g + … + g^(r_max−1)) (price + check price)].
  - pi_hat = 1 is exactly rule v4 (unit test; the same random stream).
  - pi_hat = 0 is the VRR-Stop independence assumption.
  - No new tuned parameter.
- **Three baselines from the closest works** (adaptations stated in `litbaselines.py`):
  - **B9_vrr (VRR-Stop):** check every call; on a flag, re-ask the checker up to K times; accept from the
    posterior that assumes independent votes. It accepts if P(wrong) ≤ (price + check price) / leak loss.
  - **B10_pbandit (ParetoBandit):** Thompson-sampling router on price / success with geometric forgetting γ;
    buys checks at a fixed rate c; counts every flag as a failure. The budget pacer is omitted (there is no
    hard budget).
  - **B11_btm (Bench2Robust):** offline Beta memory at the advertised rate with n_off pseudo-calls; updated
    only between tasks; no forgetting; no checks.
- **New metrics:**
  - the cost split: failed-task cost, leak cost, tool and check spend, switch spend;
  - tasks failed with a false alarm;
  - re-checks per task.
- **Regression:** 60 sampled runs from `confirm_fa` and `famap` reproduce exactly. 20 unit tests pass.
- **Seen before writing (smoke test, dev seed 1500 only, one condition):** all strategies run. That one
  condition was drop 75%, q 0.95, leak 3:

  | Strategy | f = 0.15, pi = 1 | f = 0.15, pi = 0 |
  |---|---|---|
  | always | 200 | 170 |
  | v4 | 178 | 178 |
  | v4_ind | 187 | 167 |
  | B9 | 211 | 157 |

  No other results were seen.

## Design
**Grid:**
- drop {95, 85, 75, 60}%;
- q {0.8, 0.95};
- leak loss {1, 3} task costs;
- check price 15%;
- f = 0 (reference), and f {0.05, 0.15} × pi {0, 0.5, 0.8, 1.0}.

That gives 16 + 128 = 144 conditions. Common random numbers: every strategy, f and pi share each seed's
tool outcomes.

**Strategies:**
- never, always, CUSUM (as in part B);
- v4 (Rule_v4_fa, pi_hat = 1);
- v4_ind (pi_hat = 0);
- v4_match (pi_hat = true pi; in practice, measured by the repeat test of part D);
- B9_vrr, B10_pbandit, B11_btm.

Where a result cannot differ, it is copied, not re-run:
- never and B11 at f > 0 (they never check);
- v4_ind and v4_match at f = 0;
- v4_match at pi ∈ {0, 1}.

**Tuning (fixed now, run next).** Development seeds 1500–1505, on q 0.95, leak 3, all four drops, with f = 0,
and f {0.05, 0.15} × pi {0, 1}. Each baseline takes the configuration with the lowest mean total loss:
- B9: K ∈ {1, 2};
- B10: γ ∈ {0.95, 0.98, 0.995} × c ∈ {0, 0.2, 0.5};
- B11: n_off ∈ {20, 100}.

The v4 variants are not tuned. They keep v3's settings, as in part B. The chosen values are added below before
the test is run.

**Test:** seeds 1400–1419 (never used before). Metric: `total_loss_fail` (Amendment 2).

**Statistics:**
- one-sided paired Wilcoxon over (drop, q, leak, f, seed), α = 0.05;
- Holm correction for H-E6;
- the false-alarm cost of a strategy is its loss at (f, pi) minus its loss at f = 0, on the same seed.

## Hypotheses

**E1. Cost of persistence (FR14, RQ2, G2)**
- **H-E1:** for always-check, the false-alarm cost at pi = 1 exceeds that at pi = 0, pooled over f > 0.
  Requires p < 0.05, and the mean at pi = 1 must be at least 3 times the mean at pi = 0. Whether the cost
  rises with pi across {0, 0.5, 0.8, 1} is reported descriptively.
- **H-E2 (descriptive, no test):** the split of the false-alarm cost into failed tasks, leaks, tool and check
  spend, and switching, for always, v4, v4_ind and B9 at pi = 0 and pi = 1.
- **H-E3:** at pi = 1 (f > 0), v4's loss is at least 5% below v4_ind's, with p < 0.05. This tests whether
  modelling persistence matters.
- **H-E4:** at pi = 0 (f > 0), v4_ind's loss is below v4's, with p < 0.05. This is the crossover: each
  assumption wins in its own world. If not confirmed, v4's cautious cost is safe even when false alarms are
  independent.
- **H-E5:** at pi ∈ {0.5, 0.8} (f > 0), v4_match's loss is below both v4's and v4_ind's, with p < 0.05 for
  each. This tests whether calibrating pi pays at the persistence levels of sampled real checkers.

**E2. Baselines from the closest works (FR10, RQ3, G1)**
- **H-E6:** pooled over f > 0 and all pi, v4_match's loss is below each of B9, B10 and B11. Each comparison
  requires a Holm-corrected p < 0.05 and a pooled mean at least 5% lower.
- **H-E7 (no harm):** at f = 0, v4_match's pooled loss is no more than 2% above the lowest of B9, B10 and B11.
- **H-E8a:** at pi = 1, B9's false-alarm cost exceeds always-check's, with p < 0.05. Re-verification buys
  repeated identical flags.
- **H-E8b:** at pi = 0, B9's false-alarm cost is below always-check's, with p < 0.05. Re-verification works
  when verdicts are independent.

## How outcomes will be read
- **H-E1 confirmed:** the cost of a false alarm depends on its persistence, not only its rate, which supports
  the reworded G2. In simulation this mechanism is built into the environment. The empirical anchor is the
  measured re-flag rate of real checkers (part D). H-E1 quantifies the size of the effect; it does not
  discover the effect.
- **H-E3 and H-E5 confirmed:** measuring persistence (the repeat test) is worth doing before deploying a
  checking rule.
- **H-E6 not confirmed against B9:** if pooled performance favours re-verification, especially at low pi, this
  is reported as a limit of v4. Adding re-verification to v4 would then be future work, not done after seeing
  the test.
- All outcomes are reported whatever they are. Seeds 1400–1419 are not re-run with changed code.

## Tuned values (filled in after the development step, before the test; 24 October 2026, 22:22)
From `results/persist_dev_20261024-222106/tuned.json` (development seeds 1500–1505 only; mean dev loss):
- **B9_vrr:** K = 1 (161.75; K = 2: 163.64).
- **B10_pbandit:** γ = 0.98, c = 0.5 (182.37). Note: c = 0.5 is the edge of the pre-registered grid; the grid
  is not extended after seeing this.
- **B11_btm:** n_off = 20 (214.30; n_off = 100: 219.26).

**Code fingerprint at test time:** SHA-256 of `cat ereplan/*.py` begins `a96b553650d134ad`. The test is run once with this code.

---

## Outcome (test run 24 October 2026, 22:21–23:42; `results/persist_confirm_20261024-234247/`)
Seeds 1400–1419; 18,880 runs (the rest copied where results cannot differ); 4,882 s on 2 cores.

| Hypothesis | Result | Verdict |
|---|---|---|
| H-E1 | Always-check's false-alarm cost is 48.3 at pi = 1 vs 16.6 at pi = 0; ratio 2.9 against the 3.0 bar; p = 9.4e-107. It rises monotonically: 16.6, 34.4, 42.3, 48.3. | **NOT CONFIRMED** (bar narrowly missed) |
| H-E2 (descriptive) | At pi = 1, always-check's extra loss is almost all failed tasks (+46.6 of +48.3; 38.2% of tasks failed with a false alarm, against 2.4% at pi = 0). v4's extra loss is mostly leaks (+16.2), because it checks less (spend −8.8). | Reported |
| H-E3 | At pi = 1, v4 147.0 vs v4_ind 161.7 (−9.0%), p = 6.7e-83 | **CONFIRMED** |
| H-E4 | At pi = 0, v4_ind 143.9 vs v4 143.6 (+0.2%), p = 1 | **NOT CONFIRMED.** v4's cautious cost is safe even when false alarms are independent |
| H-E5 | At pi in {0.5, 0.8}, v4_match 146.7 vs v4 145.3 (p = 1) and vs v4_ind 154.2 (p = 2.5e-114) | **NOT CONFIRMED.** Calibrating pi did not beat assuming pi = 1 |
| H-E6 | f > 0, all pi: v4_match 146.1 vs B9 168.7, B10 175.2, B11 175.7; Holm and the 5% bar met for all three | **CONFIRMED** |
| H-E7 | f = 0: v4_match 137.2 vs the best literature baseline 140.9 | **CONFIRMED** |
| H-E8a | At pi = 1: B9's false-alarm cost 44.2 vs always-check's 48.3; the one-sided rank test gives p = 0.018 | **NOT CONFIRMED (mixed)**, see the note below |
| H-E8b | At pi = 0: B9 9.3 vs always 16.6, p = 1.4e-61 | **CONFIRMED** |

**Note on H-E8a (correction to the script's printed verdict).** The script printed "CONFIRMED" because it
checked only the p-value. The hypothesis says B9's cost *exceeds* always-check's, but the pooled mean is
lower (44.2 < 48.3). A breakdown, which was not pre-registered and is exploratory:
- At leak 3, where B9 actually re-checks, its false-alarm cost is higher in 100% of pairs (median +4.5) and it
  fails as many tasks (38.2%). The re-checks are wasted.
- At leak 1, B9's acceptance threshold lets it accept most flagged answers without re-checking. That avoids
  failures (15.8% vs 38.2%) and lowers its mean.

So the pre-registered statement is not supported overall. The mechanism (re-checks are wasted under
persistence) is seen only where re-verification happens.

**Exploratory (not pre-registered):** the lowest-loss strategy per condition at f = 0.15:
- at pi = 1: v4 in 12 of 16 conditions, never-check in 4 (the no-degradation drop of 95%, a known limit of v4);
- at pi = 0.8: v4 or v4_match in 12 of 16.

---

# Part E3: replication of H-E3 with the real LLM checkers (written 24 October 2026, 23:58 Colombo time, before running)

## Why
H-E3 (simulation) was confirmed: when false alarms persist, assuming persistence (v4) beats assuming independence
(v4_ind) by 9%. E3 asks whether this holds with the **real** checkers, where persistence is not built in but comes
from the model itself.

## Design (runs on the student's laptop; Ollama; CPU)
- **Planner and tasks:** qwen2.5:1.5b plans, the same 100 kept GSM8K tasks and the same tool and degradation
  model as Runs 2–3.
- **Checkers:** recompute judge with qwen2.5:1.5b and with qwen2.5:3b, at two temperatures.
  - **T = 0:** seed 0 for every attempt, so the answers are the Run 2/3 and part D answers. f is told from
    each model's T = 0 calibration file (0.14 and 0.05).
  - **T = 0.7:** attempt j uses seed j + 1 (1, 2, 3), so each retry is a fresh sample. f is told from each
    model's part D repeat-test false-alarm rate at T = 0.7 (newest `results/repeat_<model>_*.json`). q is
    told from the T = 0 calibration at both temperatures (stated limitation).
- **Strategies:**
  - never and always (context);
  - v4 (Rule_v4_fa);
  - v4_ind (Rule_v4_pi with pi_hat = 0). It shares v4's audit draws, so the pair differs only in the
    false-alarm cost.
- **Conditions:** drop {85, 75}% × leak {1, 3}. Check price 15%.
- **Seeds:** 4000–4009 (never used).
- **Command:** `python -m ereplan.realagent persist --model qwen2.5:1.5b --seeds 10 --seed-start 4000`.
- **Metric:** Amendment 2 total loss.
- **Code changes made for E3:**
  - `Judge.says_wrong(..., attempt)` uses seed + attempt only when T > 0. At T = 0 it is unchanged: a replay of
    Run 3 gives identical numbers with the old and new code (checked; 53 answers are missing from the cloud
    copy of the cache, the same for both).
  - New counters for false alarms seen in the loop and how often they repeat on the next correct attempt.
  - Unit test: 21 tests pass.

## Pre-registered checks
- **R-E3a (T = 0, both checkers pooled; 2 × 4 × 10 = 80 pairs):** v4's mean total loss is below v4_ind's, and
  one-sided paired Wilcoxon p < 0.05.
- **R-E3b (T = 0.7, both checkers pooled, 80 pairs):** the same comparison.
- **R-E3c (descriptive):** the in-loop re-flag rate after a false alarm, per checker and temperature,
  compared with part D: 0.989 and 1.000 at T = 0; 0.838 and 0.763 at T = 0.7.
- **R-E3d (descriptive):** always-check's share of failed tasks, per checker and temperature.

## How outcomes will be read
- **R-E3a met:** the simulation result H-E3 holds with real deterministic checkers.
- **R-E3a not met:** the 9% gain is a simulation result only. G2 then rests on simulation plus the measured
  persistence, and this is reported as a limit.
- **R-E3b:** shows whether assuming persistence is still right when sampling makes real checkers only partly
  persistent (simulation at pi = 0.8: v4 better).
- All outcomes are reported whatever they are.

## Seen before writing
A pipeline check in replay mode, with qwen2.5:1.5b only, on **development** seeds 4900–4901, in a scratch copy:
- At T = 0, 6 answers were missing from the cloud cache.
- At T = 0.7, a placeholder f = 0.2 was used and nearly all answers were missing (treated as "no alarm").
- Printed, and not informative because of the missing answers:
  - T = 0: v4 75.6 vs v4_ind 75.0;
  - T = 0.7: v4 75.0 vs v4_ind 76.2.

No test seed (4000–4009) has been run.

**Code fingerprint for E3:** SHA-256 of `cat ereplan/*.py` begins `07ccb744629cbcd6`.

## Outcome of part E3 (25 October 2026, student's laptop; seeds 4000–4009)
Command as pre-registered; 21 tests passed first. Results: `results/realagent_persist_20261025-004642/`.

Total loss per task, mean over drop {85, 75}% × leak {1, 3} × seeds:

| Checker | T | f told | never | always | v4 | v4_ind | always: failed tasks | in-loop re-flag after a false alarm |
|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b | 0 | 0.143 | 82.3 | 107.2 | 76.3 | 79.8 | 31.0% | 1.000 (2867/2867) |
| qwen2.5:1.5b | 0.7 | 0.149 | 82.3 | 106.6 | 76.3 | 78.5 | 26.7% | 0.920 (2552/2774) |
| qwen2.5:3b | 0 | 0.050 | 82.3 | 94.7 | 75.8 | 82.1 | 17.6% | 1.000 (2124/2124) |
| qwen2.5:3b | 0.7 | 0.057 | 82.3 | 96.6 | 75.7 | 82.4 | 17.2% | 0.825 (2123/2573) |

- **R-E3a MET:** T = 0, both checkers pooled (80 pairs): v4 76.1 vs v4_ind 81.0 (−6.1%); one-sided paired
  Wilcoxon p = 3.2e-12.
- **R-E3b MET:** T = 0.7, pooled (80 pairs): v4 76.0 vs v4_ind 80.4 (−5.5%); p = 1.6e-12.
- **R-E3c (descriptive):** in-loop re-flag rate 1.000 and 1.000 at T = 0 (part D: 0.989, 1.000); 0.920 and 0.825
  at T = 0.7 (part D: 0.838, 0.763). At T = 0.7 the in-loop rates are higher than in the part D repeat test. Not
  yet explained. One possible reason (hypothesis, untested): steps flagged inside the loop are the ones the
  checker finds hardest, and it re-flags those more consistently, whereas part D sampled all correct
  calibration steps.
- **R-E3d (descriptive):** always-check failed 31.0% / 26.7% of tasks with the 1.5B checker (T = 0 / 0.7) and
  17.6% / 17.2% with the 3B checker.

**Reading, as pre-registered:**
- R-E3a met: the simulation result H-E3 holds with real deterministic checkers.
- R-E3b met: assuming persistence is still the better choice when sampling makes the real checkers only partly
  persistent.
- The effect is smaller than in simulation (−5.5% to −6.1%, against −9%).

**Exploratory (not pre-registered):**
- In each of the four checker × temperature rows, v4 had the lowest mean loss of the four strategies, and
  v4 < v4_ind. This row-level pattern does not depend on treating the 80 pooled pairs as independent; they share
  seeds across conditions, so the pooled p-values are optimistic.
- With the 3B checker, v4_ind (82.1, 82.4) was no better than never-check (82.3): assuming independence removed
  the whole benefit of checking, while v4 kept about 8% (75.8 and 75.7 vs 82.3).

**Limits:**
- One planner and checker family (Qwen2.5) and one task family (GSM8K).
- Degradation and prices are simulated; only the planner and checker answers are real.
- q is told from the T = 0 calibration at both temperatures.

**Replay (25 October 2026, 01:44, cloud machine):**
- The run was replayed from the laptop's answer caches with the same code (`07ccb744629cbcd6`).
- Report identical; 0 cache misses; all 640 rows identical in every field.
- The 3B calibration file and the two part D repeat files were rebuilt from the `setup` block of `rows.json`.
- Details: `results/realagent_persist_20261025-004642/REPLAY.md`.

**Robustness (exploratory, computed after the run from `rows.json`; not pre-registered):**
- **Seed clusters.** The pooled 80 pairs share seeds, so the test was repeated with one value per seed (the mean
  over both checkers and all four conditions):
  - v4 was lower on 10 of 10 seeds at T = 0 and on 10 of 10 at T = 0.7;
  - one-sided Wilcoxon p = 0.00098 each, the smallest value possible with 10 pairs.
  - With 20 (checker, seed) clusters: 20 of 20, p = 9.5e-07.
- **Conditions.** v4's mean was lower than v4_ind's in all 16 checker × temperature × drop × leak conditions.
- **Leak split.** The gain is mostly where wrong answers are costly:
  - leak 3: −9.2% (82.1 vs 90.4);
  - leak 1: −1.5% (69.9 vs 71.0).
- **Mechanism, pooled over all rows:**

  | Strategy | Checks per task | Failed tasks | Leaked wrong answers |
  |---|---|---|---|
  | v4 | 0.16 | 0.9% | 9.4% |
  | v4_ind | 0.78 | 5.2% | 6.9% |

  - v4_ind checks about 5× more often and fails about 6× more tasks: its retries meet repeated false alarms.
  - v4 lets more wrong answers through. This is a priced trade-off, not a win on every harm.
- **3B checker.** With few false alarms (f = 0.05), v4_ind treats checking as cheap and checks 1.03 times per task
  (v4: 0.25). Each false alarm then repeats, so 5.8% of tasks fail (v4: 1.2%). The extra spend and failures
  cancel the benefit of fewer leaks, so total loss is 82.2, the same as never checking (82.3).
- **Mild degradation, cheap wrong answers.** At drop 85% and leak 1, never-check (68.6) was below both v4 (69.4)
  and v4_ind. This fits the RQ1 hump: checking pays least when degradation is mild and errors are cheap.
