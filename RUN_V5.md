# Rule v5: what to run on your laptop (real-checker pilot)

**What this tests:** the real Qwen checkers (1.5B and 3B, at temperature 0 and 0.7) with rule v5, which learns the
checker's error rates without labels and cross-checks flagged steps. It is compared with rule v4, which is told the
labelled calibration. The hypotheses are written in `PREREGISTRATION_v5.md` (real-checker pilot, R-V1 to R-V3).

## Step 1: Add the update (once)
Extract `ereplan-update-v5.zip` into your **inner** project folder (the one with `ereplan`, `tests` and `README.md`)
and choose **Replace**. It adds `ereplan/crosscheck.py`, `ereplan/bayes_opt.py`, `ereplan/v5_exp.py`,
`ereplan/bayes_exp.py`, `tests/test_v5.py`, `PREREGISTRATION_v5.md` and this file, and updates `ereplan/runner.py`,
`ereplan/realagent.py` and `ereplan/config.py`. Earlier results are unchanged: the new code is used only by the new
strategies.

## Step 2: Check (1 minute)
In PowerShell, in the inner folder, with `(.venv)` showing:
```
python -m pytest -q
```
You should see **26 passed**.

## Step 3: Run the real-checker pilot
Start Ollama first (`ollama serve` in another window, or the Ollama app). Then:
```
python -m ereplan.realagent v5 --seed-start 4100 --seeds 10
```
- It uses both checkers (qwen2.5:1.5b and qwen2.5:3b) at temperature 0 and 0.7.
- These are fresh seeds, so many checker answers are new. Expect **several hours** on a CPU.
- Leave the laptop plugged in and stop it from sleeping.
- Progress lines appear after each block (`... drop 0.85 leak 1.0: done`).
- If it stops (sleep, error), just run the same command again. Every answer already obtained is saved in the cache
  and is not asked again.

## Step 4: Send me the results
When it prints `Saved to results\realagent_v5_<time>`, send me:
1. `report.md` and `rows.json` from that folder;
2. `data\processed\llm_cache_qwen2.5_1.5b.json` and `data\processed\llm_cache_qwen2.5_3b.json`, so that the run
   can be replayed exactly.

## If time is short
Run only the more informative temperature:
```
python -m ereplan.realagent v5 --seed-start 4100 --seeds 10 --temps 0.7
```
Tell me if you do this, because it changes what the report covers.

## The demo for your supervisor (1 November)
```
python -m ereplan.novelty_demo
```
It now has **6 acts**. Acts 1–4 are unchanged; acts 5 and 6 are new. You should see 6 lines of `SUPPORTED` and
`identical [OK ...]` on every spot check.

**What to say for act 5 (rule v5, about 60 s):**
- "All three reviewers said my rule needs labelled data to know how good the checker is. My new method fixes that.
  When the checker flags a step, the agent runs the step on a second tool and compares. If they agree, the flag was a
  false alarm, so the agent gets a free label."
- "With no labels at all, v5 is as good as v4 given the labels: 1% better, significant. It is 12% better than v4
  without labels."
- "Repeated false alarms no longer matter, because the agent cross-checks instead of retrying."
- **Honest point:** "The 3% bar I set for beating v4 was not reached, and the advantage disappears if comparisons are
  wrong 10% of the time. So the claim is that it needs no labels, not that it is much better."

**What to say for act 6 (Bayes-optimal, about 40 s):**
- "A reviewer said my reference point was unfair, because it sees the hidden state. So I computed the truly best
  policy, the one that sees only what my rule sees, exactly, on a small version of the problem."
- "Rule v4 is within 2.2% of that best possible policy, and captures 92% of the possible saving. So the simple
  one-step rule is close to optimal."
