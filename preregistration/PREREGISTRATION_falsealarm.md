# Pre-registration: false alarms and rule v4 (written 22 October 2026, 23:45 Colombo time, before running A–C)

## What prompted this
- In real-agent Run 2, the LLM checker (recompute judge) wrongly flagged 14% of correct steps (35 of about
  270). It flagged them again on every retry, because the model is deterministic at temperature 0.
- An audit of the cached answers found all 35 to be genuine arithmetic errors by the model, mostly an
  extra zero. None were parser errors.
- The simulator and rules v1–v3 assumed checks never flag a correct result.

## What was built and seen before writing this
- **Simulator:** `false_alarm` = f, persistent per step by default. A false alarm looks to the agent
  exactly like a caught failure. New metric: `total_loss_fail` = (spend + leak loss × leaks + one task
  cost × failed tasks) / tasks.
- **Rule v4** (`ereplan/fa_rule.py`) = rule v3 plus two changes:
  - a false-alarm-aware likelihood;
  - an expected false-alarm cost, p̂ · f · (task cost + r_max · (tool price + check price)), subtracted
    from the value of a check.
  - f is given, like q.
  - **No parameter was tuned.** Every v3 setting is reused unchanged.
- **Dev checks only:**
  - simulation seeds 1100–1105, 12 conditions;
  - real-agent cache replay seeds 2000–2004.
  - v4 was best or tied in most dev conditions. In simulation it lost to never-check when the tool did not
    degrade (drop 95%) with f > 0.
  - These seeds are not used below.

## A. Check-worth map with false alarms (descriptive, plus two hypotheses)
**Grid:**
- drop {95, 90, 85, 80, 75, 70, 60}%;
- q {0.8, 0.95};
- check price 15%;
- leak loss {1, 3};
- f {0, 0.05, 0.15}, persistent;
- seeds 1300–1309.

**Strategies:** never, always, CUSUM, v2, v4. **Metric:** total_loss_fail.

**Saving** = (never − best of {always, CUSUM, v2, v4}) / never, per cell (seed mean). Medians are taken over
q per drop level.

- **H-FA1 (the hump survives modest false alarms):** at f = 0.05 and leak 3, the median saving is largest
  at a drop in {80%, 75%, 70%}, and larger there than at both 95% and 60%.
- **H-FA2 (false alarms shrink the value of checking):** for each leak level, the median saving over all
  drops is lower at f = 0.15 than at f = 0.

## B. Confirmatory simulation test of rule v4 (seeds 1200–1219)
**Grid:** drop {95, 85, 75, 60}% × q {0.8, 0.95} × leak {1, 3} × f {0, 0.05, 0.15} × check price 15%.

**Strategies:** never, always, CUSUM, v2, v3, v4. **Metric:** total_loss_fail.

**Statistics:** paired by (condition, seed); one-sided Wilcoxon signed-rank; α = 0.05.

- **H-v4a:** with f > 0, v4 has lower total loss than v3. Requires p < 0.05 and a pooled mean at least 5%
  lower.
- **H-v4b:** with f > 0, v4 has lower pooled mean total loss than each of never, always and CUSUM, with
  p < 0.05 against each.
- **H-v4c (no harm):** with f = 0, v4's pooled mean is within 1% of v3's.

## C. Real-agent Run 3 (student's laptop, live Ollama, fresh seeds 3000–3009)
Same model, plans, judge and calibration as Run 2. Command:
`run --seeds 10 --seed-start 3000`. Conditions as in Run 2, with v4 told f = the calibrated false-alarm
rate (0.14).

**Metric:** the Amendment 2 total loss.

- **R5:** v4 has lower pooled total loss than each of never, always, CUSUM, v2 and v3. One-sided paired
  Wilcoxon over (condition, seed), p < 0.05 against each.
- **R6:** v4's mean is below never-check's in at least 3 of the 4 conditions.

All outcomes are reported whatever they are. Run 2 (seeds 1000–1009) is not re-used for these checks.

---

## Outcome of part C (Run 3, 23 October 2026, seeds 3000–3009)
- **R5 met:** v4 73.8 vs CUSUM 81.0, never 82.0, v3 86.4, v2 95.2, always 108.9; every p < 1e-5.
- **R6 met:** 3 of 4 conditions.
- Results in `results/realagent_qwen2.5_1.5b_20261023-161614/` (student's laptop).

## Part D: do persistent false alarms generalise? (written 23 October 2026, 17:00 Colombo time, before running)

**Motivation:**
- A literature check (23 October) found verifier false rejection documented in arXiv 2607.17641,
  2608.23941 and 2610.10062.
- One paper (arXiv 2605.05409, not yet verified by us) reports false rejections that mostly recover on
  retry.
- The likely reviewer objection: persistence is an artefact of one small, deterministic checker.

**Judges:**
- the recompute judge with qwen2.5:1.5b (Run 2);
- the recompute judge with **qwen2.5:3b**, the same family and twice the size.

Plans stay those of qwen2.5:1.5b, so the tasks are identical.

**D-repeat:**
- Command: `repeat --k 5 --temps 0,0.7`, on the correct results of the 60 calibration tasks
  (161 steps).
- Each step is asked 5 times per temperature (seeds 1–5).
- **Measures:**
  - false-alarm rate;
  - P(flag on try j+1 | flag on try j), the "re-flag rate";
  - P(flag | no flag before);
  - share of steps flagged every time.
- **D1 (persistence at T = 0):** the re-flag rate is ≥ 0.90 for both judge models.
- **D2 (randomness weakens persistence):** for both judge models, the re-flag rate at T = 0.7 is lower
  than at T = 0.

**D-size:**
- `calibrate --judge-model qwen2.5:3b` (same validity gate and choice rule as Amendment 2), then
  `run --judge-model qwen2.5:3b --seeds 10 --seed-start 3000`.
- **D3 (bigger checker, fewer false alarms):** the chosen judge's false-alarm rate is below 0.14.
- **D4 (v4 does not hurt with a better checker):**
  - v4's pooled total loss is at most 2% above the lowest of the other five strategies;
  - and it is below never-check and always-check (one-sided paired Wilcoxon, p < 0.05 for each).

**If D3 fails** (the 3B judge has as many false alarms or more), D4 is still reported.
**Licence note:** qwen2.5:3b is under the Qwen Research License (non-commercial), which is fine for this
research use. qwen2.5:1.5b is Apache-2.0.
All outcomes are reported whatever they are.

## Outcome of part D (23–24 October 2026, student's laptop)

**Re-flag rate P(flag | flag before)** on 161 correct steps, 5 asks each:

| Checker | T = 0 | T = 0.7 |
|---|---|---|
| qwen2.5:1.5b | 0.989 | 0.838 |
| qwen2.5:3b | 1.000 | 0.763 |

- **D1 met for both judges** (≥ 0.90).
- **D2 met for both judges** (lower at T = 0.7).
- **D3 met:** the 3b recompute judge's false-alarm rate is 0.050 < 0.14. The 3b yes/no judge is invalid
  (false alarms 0.52).
- **D4 met:**
  - with the 3b judge, v4 pooled 75.4 is the lowest (CUSUM 77.6, never 82.0, v3 84.3, v2 87.4, always 95.8);
  - v4 < never (p = 0.00025) and v4 < always (p = 1.8e-8).
- Results in `results/repeat_qwen2.5_1.5b_*.json`, `results/repeat_qwen2.5_3b_20261024-000129.json` and
  `results/realagent_qwen2.5_1.5b_judge_qwen2.5_3b_20261024-092223/`.
