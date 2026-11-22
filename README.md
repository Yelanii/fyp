# When to Pay for a Check

Code, data and pre-registered experiments for the article

> **When to Pay for a Check: Cost-Aware Checking and Switching for LLM Tool-Use Agents Under Silent Tool Degradation**
> Yelani Hanwella, Achala Aponso, Maninda Edirisooriya, Chathuni Gunasena and Lakshika Chandradeva

## Overview

An agent built on a large language model (LLM) pays for the tools it calls. A tool can **degrade silently**: it keeps
answering, but more of its answers are wrong, and no error is raised. The agent can pay a second model to check an
answer, but such checkers miss errors, raise false alarms and often repeat the same false alarm when asked again.
At each call the agent must decide whether to pay for a check, and whether to keep its current tool or switch to
another one.

This repository contains:

- a simulator of priced tools that degrade silently, with checkers that miss errors and repeat false alarms;
- live tool services backed by small local models, which degrade naturally;
- a per-call decision rule that decides when to check, how to resolve a flag and when to switch, together with
  every baseline it is compared with;
- the analysis code (exact losses, identifiability and estimator bias);
- the plan of every experiment, written before it was run, the raw results of every run, and a script that
  replays them.

Everything runs on a CPU. No GPU, no API key and no model training are needed.

## Main findings

- Small LLM checkers re-flagged 82.5 to 92% of their own false alarms, even when sampling. This persistence makes
  check-and-retry more expensive. On live model-backed tools, retrying a flagged answer failed 21% of tasks,
  against 5% when the flag was resolved by cross-checking on a second tool.
- Cross-checking worked when the second model was clearly more accurate; a follow-up pointed to accuracy rather
  than model family.
- Whether monitoring a cheap tool beats buying a reliable one depends on how much each call reveals about a
  degradation. In a pre-registered test, the premium worth paying for the reliable tool rose as this information
  fell.
- The rule stayed within 1.6% of the same rule given the checker's true error rates on three testbeds, including
  under gradual degradation and a changing checker. On live tools it needed a labeled calibration to beat never
  checking, and cross-checking every call was cheaper still.
- Twenty-nine experiments were pre-registered: 67 of 87 hypotheses were confirmed, and every outcome is reported.

## Repository layout

```
ereplan/            Python package: simulator, live tools, the decision rule, baselines and analysis
experiments/        one script per pre-registered experiment
tools/              data-building and analysis scripts
tests/              unit tests
data/               benchmark data and cached model answers
results/            one folder per run, with report.md and the raw rows (see results/README.md)
preregistration/    the plan of every experiment, committed before it was run
docs/               how to reproduce each result
reproduce_paper.py  replays a sample of every reported experiment and compares the numbers
check_local.py      checks the data files, Python packages and Ollama models on this machine
```

The main modules of `ereplan/`:

| Module                                                    | Contents                                                                                                                              |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `crosscheck.py`                                           | The proposed rule (`Rule_v5_x`): learns the checker's catch and false-alarm rates without labels and resolves flags by cross-checking |
| `selfcal.py`, `strategies.py`, `estimator.py`             | The switch line, the check criterion and the windowed estimate of each tool's success rate that the rule builds on                    |
| `env.py`, `runner.py`, `config.py`                        | The simulator: tools, prices, degradation scenarios and checkers                                                                      |
| `tools_live.py`, `agent_live.py`                          | Live tool services backed by local models, and the agent that uses them                                                               |
| `realagent.py`                                            | GSM8K agent in which a local model plans the tool calls and real models check the results                                             |
| `litbaselines.py`, `outside_baselines.py`, `bayes_opt.py` | Baselines adapted from published methods, and a Bayes-optimal comparator                                                              |
| `theory.py`, `theory_check.py`                            | Exact losses of checking under repeated false alarms, checked against the simulator                                                   |

The proposed rule is used with the corrected check criterion (`EREPLAN_NETPV=1`) in every result reported in the
paper. The experiment scripts set this themselves.

## Installation

Python 3.11 or later is required.

```bash
git clone https://github.com/Yelanii/when-to-pay-for-a-check.git
cd when-to-pay-for-a-check
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # macOS or Linux
pip install -r requirements.txt
```

## Quick check

Run these from the repository root:

```bash
python check_local.py          # data files (SHA-256), Python packages and available Ollama models
python -m pytest -q            # unit tests, about 2 minutes
python reproduce_paper.py      # replays every simulated and replayed experiment in the paper, a few minutes
```

`reproduce_paper.py` re-runs a random sample of the saved runs of each experiment and compares every number with the
saved value. It should end with `24 of 24 experiments reproduced exactly.` No model is needed, because every model
answer used by the experiments is cached in `data/processed/`.

To re-run complete experiments, see [docs/REPRODUCING.md](docs/REPRODUCING.md).

## Models

The experiments with real models used [Ollama](https://ollama.com) with these models (4-bit quantized, as
distributed by Ollama): `qwen2.5:1.5b`, `qwen2.5:3b`, `phi4-mini`, `llama3.1:8b` and `llama3.2:3b`. They are needed
only to collect new model answers. All runs were made on a laptop with an Intel Core i7-10510U CPU, 16 GB of RAM
and Windows 11, with Python 3.13 and Ollama 0.40.16, and without a graphics processor.

## Data

| Dataset   | Used for                                                                         | File                                    | Source and license                                                                                                               |
| --------- | -------------------------------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| GSM8K     | Maths word problems for the model-backed tools and checkers                      | `data/raw/gsm8k_test.jsonl`             | Cobbe et al. (2021), [openai/grade-school-math](https://github.com/openai/grade-school-math), MIT (`data/raw/GSM8K_LICENSE.txt`) |
| FreshQA   | Stale knowledge: 574 question pairs from two snapshots, 89 with a changed answer | `data/processed/freshqa_staleness.json` | Vu et al. (2024), snapshots of 24 Nov 2025 and 21 Apr 2026, Apache-2.0                                                           |
| CostBench | Task routes and tool prices; the degradation is added in this work               | `data/processed/costbench_routes.json`  | Liu et al. (2026), built by `tools/costbench_routes.py`                                                                          |

Cached model answers and checker verdicts are in `data/processed/` (`llm_cache_*.json`, `d1_cache_*.json`,
`d1_table.json` and `freshqa_judge_*.json`). `data/MANIFEST.json` records the SHA-256 hash of every data file.

## Pre-registration

Each experiment was planned in a file in [`preregistration/`](preregistration/README.md) and committed before it was
run. Development and tuning used separate seeds, and each confirmatory test was run once. The commit history shows
the order in which plans and results were added.

## Citation

```
Y. Hanwella, A. Aponso, M. Edirisooriya, C. Gunasena and L. Chandradeva, "When to Pay for a Check: Cost-Aware
Checking and Switching for LLM Tool-Use Agents Under Silent Tool Degradation," manuscript, 2026.
```

## Contact

Yelani Hanwella, School of Computing, Informatics Institute of Technology (IIT), Colombo, Sri Lanka
(ymhanwella01@gmail.com). This work was carried out as a final-year project for the BSc (Hons) in Computer Science
at IIT, in affiliation with the University of Westminster.
