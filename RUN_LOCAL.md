# Run and check the implementation on your own laptop

Everything here runs on a CPU. Commands are for Windows PowerShell; on macOS or Linux use `source .venv/bin/activate`.

## 0. Do I need to download any dataset? No.
All data the experiments read is inside `data/`, and `check_local.py` verifies each file by its SHA-256 hash.

| Dataset | File in this folder | Source and licence |
|---|---|---|
| GSM8K (arithmetic tasks, real-agent runs) | `data/raw/gsm8k_test.jsonl` | github.com/openai/grade-school-math, commit 3101c7d, MIT |
| CostBench (tasks and tool prices) | `data/processed/costbench_routes.json` | built from CostBench commit 6424069 by `tools/costbench_routes.py` |
| FreshQA (questions whose answers went stale) | `data/processed/freshqa_staleness.json` | FreshQA snapshots of 24 Nov 2025 and 21 Apr 2026, Apache-2.0 |
| Your judges' verdicts on FreshQA | `data/processed/freshqa_judge_*.json` | collected on your laptop, 31 Oct to 1 Nov |
| Your Qwen answers (real-agent runs) | `data/processed/llm_cache_qwen2.5_*.json` | collected on your laptop |

You only need the original CostBench or FreshQA downloads if you want to rebuild these files from scratch.

## 1. Set up (once, about 5 minutes)
```powershell
cd ereplan
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install numpy scipy matplotlib pytest
```

## 2. Check the machine (1 minute)
```powershell
python check_local.py
```
It checks the data files, the Python packages, and which of your four Ollama models are pulled
(`qwen2.5:1.5b`, `qwen2.5:3b`, `phi4-mini`, `llama3.1:8b`).

## 3. Run the tests (1 to 2 minutes)
```powershell
python -m pytest -q
```
Expected: `76 passed`.

## 4. Confirm your laptop reproduces the reported results (3 to 5 minutes)
```powershell
python verify_results.py
```
It re-runs a random sample of the saved confirmatory runs and compares every number exactly. Expected: six lines
saying `IDENTICAL`. Use `--n 60` for a larger sample.

## 5. Check with your own models (Ollama; 5 to 15 minutes)
```powershell
ollama serve            # if it is not already running
python check_local.py --live 20
```
Phi-4 Mini and Llama 3.1 8B re-judge 20 FreshQA questions each, and the script compares their answers with the saved
verdicts the experiments used. If a few differ, your Ollama or model version has changed since 1 Nov: write down
the count and the Ollama version (`ollama --version`); it is a reproducibility note, not a failure of the code.

## 6. Optional: re-run a whole experiment (slow; leave the laptop plugged in)
Each command writes a new folder in `results/` with `report.md`. The numbers should equal the saved report.

| Experiment | Command | Time on 2 cores (faster with more) |
|---|---|---|
| FR11 CostBench, real-checker rates | `python run_fr11.py confirm` | 15 min |
| FR16/17 FreshQA, two real judges | `python run_freshqa_confirm.py confirm` | 20 min |
| FR18 any tool can degrade | `python run_anytool.py confirm` | 7 min |
| Boundary map | `python run_boundary.py confirm` | 9 min |
| FR13 sensitivity | `python fr13_sensitivity.py` | 20 min |
| FR21 ablation | `python run_ablation.py confirm` | 45 min |
| FR20 learning rho | `python run_rho.py confirm` | 1 h 45 min |

## 7. Optional: collect the judges' verdicts again from scratch (about 1 hour per model)
Only if you want fully fresh verdicts. Move the saved file away first, otherwise the command sees it is complete and
does nothing.
```powershell
Move-Item data\processed\freshqa_judge_phi4-mini_plain.json data\processed\freshqa_judge_phi4-mini_plain.saved.json
python -m ereplan.freshqa_real collect --model phi4-mini@plain
python -m ereplan.freshqa_real measure --model phi4-mini@plain
```

## What is not yet run with a live model
FR11 uses the error RATES of your four real checkers, measured on arithmetic and FreshQA. No model has judged
CostBench outputs directly. That would be new work, not a re-run.
