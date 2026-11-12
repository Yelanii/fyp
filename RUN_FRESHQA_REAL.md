# How to run: FreshQA with a real judge (Core 1)

**What you are doing.** Your local Qwen model reads 574 real FreshQA questions and judges two answers for each:
- the November 2025 answer (the one a stale tool would give);
- the April 2026 answer.

For each answer it says whether the answer is correct today. When the two answers are worded differently, it also
says whether they mean the same thing.

The verdicts are saved in one small file. That file is all I need back to run the experiments.

## Steps (Windows PowerShell)
1. Start Ollama, and make sure the models are there:
   ```powershell
   ollama pull qwen2.5:1.5b
   ollama pull qwen2.5:3b
   ```
2. Open PowerShell in the **outer** `ereplan` folder, activate the environment, then go into the inner folder:
   ```powershell
   .venv\Scripts\Activate.ps1
   cd ereplan
   ```
3. Unzip `ereplan-update-core.zip` here (overwrite when asked).
4. Quick test without Ollama (a few seconds; all tests should pass):
   ```powershell
   python -m pytest -q
   ```
5. Collect the verdicts. Each model takes about 20–60 minutes on a laptop CPU.
   - If it stops, run the same command again: it continues where it stopped.
   ```powershell
   python -m ereplan.freshqa_real collect --model qwen2.5:1.5b
   python -m ereplan.freshqa_real collect --model qwen2.5:3b
   ```
   At the end it prints the judge's measured rates:
   - catch rate q: how often it says NO to a stale answer;
   - false-alarm rate f: how often it says NO to a correct answer;
   - comparison errors.
6. Send me these two files from `data\processed\`:
   - `freshqa_judge_qwen2.5_1.5b.json`
   - `freshqa_judge_qwen2.5_3b.json`

## Optional
You can run the development experiment yourself; it takes a few minutes:
```powershell
python -m ereplan.freshqa_real run --model qwen2.5:1.5b --seeds dev
```

## What is real here
| Real | Simulated |
|---|---|
| Questions and answers | When tool A stops updating |
| Which answers went stale | Order of questions |
| Every check verdict | Timeouts (5%) |
| Every comparison between two answers | |

The judge runs at temperature 0, so asking again gives the same verdict. Repeated false alarms come from the model
itself; they are not assumed.
