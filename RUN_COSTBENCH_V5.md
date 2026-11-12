# Rules v4 and v5 on CostBench (28 October 2026)

Plan written first: `PREREGISTRATION_costbench_v5.md`.

```powershell
# Windows, from the outer folder
.venv\Scripts\Activate.ps1
cd ereplan
python -m pytest -q                         # 30 tests
python -m ereplan.costbench_v5 dev          # 1-2 minutes: smoke test, seeds 1990-1991 (not a test)
python -m ereplan.costbench_v5 confirm      # 10-20 minutes: the pre-registered test, seeds 2000-2017
```
Needs `data/processed/costbench_routes.json` (already in the folder). To rebuild it from CostBench itself:
`python -I tools/costbench_routes.py <path to your CostBench clone>`. Do not publish that json file or any CostBench
file in a public repo (the CostBench repo has no licence file): publish the script, and record the commit.

The result is in `results/costbench_v5_confirm_<date>/report.md`. On the same seeds it gives the same numbers as
the run in the container.

## Feasibility: the alternative can degrade too (exploratory, 28 Oct 2026)
```powershell
python -m ereplan.alt_feasibility      # about 2-4 minutes; seeds 2100-2109
```
Adds five scenarios (S1 only A, S2 B fails after the switch, S3 independent, S4 shared cause, S5 A recovers) to
`ereplan/env.py` without changing any earlier scenario. Exploratory: no hypotheses, not a confirmatory test.

## Part 2: cheap checks (pre-registered, 28 Oct 2026)
```powershell
python -m ereplan.costbench_v5 cheap   # about 25-40 minutes; seeds 2200-2217; plan: PREREGISTRATION_costbench_v5_part2.md
python -m ereplan.novelty_demo         # now 10 claims (C10 = part 2)
```

## FreshQA feasibility (exploratory, 31 Oct 2026)
```powershell
python -I tools/freshqa_compare.py <FreshQA Nov 2025 csv> <FreshQA Apr 2026 csv> data/processed/freshqa_staleness.json
python -m ereplan.freshqa_feasibility     # under 1 minute; seeds 2300-2309
```
