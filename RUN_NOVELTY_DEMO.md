# Novelty demo for Mr. Aponso (deadline 1 November)

**What he asked for:** "a working demo that proves your novelty … the cream of the project should work".

**What this demo does:** it shows each of the four novelty claims, one act each. Each act:
1. **runs the real code in front of him** on a sample of the pre-registered runs, and shows that the result is
   identical to the saved run;
2. **recomputes the full evidence** from all saved raw runs (nothing is typed in by hand);
3. **gives the verdict and the honest limit.**

It opens a results page with charts in your browser.

## Step 1: Add the package (once)
1. Extract `ereplan-update-novelty-demo.zip` into your **inner** project folder (the one with `ereplan`, `tests`
   and `README.md`).
2. Choose **Replace** if asked. It adds:
   - `ereplan/novelty_demo.py`;
   - the saved runs of part E and of the false-alarm map, in `results/`;
   - this file.

## Step 2: Check (1 minute)
In PowerShell, in the inner folder, with `(.venv)` showing:
```
python -m pytest -q
```
You should see **21 passed**.

## Step 3: Run the demo
```
python -m ereplan.novelty_demo
```
- It takes about 1.5–3 minutes and needs no Ollama: the real checker answers come from your saved cache.
- At the end the browser opens `results\novelty_demo_<time>\novelty_demo.html`.

**Options:**
- `python -m ereplan.novelty_demo --quick`: about 20 seconds. Use it if time is short in the meeting.
- `python -m ereplan.novelty_demo --live`: Act 1 also asks the real Qwen checker **right now** through Ollama, on
  three steps it got wrong before. Start Ollama first. This is the most convincing version: he sees the model
  repeat the same wrong answer live.

**Check that you see:**
- every act prints `Live spot check: ... identical [OK ...]`;
- the summary shows **C1–C4 SUPPORTED**.

Expected numbers:
- **C2:** −6.1% at T = 0 and −5.5% at T = 0.7; 16 of 16 conditions.
- **C3:** −13.4%, −16.6% and −16.8%.
- **C4:** peak +23.3% at 80%.

If any line says MISMATCH, stop and send me a screenshot.

## What to say (about 5 minutes; one act per minute)
**Opening (20 s):** "My novelty has four claims. For each one, the demo re-runs my code on runs that were
pre-registered, shows that it reproduces them exactly, and then shows the full evidence."

**Act 1, C1 (60 s):**
- "Real LLM checkers don't make random mistakes. Here the 1.5B checker rejects 180 × 3 = 540 five times out of
  five, saying 5400 each time."
- "After a false alarm, the next check repeats it 76–100% of the time, against 0–2% for a fresh false alarm."
- "So retrying cannot fix it. The closest work, VRR-Stop, assumes the opposite: independent verdicts."

**Act 2, C2 (75 s):**
- "Same agent, same real checkers, same tasks. The only difference is whether it expects false alarms to repeat."
- "Expecting repetition (v4) loses 6.1% less at temperature 0 and 5.5% less at 0.7. Lower in all 16 conditions
  and on every seed. Pre-registered."
- "Why: the independence version checks five times more often and keeps hitting the same false alarm, so it
  fails six times more tasks."
- **Honest point:** "v4 lets a few more wrong answers through. It's a priced trade-off."

**Act 3, C3 (60 s):**
- "Against methods modelled on the three closest works (VRR-Stop, ParetoBandit and Bench2Robust), tuned on
  separate seeds, my rule is 13–17% lower in loss."
- "The chart shows why: when false alarms repeat, always-checking and re-verifying become expensive, while v4
  stays nearly flat."

**Act 4, C4 (45 s):**
- "Checking is not always worth it. It pays most when the tool degrades moderately: up to +23%."
- "For a nearly healthy tool it loses money (−8%), and for a very bad tool switching is better than checking."

**Close (20 s):**
- "Limits: one model family, arithmetic tasks, and simulated prices and degradation."
- "Next: a Llama 3.2 checker and an ablation."

## If he asks
- **"Is this cherry-picked?"** No. The numbers are averages over all pre-registered runs, not one good run. The
  hypotheses and seeds were written down before running, and the failed hypotheses are reported too.
- **"Show me it's real."** Use `--live` (Ollama on), or open `data\processed\llm_cache_qwen2.5_1.5b.json`: these
  are the model's saved answers.
- **"Where is the novelty in one sentence?"** "I measure what checker errors, especially repeated false alarms,
  cost an agent that pays for checks and can switch tools, and I give a rule that avoids that cost. It is shown
  with real checkers and against methods from the closest works."
- **The old demo** (`python -m ereplan.showcase`) still works. It shows one run call by call, which is useful if
  he asks "how does the rule decide?".
