# Pre-registration: does an API-served checker repeat its false alarms?

Written before any of these checker answers is collected, and committed to the repository before the run.

## Why

Small local checkers (1.5B to 8B parameters) repeated 68 to 92% of their false alarms at temperature 0.7 (`PREREGISTRATION_persistence.md`, part E3, and `PREREGISTRATION_persist_larger.md`). A review asked whether a larger checker served through an API, as such checkers are commonly used, behaves the same way. This test measures persistence for a 120B open-weight model served by Groq's API, using the free plan only (no paid calls).

## Design

**Checkers.**
- Primary: `openai/gpt-oss-120b`, served by Groq (`--judge-model groq:openai/gpt-oss-120b`).
- Descriptive only: `openai/gpt-oss-20b`, served by Groq (`--judge-model groq:openai/gpt-oss-20b`).
- Both are reasoning models. Their thinking counts against the token limit, so each call allows at least 1,024 completion tokens and sets reasoning effort to low. The prompt is unchanged.
- The served model id and system fingerprint of every response are recorded in `data/processed/api_meta_<model>.json`.

**Items and check.** As in `PREREGISTRATION_persist_larger.md`:
- The 276 correct calculator steps of the first 300 planned GSM8K tasks in `data/processed/gsm8k_plans_qwen2.5_1.5b.json`. Every step is correct, so every flag is a false alarm.
- The recompute checker (`Judge`, kind `recompute`). The prompt holds only the expression, so every repeat shows the checker exactly the same input. An answer with no usable number raises no flag.

**Asks.** K = 4 per step at temperature 0.7, with seeds 1 to 4 (1,104 calls per checker). This is fewer than the 8 asks of the local test because the free plan allows about 1,000 requests and 200,000 tokens per model per day; the run may take two days, and it resumes from its cache.

**Command, for each checker** (with the free key in `GROQ_API_KEY`):

```
python -m ereplan.realagent repeat --model qwen2.5:1.5b --judge-model groq:openai/gpt-oss-120b --cal-n 300 --k 4 --temps 0.7
```

**Measures.**
- The false-alarm rate.
- The re-flag rate: P(flag on ask j+1 | flag on ask j), over consecutive asks, with a Wilson 95% interval.
- The flag rate after no flag.
- The share of steps flagged on every ask, among steps flagged at least once.

## Hypothesis

- **H-A1 (gpt-oss-120b):** the re-flag rate after a false alarm exceeds the flag rate after no flag. One-sided Fisher exact test at alpha = 0.05. Consecutive asks on one step are not independent, so the p-value overstates the evidence; the per-step shares are reported alongside.
- H-A1 is tested only if the checker makes at least 20 false alarms over its 1,104 asks. Otherwise it is reported as not estimable.
- **Descriptive only:** gpt-oss-20b, with the same measures.

## What the outcomes would mean

- **Confirmed, with a high re-flag rate:** persistence also holds for a much larger, API-served checker, so check-and-retry is expected to fail in the same way.
- **Not confirmed, or a low re-flag rate:** this checker samples its verdicts more independently, and the paper narrows the persistence claim to the small local checkers.
- **Too few false alarms to test:** on these arithmetic steps the larger checker rarely raises a false alarm at all. By Corollary 1 of the paper, the cost of persistence then is small whatever the re-flag rate, and the paper reports the false-alarm rate instead.

## Limits

One task type (single arithmetic steps), one provider, one temperature. Groq may update the served model; the recorded fingerprints show whether that happened during the run.
