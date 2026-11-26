# Pre-registrations

Each file is the plan of one confirmatory experiment: its hypotheses, conditions, seeds, metrics and analysis. Every
file was written and committed **before** its confirmatory run, and the commit history shows when it was added.

The files are kept exactly as they were written, including their dates, because they are the record that each plan
came before its run. Notes added later inside a file (amendments and run records) are marked as such. The commands
in these files give the scripts' location at the time they were written; the experiment scripts are now in
`experiments/` (see [docs/REPRODUCING.md](../docs/REPRODUCING.md)).

## Reported in the paper

| File | Experiment |
|---|---|
| `PREREGISTRATION_persistence.md` | Repeated false alarms of real checkers, and baselines from the literature (part E3: real Qwen2.5 checkers in the GSM8K agent) |
| `PREREGISTRATION_netpv.md` | Corrected check criterion (net protection value) against the earlier criterion |
| `PREREGISTRATION_corrected_suite.md` | Re-run, with the corrected criterion and fresh seeds, of every confirmatory experiment that involves the rule. The designs and hypotheses are those of the original plans listed below |
| `PREREGISTRATION_realtools.md` | Study R (the corrected rule with real checkers in the GSM8K agent) and Study M (cross-check assumptions on real tools) |
| `PREREGISTRATION_assumptions_ext.md` | Study M2 (cross-check assumptions on 300 further GSM8K problems) |
| `PREREGISTRATION_family.md` | Study F (model family or accuracy of the second tool) |
| `PREREGISTRATION_dvsym.md` | Decision-value symmetry |
| `PREREGISTRATION_detect.md` | Detectability and the boundary between monitoring and buying |
| `PREREGISTRATION_D1.md` | Live model-backed tools with natural degradation |
| `PREREGISTRATION_exactline.md` | Exact step cost in the switch line |
| `PREREGISTRATION_d1cal.md` | Live tools, with a labeled calibration as the checker prior |
| `PREREGISTRATION_priorfix.md` | Why the learned false-alarm rate is biased (shrinkage to the prior), and a corrected prior: simulator, live tools and CostBench |
| `PREREGISTRATION_d1power.md` | Live tools on 200 seeds, with the sample size set by a power analysis |
| `PREREGISTRATION_drift.md` | Gradual decline, and a checker whose error rates change during a run |
| `PREREGISTRATION_core2x.md` | The published baselines given the rule's cross-check |
| `PREREGISTRATION_persist_larger.md` | Whether larger local checkers (Llama 3.1 8B, Phi-4 Mini) repeat their false alarms |

Original plans of the experiments re-run by the corrected suite:

| File | Experiment |
|---|---|
| `PREREGISTRATION_v5.md` | Label-free rule, distance to the Bayes-optimal policy (part B) and unreliable comparisons (part C) |
| `PREREGISTRATION_core2.md` | Baselines adapted from published methods |
| `PREREGISTRATION_costbench_v5.md`, `PREREGISTRATION_costbench_v5_part2.md` | CostBench with checks at 15% and 5% of a tool call |
| `PREREGISTRATION_fr11_realcheckers.md` | CostBench with the error rates of real checkers |
| `PREREGISTRATION_robustness.md` | Robustness to broken cross-check assumptions (A1 and A3) |
| `PREREGISTRATION_freshqa.md` | FreshQA with two real judge families |
| `PREREGISTRATION_anytool.md` | Any tool can degrade |
| `PREREGISTRATION_boundary.md` | Monitoring against buying the better tool |
| `PREREGISTRATION_ablation_v51.md` | Ablation of the rule's ingredients |
| `PREREGISTRATION_rho.md` | Learning the share of loud failures (rho) |

## Earlier stages of the project

These tested earlier versions of the rule (v2 to v4). Their results are in `results/` and are superseded by the
experiments above; they are kept for completeness.

| File | Experiment |
|---|---|
| `PREREGISTRATION_confirm_leak.md`, `PREREGISTRATION_confirm_always.md` | Rule v2 against CUSUM and against always checking |
| `PREREGISTRATION_v2.md` | Revised rule v2 |
| `PREREGISTRATION_costbench.md` | First evaluation on CostBench tasks |
| `PREREGISTRATION_selfcal.md` | False reassurance and the self-calibrating rule v3 |
| `PREREGISTRATION_falsealarm.md` | Checker false alarms and rule v4 |
| `PREREGISTRATION_realagent.md` | First test with a real model as the agent |
