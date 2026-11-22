# Reproducing the results

Run every command from the repository root, with the packages in `requirements.txt` installed.

Each confirmatory experiment has a plan in `preregistration/`, committed before the run. Each run writes a folder
`results/<experiment>_<mode>_<run id>/` with `report.md` (the tables and every pre-registered hypothesis with its
verdict) and `rows.json` (one row per run). Running an experiment again writes a new folder; the saved folders are
not changed.

Where a command needs an environment variable, set it first:

| Shell | Example |
|---|---|
| Windows PowerShell | `$env:EREPLAN_REPLAY = "1"` and then the command |
| macOS or Linux | `EREPLAN_REPLAY=1 <command>` |

## 1. Check every reported number at once

```
python reproduce_paper.py
```

For each of the 24 experiments that run on the simulator, on CostBench or on cached live-tool answers, this re-runs a
random sample of the saved runs with that experiment's own settings and compares loss, wrong answers kept, failed
tasks and checks per task with the saved values. Every line should say `IDENTICAL`, and the last line should be
`24 of 24 experiments reproduced exactly.` It needs no model and takes a few minutes.

- `python reproduce_paper.py --n 40` checks a larger sample.
- `python reproduce_paper.py --only d1 fr11` checks only some experiments; the keys are listed in the script.

The sections below re-run whole experiments from the start.

## 2. Simulator, CostBench and cached live-tool answers (no model needed)

| Experiment in the paper | Pre-registration | Seeds | Command | Saved results |
|---|---|---|---|---|
| Corrected against earlier criterion | `netpv` | 8100-8119 | `python experiments/run_netpv.py confirm` | `netpv_confirm_20261116-231543` |
| Label-free rule | `corrected_suite` (design of `v5`) | 8200-8219 | `python experiments/run_corrected_suite.py one sim` | `v5_confirm_20261117-141451_netpv` |
| Unreliable comparisons (A3) | `corrected_suite` (`v5`, part C) | 8220-8229 | `python experiments/run_corrected_suite.py one stress` | `v5_stress_20261117-142756_netpv` |
| Distance to Bayes-optimal | `corrected_suite` (`v5`, part B) | 8240-8259 | `python experiments/run_corrected_suite.py one bayes` | `bayes_confirm_20261117-154016_netpv` |
| Published methods | `corrected_suite` (`core2`) | 8300-8319 | `python experiments/run_corrected_suite.py one core2` | `core2_confirm_20261117-173234_netpv` |
| CostBench, check at 15% | `corrected_suite` (`costbench_v5`) | 8340-8357 | `python experiments/run_corrected_suite.py one cb15` | `costbench_v5_confirm_20261117-181237_netpv` |
| CostBench, check at 5% | `corrected_suite` (`costbench_v5_part2`) | 8360-8377 | `python experiments/run_corrected_suite.py one cb5` | `costbench_v5_cheap_20261117-182202_netpv` |
| CostBench, real-checker rates | `corrected_suite` (`fr11_realcheckers`) | 8400-8417 | `python experiments/run_corrected_suite.py one fr11` | `fr11_confirm_20261117-183020_netpv` |
| Robustness to A1 and A3 | `corrected_suite` (`robustness`) | 8500-8519 | `python experiments/run_corrected_suite.py one robust` | `robustness_confirm_20261117-212216_netpv` |
| FreshQA, two judge families | `corrected_suite` (`freshqa`) | 8600-8619 | `python experiments/run_corrected_suite.py one freshqa` | `freshqa_confirm_20261117-222920_netpv` |
| Any tool can degrade | `corrected_suite` (`anytool`) | 8700-8719 | `python experiments/run_corrected_suite.py one anytool` | `anytool_confirm_20261117-225549_netpv` |
| Monitoring vs. buying | `corrected_suite` (`boundary`) | 8800-8819 | `python experiments/run_corrected_suite.py one boundary` | `boundary_confirm_20261117-230438_netpv` |
| Ablation | `corrected_suite` (`ablation_v51`) | 8900-8919 | `python experiments/run_corrected_suite.py one ablation` | `ablation_confirm_20261118-014709_netpv` |
| Learning rho | `corrected_suite` (`rho`) | 9000-9019 | `python experiments/run_corrected_suite.py one rho` | `rho_confirm_20261118-085301_netpv` |
| Decision-value symmetry | `dvsym` | 9100-9119 | `python experiments/run_dvsym.py confirm` | `dvsym_confirm_20261119-231137` |
| Detectability and the boundary | `detect` | 9200-9219 | `python experiments/run_detect.py confirm` | `detect_confirm_20261120-230307` |
| Live tools, natural degradation | `D1` | 7100-7119 | `python -m ereplan.agent_live run confirm` | `d1_confirm_20261121-021314` |
| Live tools, calibrated prior | `d1cal` | 7200-7219 | `python experiments/run_d1cal.py confirm` | `d1cal_confirm_20261121-103616` |
| Exact step cost | `exactline` | 9300-9319 | `python experiments/run_exactline.py confirm` | `exactline_confirm_20261121-120338` |
| Prior fix, simulator | `priorfix` | 9400-9419 | `python experiments/run_priorfix.py sim confirm` | `priorfix_sim_confirm_20261121-171041` |
| Prior fix, live tools | `priorfix` | 7300-7319 | `python experiments/run_priorfix.py live confirm` | `priorfix_live_confirm_20261121-151854` |
| Prior fix, CostBench | `priorfix` | 9500-9517 | `python experiments/run_priorfix_cb.py confirm` | `priorfix_cb_confirm_20261121-153037` |
| Live tools, 200 seeds | `d1power` | 7400-7599 | `python experiments/run_d1power.py confirm` | `d1power_confirm_20261121-175005` |
| Gradual decline, changing checker | `drift` | 9600-9619 | `python experiments/run_drift.py confirm` | `drift_confirm_20261121-195725` |

Pre-registration `x` is the file `preregistration/PREREGISTRATION_x.md`, and every saved results folder is in
`results/`.

The experiments run by `run_corrected_suite.py` re-use the designs, hypotheses and analysis code of the earlier
experiments with the corrected check criterion and fresh seeds. `python experiments/run_corrected_suite.py list`
shows them with rough run times, and `all` runs them one after another. Each writes
`results/<name>_confirm_<run id>_netpv/`, and the hypothesis lines of all reports are collected in a file
`results/corrected_suite_summary_<run id>.md`.

The live-tool experiments replay the model answers saved in `data/processed/d1_table.json`. To collect the answers
again with Ollama, run `python -m ereplan.agent_live prepare` first; answers already in the cache are not requested
again.

## 3. Experiments with real models (Ollama)

These call local models through Ollama (see `README.md`). Every answer is saved in `data/processed/` the first time
it is produced, so a second run reads the saved answers instead of calling the model.

| Experiment in the paper | Pre-registration | Seeds or items | Command | Saved results |
|---|---|---|---|---|
| Repeated verdicts with real checkers | `persistence` (part E3) | 4000-4009 | `python -m ereplan.realagent persist --model qwen2.5:1.5b --seeds 10 --seed-start 4000` | `realagent_persist_20261025-004642` |
| Label-free rule with real checkers (Study R) | `realtools` | 4300-4309 | with `EREPLAN_NETPV=1`: `python -m ereplan.realagent v5 --seed-start 4300 --seeds 10 --setup-from results/realagent_persist_20261025-004642/rows.json` | `realagent_v5_20261119-175229` |
| A1-A3 on real tools (Study M) | `realtools` | GSM8K problems 1-200; 574 FreshQA pairs | `python experiments/measure_assumptions.py confirm` | `assumptions_confirm_20261118-131727` |
| A1 and A2 on new problems (Study M2) | `assumptions_ext` | GSM8K problems 201-500 | `python experiments/measure_assumptions_ext.py confirm` | `assumptions_ext_confirm_20261119-234258` |
| Model family or accuracy (Study F) | `family` | GSM8K problems 201-500 | `python experiments/measure_family.py confirm` | `family_confirm_20261121-223532` |

The two GSM8K agent experiments (`ereplan.realagent`) can be replayed from the saved answers without Ollama by setting
`EREPLAN_REPLAY=1`.

## 4. Analysis scripts

| Result in the paper | Command |
|---|---|
| Exact losses of checking against the simulator | `python -m ereplan.theory_check` |
| Identifiability of the checker's error rates (Proposition S1) | `python tools/check_identifiability.py` |
| Bias of the label-free estimates under shared mistakes (Proposition S2) | `python tools/sigma_bias.py` |

## 5. Development seeds

Development and tuning used separate seeds (for example 8000-8003, 4960-4961 and 7010-7014), listed in each
pre-registration. They were never used in a confirmatory test.

## 6. Environment

The reported runs were made on a laptop with an Intel Core i7-10510U CPU, 16 GB of RAM and Windows 11, with Python
3.13, Ollama 0.40.16 and no graphics processor. `python check_local.py` prints the versions on your machine. The
FreshQA judge verdicts were collected before the Ollama version was recorded; a later live re-check reproduced 78 of
80 verdicts, and the analysis uses the saved verdicts.
