# Pre-registration: real-agent validation (written 21 October 2026, before ANY real-LLM data exists)

Run on the student's laptop with Ollama: planner and judge = the same local model (primary: qwen2.5:1.5b;
the exact model details are recorded automatically). Tasks: GSM8K test problems the planner solves with
healthy tools (up to 300). Judge calibrated on 60 tasks. Strategies are told the judge's catch rate measured
on OBVIOUS faults. After service A degrades, its silent faults are SUBTLE. Conditions: drop to {85%, 75%} x
leak loss {1, 3}; check price 15%; seeds 1000-1009; 120 tasks per run. Metric: total loss per task.

R1: the real judge catches subtle faults less often than obvious faults.
R2: rule v3 has lower total loss than rule v2 (pooled over the 4 conditions, one-sided paired Wilcoxon p < 0.05).
R3: rule v3 has lower mean total loss than both always-check and never-check (pooled).
R4: always-check has higher mean total loss than never-check in at least 2 of the 4 conditions
    (false reassurance in a real setting; expected only if R1 holds clearly).
All four are reported whatever the outcome. Pipeline tests with `--model stub` are not data.

## Amendment 1 (22 October 2026, before any judge or strategy data existed)
A trial `plan --n 20` with qwen2.5:1.5b showed the zero-shot planner prompt solved only 20 of 150 problems
(13%), mostly because the small model ignored the line format. Changes, made after seeing ONLY planner output:
(1) two invented worked examples (not GSM8K problems) were added to the planner prompt; (2) the parser now
tolerates markdown, numbering, LaTeX brackets and a trailing "= result", and stops at the first "answer" line;
(3) the run uses 100 kept tasks (`--n 100`), within the "up to 300" stated above. R1-R4, conditions, seeds and
metrics are unchanged.

## Run 1 outcome (22 October 2026, qwen2.5:1.5b, 100 tasks kept of 397 tried)
- **Judge calibration:** catch obvious 1.00, catch subtle 1.00, false alarms 0.94. The yes/no judge answers
  "wrong" to almost every result, correct or not.
- **R1–R4, as pre-registered:**
  - R1 not met (1.00 vs 1.00);
  - R2 met (84.4 vs 86.6, p = 0.021);
  - R3 not met (84.4 vs 87.3 and 83.6);
  - R4 met (2 of 4).
- **Validity:** the manipulation that R1 assumes (a working but imperfect checker) did not occur. R4 is
  "met" because false alarms make always-check fail tasks, not because of false reassurance (correlated
  misses). Run 1 is therefore reported as a failed manipulation check. Its R2–R4 outcomes are not
  evidence for or against the hypotheses. The results folder is kept unchanged.
- **Second flaw found:** the pre-registered metric charges nothing for a task that ends in a known
  failure. With a 94%-false-alarm judge, that hides the cost of always-check. In the simulations,
  known failures are under 2% of tasks, and charging one task cost for them changes the check-worth
  map's median savings by at most 0.6 percentage points (re-scored from the saved rows).

## Amendment 2 (22 October 2026, written after Run 1, before Run 2)
1. **Two judges are calibrated:**
   - `yesno`, the original prompt;
   - `recompute`, where the model computes the expression and the check flags a mismatch above a
     tolerance of 1e-6·|value| + 0.005; an unparseable answer raises no alarm.
2. **Validity gate:** a judge is valid if its false-alarm rate is ≤ 0.30 and its obvious-fault catch
   rate is ≥ 0.50. The run uses the valid judge with the lowest false-alarm rate. If no judge is valid,
   the run does not start, and that is reported as the outcome.
3. **Primary metric:** total loss = (spend + leak loss × leaks + one task cost × failed tasks) / tasks.
   The pre-registered metric is reported alongside it for the same runs.
4. **Unchanged:** R1–R4, conditions (drop {85%, 75%} × leak loss {1, 3}, check price 15%), seeds
   1000–1009, 120 tasks per run, and the 100 kept plans from Run 1. The strategies are told the chosen
   judge's catch rate on obvious faults.
