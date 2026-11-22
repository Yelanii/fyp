# Pre-registration: rules v4 and v5 on CostBench tasks (28 October 2026, before running seeds 2000-2017)

**Why.** The CostBench evaluation of 21 October (PREREGISTRATION_costbench.md, H-cb confirmed) tested rule v2
with a checker that never flags a correct result. Rules v4 and v5 were later built for checkers with false alarms,
and have only been tested on synthetic tools (v5_exp) and GSM8K (real checkers). This test runs them on CostBench.

**Order of work (stated honestly).** The code and the hypotheses in `ereplan/costbench_v5.py` were written first.
Then one condition on development seed 1990 was run to time the code, and a development smoke run on seeds
1990-1991 (128 conditions) was run to catch crashes. No parameter, hypothesis or threshold was changed after
either run. The development result is kept in `results/costbench_v5_dev_20261028-161831/`. It suggested that
H-CB1 may fail; the hypothesis is kept unchanged.

## Environment
- Tasks and prices: real CostBench test queries, commit 6424069, refinement level 2
  (`data/processed/costbench_routes.json`, 194 queries). Each task: the cheapest route (uses tool X) and the
  cheapest route avoiding X. 120 tasks per run, sampled from one task type; the type rotates with the seed.
- X's success rate drops silently from 95% to {95% (no drop), 85%, 75%, 60%} at a random task in [30, 70).
  Other tools stay at 95%. Loud share rho = 0.5. Up to 2 retries.
- Checker: catch rate q in {0.8, 0.95}; false-alarm rate f in {0.05, 0.15}; persistence pi in {0, 1}
  (pi = 1: a retry gets the same verdict, as with a deterministic LLM judge). Check price 15% of the mean tool price.
- Wrong-answer (leak) loss = {1, 3} x mean route cost. Price gap: native CostBench prices, or X made 20% cheaper.
- Grid: 4 x 2 x 2 x 2 x 2 x 2 = 128 conditions per seed.
- Cross-check (v5 and always_x): a flagged step on X is re-done by CostBench's own route around X, priced at
  c_X + (route cost without X - route cost with X). A flagged step on another tool is re-done by a second provider
  at the same price (assumption: CostBench lists no duplicate providers). The alternative succeeds 95% of the
  time; its failures are loud with share rho, otherwise silently wrong. Two wrong outputs never agree.

## Strategies (all parameters frozen from earlier studies; nothing tuned)
never, always, CUSUM, rule v2 (21 Oct CostBench version), rule v4 (told q and f), v4_nocal (told nothing:
f = 0, q prior 0.5), always_x (check everything, cross-check every flag), v5_told (cross-check, told q and f),
v5 (cross-check, learns q and f without labels). v4/v5: window 60, audit 2%, k 3, horizon 10 tasks.

## Metric and analysis
Total loss per task = spend + leak loss x wrong answers kept + route cost x failed tasks. Unit of analysis: the
seed (mean over the 128 conditions). Seeds 2000-2017 (18 seeds, 3 per task type). One-sided Wilcoxon signed-rank
tests; Holm correction over H-CB1 to H-CB4 at alpha 0.05; 95% paired bootstrap CIs.

## Hypotheses
- **H-CB1** v5 has lower total loss than v4_nocal (both without labelled calibration).
- **H-CB2** v5 has lower total loss than always_x (cross-checking every flag).
- **H-CB3** v5 has lower total loss than v4 told q and f.
- **H-CB4** v4 has lower total loss than v2 (false-alarm awareness pays on CostBench).
- **H-CB5** v5 is within 3% of v5_told (upper end of the 95% CI of the difference <= +3%).

Reported regardless of outcome: every hypothesis, wrong-answer and failed-task rates, checks and cross-checks
per task, results on native prices only, and v5's learned f and q.

## Outcome (added after the run, 28 October 2026; results/costbench_v5_confirm_20261028-162916)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-CB1 v5 < v4_nocal | 111.0 vs 110.3 (+0.6%, CI -0.1% to +1.3%), p = 0.96 | NOT CONFIRMED |
| H-CB2 v5 < always_x | 111.0 vs 124.7 (-11.0%, CI -12.0% to -10.0%), p = 3.8e-06 | CONFIRMED |
| H-CB3 v5 < v4 told | 111.0 vs 110.9 (+0.0%, CI -0.3% to +0.3%), p = 0.75 | NOT CONFIRMED |
| H-CB4 v4 < v2 | 110.9 vs 120.6 (-8.0%, CI -8.9% to -7.1%), p = 3.8e-06 | CONFIRMED |
| H-CB5 v5 within 3% of v5_told | +0.9%, CI upper +1.3% | CONFIRMED |

Interpretation (not part of the plan): on CostBench prices the route around X costs only about 0.1% more, so the
cheapest response to doubt is to avoid X, and checks rarely pay (v4 and v5 check 0.1-0.35 times per task). When
checks are rare, knowing or learning the checker matters little, so v5's label-free learning gives no advantage
over v4 without labels here, unlike the synthetic study (H-V2, -11.8%). What carries over: false-alarm-aware
checking beats the false-alarm-unaware rule v2 (-8.0%), and selective checking beats cross-checking everything
(-11.0%). Never-checking (113.1) is close: CostBench's cheap alternative leaves little for any checking rule to save.
