# Pre-registration: do larger local checkers repeat their false alarms?

Written before any of these checker answers is collected, and committed to the repository before the run.

## Why

Two Qwen2.5 checkers (1.5B and 3B) repeated most of their false alarms when sampled at temperature 0.7 (part E3 of `PREREGISTRATION_persistence.md`). At temperature 0 a repeat follows by construction. A review asked whether larger checkers behave the same way, and what exactly is repeated. This test measures persistence at temperature 0.7 for the two larger local models already used in this project, with the same input asked again each time.

A paid API checker is outside the project's zero-cost constraint, so it is not included.

## Design

**Checkers.**
- `llama3.1:8b` and `phi4-mini`, run through Ollama (4-bit, as distributed). These are the two primary checkers of this test.
- `qwen2.5:1.5b` and `qwen2.5:3b` are run with the same protocol for comparison. They are descriptive only.

**Items.**
- The correct calculator steps of the first 300 planned GSM8K tasks in `data/processed/gsm8k_plans_qwen2.5_1.5b.json` (276 steps).
- Every step is correct, so every flag is a false alarm.

**Check.**
- The recompute checker of the GSM8K agent (`ereplan/realagent.py`, `Judge`, kind `recompute`). The checker computes the expression itself, and a mismatch with the correct value is a flag.
- The prompt contains only the expression, so every repeat shows the checker exactly the same input.
- Each step is asked K = 8 times at temperature 0.7, with sampling seeds 1 to 8.

**Command, for each checker:**

```
python -m ereplan.realagent repeat --model qwen2.5:1.5b --judge-model <checker> --cal-n 300 --k 8 --temps 0.7
```

**Measures.**
- The false-alarm rate.
- The re-flag rate: P(flag on ask j+1 | flag on ask j), over consecutive asks.
- The flag rate after no flag.
- The share of steps flagged on every ask.

## Hypotheses

**Superiority.** One-sided Fisher exact test, with Holm's correction across the two primary checkers at alpha = 0.05.
- **H-L1 (llama3.1:8b):** the re-flag rate after a false alarm exceeds the flag rate after no flag.
- **H-L2 (phi4-mini):** the same.

**Descriptive only:** the re-flag rates with Wilson 95% intervals, and the Qwen2.5 comparison rows.

## What the outcomes would mean

- **Confirmed, with high re-flag rates:** persistence is not limited to the two small Qwen checkers. Check-and-retry is expected to fail in the same way with these larger checkers.
- **Not confirmed, or low re-flag rates:** larger checkers sample their verdicts more independently at temperature 0.7. The paper then narrows the persistence claim to the checkers and temperatures where it was observed.

A checker with too few false alarms (fewer than 20 flagged asks) gives no usable estimate, and that is reported as such.
