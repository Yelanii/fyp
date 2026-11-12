# Pre-registration, Core 2: rules v4 and v5 against three recent outside methods (31 October 2026)

Written before the tuning run finished and before any test seed (2410–2429) was run.
Code: `ereplan/outside_baselines.py`, `ereplan/core2_exp.py`. The runner has one new branch, used only by B13, so
all earlier results are unchanged (38 earlier tests pass).

## Why
Reviewers asked for comparisons with methods from outside this project's own baselines. The proposal (FR12, Core 2)
names three recent ones:

| Baseline | Source | What it represents |
|---|---|---|
| B13_ssv | Kiyani et al. (2026), ICML, Algorithm 1 | Online weak/strong verification with error control |
| B14_rdecusum | Hou, Bidkhori and Banerjee (2024), arXiv:2412.20207 | Robust change detection that limits paid observations |
| B15_glrklucb | Besson et al. (2022), JMLR 23(77) | Bandit for tools whose quality changes |

Each adaptation is described at the top of `outside_baselines.py`.

## Fairness rules (set before the run)
- **Baselines are tuned; our rules are not.**
  - Each outside baseline gets a parameter grid on development seeds 2400–2403, over all 64 conditions:
    - B13: 48 settings of α, β and the exploration rate;
    - B14: 120 settings of A, μ, h and p1;
    - B15: 12 settings of α0 and the check rate.
  - The setting with the lowest mean loss is frozen in `data/processed/core2_tuned.json`.
  - Rules v4 and v5 keep the parameters frozen since 27–28 October.
- **Baselines are told the checker.** They are told the true q and f (labelled calibration). Rule v5 is told
  nothing.
- **Same environment.** Same random outcomes for every strategy (common random numbers).

**Addition after tuning round 1 (before any test seed).** Several round-1 choices sat at the edge of their grid:
- B14: the smallest μ and the smallest A;
- B15: the smallest α0 and the largest check rate;
- B13: the smallest exploration rate.

A second round extends each grid past those edges (60 more settings, same development seeds). The final choice is
the better of the round-1 choice and the best round-2 setting. Reference losses on the development seeds, seen
before this addition:

| Strategy | Mean loss |
|---|---|
| never | 165.7 |
| v4 | 146.9 |
| v5 | 146.5 |
| best B13 | 175.8 |
| best B14 | 158.2 |
| best B15 | 181.8 |

The hypotheses are unchanged.

## Environment
The synthetic grid of PREREGISTRATION_v5.md, 64 conditions per seed:

| Factor | Levels |
|---|---|
| Drop | 95%, 85%, 75%, 60% |
| Catch rate q | 0.8, 0.95 |
| Leak weight | 1, 3 |
| False-alarm rate f | 0.05, 0.15 |
| Persistence π | 0, 1 |

- Check price: 15%.
- Test seeds: 2410–2429 (20, never used).
- Unit of analysis: the seed.

## Hypotheses
Total loss per task, one-sided Wilcoxon signed-rank tests over the 20 seeds, Holm correction within each family
at α = 0.05, 95% paired bootstrap CIs.

**Family 1 (primary):**
- **H-O1:** v5 has lower total loss than B13_ssv.
- **H-O2:** v5 has lower total loss than B14_rdecusum.
- **H-O3:** v5 has lower total loss than B15_glrklucb.

**Family 2 (secondary):**
- **H-O4.1–4.3:** rule v4 (told q and f) has lower total loss than each of B13, B14 and B15.

Reported regardless of outcome:
- spend, leak rate, failed tasks, checks, cross-checks and switches;
- losses split by π, f, leak weight and drop;
- the full tuning table, including the worst setting.

## What the outcomes would mean
| Outcome | Meaning |
|---|---|
| Family 1 confirmed | With no labels, v5 beats tuned recent methods that are given labels, in this simulator. |
| A hypothesis not confirmed | That method is competitive here. The split by π and f shows where, and the paper says so. |
| B13 close to v5 | Cross-checking (a strong verifier) is the main ingredient, and online error control is a real alternative to cost-based checking. |

## Limits stated in advance
- The adaptations are ours. B13's strong verifier is a cross-check that can itself be wrong, unlike the paper's
  reference g.
- B14 ignores skipped calls, as in the paper.
- B15 counts flags as failures, as B10 does.
- Simulator only. CostBench and FreshQA versions come after this test.

**Frozen choice after round 2** (`data/processed/core2_tuned.json`, results/core2_tune2_20261031-203347):

| Baseline | Frozen setting | Dev loss |
|---|---|---|
| B13 | α 0.2, β 0.1, exploration 0.005, η 0.05 | 173.9 |
| B14 | A 2, μ 0.01, h 1, p1 0.75 | 154.5 |
| B15 | α0 0.03, check rate 1.0 (the largest possible) | 176.8 |

Every choice is now inside its grid, except B15's check rate, which is at the natural limit. The confirmatory run
starts now.

## Outcome (31 October 2026, 21:32; results/core2_confirm_20261031-213208; 12,800 runs, 3,358 s)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-O1 v5 < B13 SSV | 145.5 vs 174.2 (−16.4%, CI −17.3% to −15.5%), p = 9.5e-07 | CONFIRMED |
| H-O2 v5 < B14 RDE-CUSUM | 145.5 vs 157.2 (−7.4%, CI −8.1% to −6.7%), p = 9.5e-07 | CONFIRMED |
| H-O3 v5 < B15 GLR-klUCB | 145.5 vs 175.0 (−16.8%, CI −17.4% to −16.2%), p = 9.5e-07 | CONFIRMED |
| H-O4.1–4.3 v4 < each | −15.9%, −6.8%, −16.3%; all p = 9.5e-07 | CONFIRMED |

p = 9.5e-07 is the smallest value a one-sided Wilcoxon test can give with 20 seeds: v5 was lower on every seed.

Interpretation (not part of the plan):
- **Repeated false alarms drive most of the gap, as the theory predicts.**
  - SSV and GLR-klUCB fail 17–22% of tasks.
  - Their loss jumps from π = 0 to π = 1: 160 → 188 for SSV, 162 → 188 for GLR-klUCB.
  - v5 is flat across π: 145.5 vs 145.5 (Proposition 2 in data).
- **v5 still wins when π = 0**: 145.5 vs 153.6 for the closest baseline, RDE-CUSUM.
- **v5, told nothing, matches v4, which is given labels**: 145.5 vs 146.5.
- **The closest outside method is the robust change detector** (−7.4%), which limits paid checks like our rules do.
