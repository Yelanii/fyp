# Part E3 on your laptop: does assuming "false alarms repeat" win with the REAL checkers?

This uses **Ollama** and both models you already have: qwen2.5:1.5b and qwen2.5:3b. It takes about 30–90
minutes. Pre-registration: `PREREGISTRATION_persistence.md`, section "Part E3", written before any test seed
was run.

## Step 1: Add the update (once)
1. Extract `ereplan-update-E3.zip` into your **inner** project folder (the one with `ereplan`, `tests` and
   `README.md`).
2. Choose **Replace**. Your `data/` folder and your old results are not touched. This zip also contains
   everything from the part E zip, so you do not need that one first.

## Step 2: Check the code (1 minute)
In the terminal, in the inner folder, with `(.venv)` showing:

```
python -m pytest -q
```

You should see **21 passed**.

## Step 3: Get the laptop ready
- **Ollama:** make sure it is running (the llama icon near the clock).
- **Models:** in the terminal, type `ollama list`. You should see both `qwen2.5:1.5b` and `qwen2.5:3b`.
- **Power:** plug in the charger and stop the laptop from sleeping, as before.

## Step 4: Run it (one long line)

```
python -m ereplan.realagent persist --model qwen2.5:1.5b --seeds 10 --seed-start 4000
```

You will see 16 progress lines like this:

`qwen2.5:1.5b T=0 drop 0.85 leak 1.0: done (40s)`

The T = 0 lines are quick, because the answers are already saved. The T = 0.7 lines are slower, because the
model is asked new questions.

## Step 5: Send me the result
At the end, a short report is printed and saved to `results/realagent_persist_<time>/report.md`. Send me:
1. that `report.md` (or a screenshot of the printed report);
2. if possible, the two updated answer files, so the run can be replayed:
   - `data/processed/llm_cache_qwen2.5_1.5b.json`
   - `data/processed/llm_cache_qwen2.5_3b.json`

**Do not edit these files.**

## If something goes wrong
- **"no repeat-test file":** the part D files are missing from `results/`. Send me a screenshot of your
  `results` folder.
- **"Ollama did not answer":** check the llama icon. The program waits and retries by itself.
