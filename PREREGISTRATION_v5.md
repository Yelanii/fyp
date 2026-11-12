# Pre-registration: rule v5 pilot (label-free checker learning and cross-checking)

**Written:** 27 October 2026, 01:40 (Asia/Colombo), **before** any development or test run of rule v5 across conditions.
Two single-run smoke tests on development seed 1600 were run while writing the code (to find bugs). One bug was found
and fixed: outcomes 'ok' and 'leak' were treated as flags.

## Why
Two external reviews (27 Oct 2026) agreed that:
- rule v4 must be **told** the checker's catch rate q and false-alarm rate f, from labelled calibration tasks;
- its cost of false alarms partly comes from the **retry policy**: a flagged step is retried on the same tool, so a
  checker that repeats its false alarms fails correct work.

Rule v5 tests a method that addresses both.

## The method (rule v5, `ereplan/crosscheck.py`)
1. **Cross-check instead of retry.** When a check flags a step, the agent runs the same step on the best alternative
   tool and compares the two outputs:
   - agree: the flag was a false alarm, so the original output is kept;
   - disagree: the alternative's output is used;
   - alternative fails loudly: retry as before.

   Wrong outputs of two different tools are assumed never to coincide (numeric answers).
2. **Learn the checker without labels.** Agreement after a flag acts as a free label. A posterior over (q, f) is
   updated from every checked call, and each tool's success-rate estimate uses it. v5 starts from vague priors
   (q: mean 0.5, strength 2; f: mean 0.1, strength 2, on [0, 0.5]) and is told **nothing** about q or f.
3. **Decide** as rule v4 (switch if the whole range is below the switch line; else check if
   PV + DV − FA ≥ check price). FA is now the expected cost of a false alarm under cross-checking:
   one call on the alternative, plus a leak if the alternative is silently wrong, plus a retry if it fails loudly.

**Approximations (stated in advance):**
- plug-in estimates of the tool's and the alternative's success rate when updating (q, f);
- the (q, f) posterior is also used as the prior of each windowed estimate, so recent checked calls count twice for q.

## Design
- **Simulator:** unchanged except for a new runner branch that only strategies with `crosscheck = True` reach. A
  regression check reproduced 12 of 12 sampled part E runs exactly.
- **Conditions (64):**
  - drop ∈ {95, 85, 75, 60}%;
  - q ∈ {0.8, 0.95};
  - wrong-answer cost ∈ {1, 3} tasks;
  - f ∈ {0.05, 0.15};
  - persistence π ∈ {0, 1}.

  Check price 15% of the mean tool price.
- **Seeds:** development 1600–1605 (smoke test only: nothing is tuned; a change after the smoke test is allowed only to
  fix a bug, and would be reported). Test: **1700–1719**, run once.
- **Strategies:**

  | Key | What it is | Told q and f? |
  |---|---|---|
  | never, always, cusum | simple baselines | yes (as before) |
  | v4 | pre-registered rule v4; retries a flagged step | yes (labelled calibration) |
  | v4_nocal | rule v4 without calibration | no: assumes f = 0, q prior mean 0.5 |
  | v4_miscal | rule v4 told wrong values | wrong: q − 0.15, f / 2 |
  | always_x | check every call; cross-check every flag (reviewers' cross-check baseline) | yes |
  | v5_told | ablation: rule v5's policy, told q and f | yes |
  | **v5** | **rule v5: cross-check, learns q and f** | **no** |

- **Metric:** total loss per task (spend + wrong-answer cost × leaks + one task's cost × failed tasks). Leak rate,
  failed tasks, spend, checks and cross-checks are also reported separately, by wrong-answer cost and by π.
- **Unit of analysis:** the **seed** (mean over the 64 conditions), as the reviewers asked; n = 20. Paired one-sided
  Wilcoxon signed-rank tests; 95% bootstrap confidence intervals of the percentage difference.

## Hypotheses
**Primary** (Holm correction over the three):
- **H-V1:** v5 (no labels) has lower total loss than v4 (told q and f), by at least 3%.
- **H-V2:** v5 has lower total loss than v4 without calibration (v4_nocal), by at least 5%.
- **H-V3:** v5 has lower total loss than the cross-check baseline always_x (any size).

**Secondary:**
- **H-V4:** learning costs little. v5 is within 3% of v5_told (upper 95% bootstrap bound ≤ +3%).
- **H-V5:** persistence barely matters for v5. |loss(π = 1) − loss(π = 0)| ≤ 2% of v5's loss, and the difference is
  smaller than v4's (p < 0.05).
- **H-V6:** v5 learns f. Median |f̂ − f| at the end of a run ≤ 0.03. q̂ error is reported without a pass mark.
- **H-V7:** v5 has lower total loss than v4 told wrong values (v4_miscal), p < 0.05.

## How results will be read
- **H-V1 and H-V2 confirmed:** v5 removes the need for labelled calibration without losing performance.
- **H-V3 not confirmed:** the cross-check policy alone (always_x) explains the gain, and checking selectively adds
  nothing. This would be reported as such.
- **H-V4 not confirmed:** learning without labels costs more than 3%. The contribution then shrinks to the
  cross-check policy.
- **v5 not better than v4:** reported as a negative result; rule v4 stays the main method.

All outcomes are reported, including failures.

## Real-checker pilot (after the simulation test)
- **Setup:** the same comparison (v5 vs v4) with the real Qwen2.5 1.5B and 3B recompute checkers, at temperature 0
  and 0.7, on GSM8K steps. Tool faults are simulated as before. Seeds **4100–4109**; drop ∈ {85, 75}%; wrong-answer
  cost ∈ {1, 3}. v4 is told the calibrated q and f. v5 is told nothing.
- **R-V1:** v5's total loss is lower than v4's, paired over 80 pairs and over the 10 seeds; Wilcoxon p < 0.05.
- **R-V2:** v5's learned f̂ is within 0.05 of the calibrated f, median over runs.
- **Method:** run on the laptop with Ollama. A replay from the saved answers may be run first as a preview. Any answer
  missing from the cache is counted and reported. Results with missing answers are a preview only, not the test.

---

## Part B: distance to the Bayes-optimal policy (added 27 Oct 2026, 02:05, before any Part B test run)
Requested by external review 3 ("the perfect-knowledge optimum knows the hidden state, so it is the wrong reference").

**Instance (small enough to solve exactly):**
- two tools: A, price 20, drops silently from 0.95 to p1 at a time uniform on 150–349; B, price 24, stable at 0.95;
- single-step tasks, 600 per run, no retries;
- 48 conditions:
  - p1 ∈ {95, 85, 75, 60}%;
  - q ∈ {0.8, 0.95};
  - wrong-answer cost ∈ {5, 15} tasks (≈ 110 and 330, similar in money to the main experiments);
  - f ∈ {0, 0.05, 0.15}.

**Bayes-optimal policy (`ereplan/bayes_opt.py`):**
- It is solved by dynamic programming over the agent's belief that A has degraded, on a 1,001-point grid.
- Its actions are call, call and check, and switch.
- It is told the model (p0, p1, the change-time distribution, q, f, ρ, prices).

Sanity check before this addendum: a run on seeds 1800–1805 showed that the programme's predicted loss matched the
simulated loss within 0.3. Because those seeds have been seen, the test uses fresh seeds **1820–1839**.

**Strategies:**
- same actions as Bayes: never, always, cusum, v4 (told q and f);
- also run: B6, which sees the true state but uses a simple check rule;
- v5 is reported separately, because it has an extra action (cross-check).

**Hypotheses (unit: seed, n = 20):**
- **H-B1 (sanity):** Bayes has the lowest mean loss among never, always, cusum and v4. If not, there is a bug.
- **H-B2:** v4's mean loss is within 5% of Bayes-optimal (the 95% bootstrap CI is reported).
- **H-B3:** v4 captures at least 80% of the achievable saving over never-check: (never − v4) / (never − Bayes).
- **Descriptive:** regret by drop level and f, i.e. where the one-step rule falls short.

## Real-checker pilot: addition after the replay preview (27 Oct 2026, 02:05)
A replay preview on the already-used part E3 seeds 4000–4009, with saved answers (~950 missing answers counted as no
alarm), gave:
- v5 75.5 vs v4 76.0 (−0.6%; per seed 6 of 10 lower, p = 0.22), so R-V1 was not met in the preview;
- learned f within 0.05 of the calibrated f (median error 0.041).

R-V1 and R-V2 stay as written for the laptop run on fresh seeds 4100–4109. One check is **added, and declared as added
after seeing the preview**:
- **R-V3 (non-inferiority):** v5, told nothing, is no more than 3% worse than v4, told the labelled calibration
  (mean over all 160 pairs).

---

## Part C: cross-checks that are sometimes wrong (added 27 Oct 2026, 02:15, before any Part C run)
Requested by external review 3: on calculator steps, two different tools almost never agree on a wrong number, so
cross-checking is close to perfect. In tasks with text answers, comparing two outputs is itself error-prone.

- **Stress parameter:** e = the chance that the comparison reports the wrong result (agree ↔ disagree); e ∈ {0, 0.1, 0.2}.
- **Conditions:** q 0.95, π 1, drop {85, 75}%, wrong-answer cost {1, 3}, f {0.05, 0.15}.
- **Seeds:** 1720–1729.
- **Strategies:** v4 (does not cross-check, so it does not depend on e), always_x and v5.
- **H-C1:** at e = 0.1, v5's total loss is still below v4's (one-sided Wilcoxon over the 10 seeds, p < 0.05).
- **Descriptive:** the size of v5's advantage at each e, and v5's learned f (which a wrong comparison biases).

---

## Outcomes (recorded 27 Oct 2026, 03:10; all reported, including failures)

### Simulation test (seeds 1700–1719; 11,520 runs; `results/v5_confirm_20261027-024238`)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-V1 v5 < v4 (told labels) by ≥ 3% | 145.5 vs 147.1 (−1.0%, 95% CI −1.4% to −0.6%), p = 0.00035 | **NOT CONFIRMED** (significant, but below the 3% bar) |
| H-V2 v5 < v4 without calibration by ≥ 5% | 145.5 vs 165.1 (−11.8%) | CONFIRMED |
| H-V3 v5 < always_x (cross-check baseline) | 145.5 vs 156.8 (−7.2%) | CONFIRMED |
| H-V4 v5 within 3% of v5_told | −0.4% (CI upper +0.3%) | CONFIRMED |
| H-V5 persistence barely matters for v5 | +0.00 (v4: +3.23) | CONFIRMED |
| H-V6 v5 learns f (median error ≤ 0.03) | 0.028 | CONFIRMED (q is learned poorly: median error 0.37) |
| H-V7 v5 < v4 told wrong values | −2.4% | CONFIRMED |

### Part B, Bayes-optimal comparison (seeds 1820–1839; 6,720 runs; `results/bayes_confirm_20261027-030012`)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-B1 Bayes lowest | Bayes 26.91; v4 27.49, always 28.62, cusum 28.82, never 34.10 | CONFIRMED |
| H-B2 v4 within 5% of Bayes | +2.2% (95% CI +1.7% to +2.7%) | CONFIRMED |
| H-B3 v4 captures ≥ 80% of the achievable saving | 92% | CONFIRMED |

Descriptive: v5 is +5.6% from Bayes here. In this instance a failed task costs one call (22), which is less than a
cross-check call (24), so cross-checking does not pay.

### Part C, noisy comparisons (seeds 1720–1729; `results/v5_stress_20261027-030335`)
| e | v4 | always_x | v5 | v5 vs v4 |
|---|---|---|---|---|
| 0 | 151.2 | 156.0 | 148.5 | −1.8% |
| 0.1 | 151.2 | 163.5 | 150.4 | −0.5% |
| 0.2 | 151.2 | 170.8 | 151.2 | 0.0% |

**H-C1** (v5 < v4 at e = 0.1): p = 0.38, **NOT CONFIRMED**. v5's advantage disappears as comparisons become
unreliable, but v5 does not fall below v4. always_x degrades steadily.

### Reading
- Rule v5 removes the need for labelled calibration at no cost: it is equal to, or slightly better than, rule v4 told
  the labels (−1.0%), and much better than rule v4 without them (−11.8%).
- It also makes the persistence of false alarms irrelevant.
- Its advantage depends on reliable cross-check comparisons.
- Rule v4 is within 2.2% of the Bayes-optimal policy on a small instance solved exactly.

### Real-checker pilot (laptop, Ollama, fresh seeds 4100–4109; 27 Oct 2026, 17:42; `results/realagent_v5_20261027-174158`)
There were 0 cache misses, so every checker answer is a real model answer.

| Check | Result | Verdict |
|---|---|---|
| R-V1 v5 < v4 (told the calibrated q and f) | 75.3 vs 75.8 (−0.7%); 160 pairs p = 0.00089; per seed 8 of 10 lower, p = 0.032 | **MET** |
| R-V2 v5's learned f within 0.05 of the calibrated f | median error 0.080 (v5 overestimates f: 0.17–0.20 vs 0.14–0.15 for the 1.5B checker; 0.14–0.17 vs 0.05–0.06 for the 3B checker) | **NOT MET** |
| R-V3 (added after the preview) v5 at most 3% worse than v4 | −0.7% | MET |

Descriptive: v5 failed 0.0% of tasks, against 0.9–1.3% for v4.

**Reading:** with real checkers, rule v5 needed no labels and still had slightly lower loss than rule v4 given the
labelled calibration. However, its learned false-alarm rate was biased upwards. Possible reasons (to investigate, not
claimed):
- the false-alarm rate inside the loop differs from the one measured on the calibration tasks;
- the plug-in approximation;
- tools that agree on a wrong value.

**Diagnostic (descriptive, from rows.json, 27 Oct 2026, 18:30):**
- In these real runs, v5 cross-checked only about 0.02–0.03 times per task, i.e. about 3 flags per 120-task run, and
  resolved 58–100 false alarms in total across 40 runs per checker setting.
- Its learned q stayed at about 0.48, close to the prior mean of 0.5.
- So in the real pilot, v5 had too little evidence to learn its checker: its estimates mostly reflect the vague
  priors (prior mean f = 0.1, which explains the upward bias for the 3B checker, whose true f is about 0.05).

The real-checker result therefore shows that v5 **performs well without labels**. The evidence that it **learns** the
false-alarm rate comes from the longer simulation runs (median error 0.028). Planned follow-ups:
- keep the checker memory across runs;
- use longer runs.

