# Pilot findings (run on 20–21 October 2026)

Source: `results/pilot_20261020-235328/pilot_report.md`. The pilot used seeds 0–19, four settings
and three scenarios, giving 80 paired runs per scenario. All costs are simulated. Test seeds
100–129 were not touched.

## The decision: NO-GO under the pre-registered criteria

| Scenario | Best non-oracle baseline | Its median cost per success | Rule median | Rule vs baseline |
|---|---|---|---|---|
| S1 sudden drop | B4 CUSUM | 133.9 | 140.6 | 5.0% worse |
| S2 gradual decline | B4 CUSUM | 138.1 | 151.7 | 9.9% worse |
| S3 harmless drift | B4 CUSUM | 136.6 | 147.0 | 7.6% worse |

- **Criterion 1 is not met.** The rule won in 0 of the 3 scenarios.
- **Criteria 2 and 3 are met.**
  - The rule made fewer false switches than CUSUM.
  - Under harmless drift it used fewer checks than fixed-rate checking, at the same leak rate
    (0.245), in the one setting where protection alone did not justify a check.
- **Where the rule does well.**
  - In S1 it beat check-always, fixed-rate checking and the fixed-estimate planner, but
    never-checking had a slightly lower median (138.1 against 140.6).
  - In S2 it beat check-always, never-checking and the fixed-estimate planner, and roughly tied
    fixed-rate checking (151.7 against 151.1).
  - The fixed-estimate planner (B8, modelled on INTENT and MCPP)
  was by far the worst in S1 and S2, at 211.2 and 197.8. That supports Gap 1: estimates that do
  not update during the run are costly.

By the proposal's own rule (Table 3.16), the project should either pivot to "When does checking
pay off for tool agents?" or revise the rule and re-register it before re-testing. This is a
supervisor decision.

## Why the rule lost: three findings, each a design issue

1. **The switch line ignores leak loss.** The line compares price per success only (Section
   2.4.3). A silently degrading tool also makes whole tasks fail, so the rule stays on a bad tool
   too long.
   - Median delay before leaving a tool whose true rate fell below the line: 28 calls in S1 and
     84 in S2, against 12 for CUSUM.
   - An exploratory variant whose line also counts expected leak loss (`Rule_leakaware`) closed
     most of the gap: 134.3 against CUSUM's 133.9 in S1, 138.2 against 138.1 in S2 and 138.1
     against 136.6 in S3.
   - It was added after seeing the results, so this is a hypothesis, not a finding. It must be
     re-registered and tested on fresh seeds.
2. **The decision value is almost inactive.** The proposal sets the plan horizon to "calls left in
   this task", which is at most 5. Over that horizon a check can rarely change enough cost to pay
   for itself.
   - Only 0.8% of the rule's checks happened because of the decision value. Almost all checks
     came from the protection value or random audits.
   - With the horizon set to calls left in the run (capped at 50), this rose to 6.5%.
   - This matters most: the decision-aware part is the claimed novelty (C2), and as currently
     specified the pilot barely exercises it.
3. **S3 is not harmless once leaks count.** At 85%, staying on the cheap tool is above the
   price-only line (about 76%), but below the leak-aware line (about 89%). CUSUM "falsely" switched
   in S3 and still had the lowest cost per success.
   - The definitions of harmless drift and false switch need to be revisited with the
     leak-aware line.

## Questions to take to the supervisor (this week)

1. Pivot, or revise the rule? The revision would mean a leak-aware switch line and a longer plan
   horizon, then a re-registered pilot on new seeds.
2. Should the plan horizon be the task or the session? The tool choice persists across tasks, so a
   switch affects later tasks too.
3. Should CUSUM (B4) stay the main competitor? It is strong here because the drops are large and
   abrupt. Small or slow drift near the line is where a decision-aware rule should help; S2
   currently ends at 70%, only a few points below the line.

## What to write in the proposal (abstract and Table 3.16, "Results")

Replace the bracketed text with your own wording of the numbers above: cost per successful task
against CUSUM (+5.0%, +9.9% and +7.6%), false switches (fewer than CUSUM), checks under harmless
drift (fewer than fixed-rate at an equal leak rate), and the decision (NO-GO by the pre-registered
criteria; next step agreed with the supervisor). For feasibility, use about 0.9 CPU-seconds per
1,000 simulated tasks, and 6.5 minutes of wall time for the whole pilot on 2 cores.

---

# Re-test of the fixed rule (v2), 21 October 2026

The plan was written down first, in `PREREGISTRATION_v2.md` at 14:25. The test then ran on fresh
seeds 20–39; the report is `results/pilot_v2_20261021-142623/pilot_report.md`.

**In simple words: the fix worked, but only enough to tie, not to win.**

| Situation | Cost per successful delivery: fixed rule (v2) | Alarm method (CUSUM) | Old rule (v1) |
|---|---|---|---|
| Sudden drop (S1) | 134.9 | 134.0 | 138.3 |
| Slow decline (S2) | 138.9 | 139.4 | 153.9 |
| Small drop (S3) | 135.6 | 136.6 | 148.0 |

- **The fix closed the gap.** The old rule was 3–11% more expensive than the alarm method on these
  seeds. The fixed rule is within 1%: slightly better in two situations, slightly worse in one.
  - None of these differences is statistically meaningful (Wilcoxon p = 0.39–0.62).
- **The pass mark was not reached.** The rule needed to be at least 5% cheaper in 2 of 3 situations.
  Result: **NO-GO**.
  - Criterion 2 also missed by a hair in S1: 0.3 against 0.2 false switches per 1,000 tasks.
  - Criterion 3 was met: far fewer checks than fixed-rate checking (0.11 against 1.12 per task), with
    fewer leaks.
- **Decision, as written in advance:** switch to the backup question, "When does checking pay off
  for tool agents?". Confirm this with the supervisor.

---

# New direction: "When is checking worth paying for?" (21 October 2026)

## Draft research questions
- **RQ1:** When does paying for checks lower an agent's cost per successful task under silent tool
  degradation, as the size of the drop, the check price and the catch rate change?
- **RQ2:** Which checking-and-switching strategy is cheapest in each condition, and how close is it
  to the best possible (oracle, and later the exact optimum)?
- **RQ3:** Which design features matter: updating reliability during the run, counting lost answers
  (leaks) in the switch decision, and how far ahead the agent plans?

## Check-worth map (first run: `results/checkmap_20261021-144115/`)
**Setup**
- 126 conditions, built from:
  - drop of the cheap tool to 95% (no drop), 90%, 85%, 80%, 75%, 70% or 60%;
  - catch rate 0.5, 0.8 or 0.95;
  - check price 5%, 15% or 30%;
  - leak loss of 1 or 3 tasks.
- 6 strategies; new seeds 200–209.
- Settings were taken from the v2 pilot tuning and not re-tuned.

**Findings (in simple words)**
1. **No drop, or a small drop (to 90%):** checking does not pay. Never checking is about as
   cheap: the saving is −2% to +2%, except when checks are very cheap (5%), where it is up to +8%.
2. **Medium drop (75–85%):** checking pays the most. Up to 21% cheaper per successful task, with
   a 19% median saving at 75%. These are the quiet failures you cannot spot without checking.
3. **Big drop (60%):** checking helps less (+2% to +9%), because the many loud errors already show
   the tool is broken.
4. **Cheaper checks and better catch rates increase the saving.** Leak loss (1 against 3 tasks)
   barely changed the picture with this metric. That is because cost per successful task only
   counts leaks through lost successes.
5. **Who wins:** the CUSUM change alarm was cheapest in 49 of 126 conditions, decision rule v2 in
   40, never-checking in 22, always-checking in 13 and fixed-rate checking in 2. Rule v2 and CUSUM
   were within about 2% of each other everywhere (median by drop size).

**Next**
- Repeat the map with total loss per task, which counts leak loss directly.
- Add the exact optimum (B7).
- Run on CostBench tasks.

---

# Total-loss map and confirmed result (21 October 2026)

**Map re-scored with total loss per task** (spend plus leak loss; `results/checkmap_20261021-144627/`,
seeds 200–209):
- **Checking pays far more once wrong answers are charged for.** It saves at least 5% in 90 of 126
  conditions.
  - With leak loss = 3 tasks, the median saving is 21.9% (up to 43.7%), and checking pays even with
    no drop when checks are cheap.
  - With leak loss = 1 task, the median saving is 5.1% (up to 14.5%).
- **Who wins:**

  | Leak loss | Rule v2 | CUSUM | Always check | Never check | Fixed-rate |
  |---|---|---|---|---|---|
  | 1 task | 21 | 22 | 7 | 12 | 1 |
  | 3 tasks | 35 | 10 | 18 | 0 | 0 |

**Confirmatory test of H-leak** (`PREREGISTRATION_confirm_leak.md`, written before running; fresh
seeds 300–319; result in `results/confirm_leak_20261021-144904/`):
- With leak loss = 3, rule v2 had **8.3% lower total loss than CUSUM** (mean 149.4 against 163.5).
- It was cheaper in **54 of 63 conditions**.
- One-sided paired Wilcoxon p = 7e-126 over all pairs, and p = 1e-6 on per-seed means.
- **Decision: CONFIRMED.**

**Plain meaning:** when a wrong answer is cheap, a simple change alarm is as good as the decision
rule. When a wrong answer is expensive, the decision rule, which weighs the cost of wrong answers
when it decides, is clearly better.

**Not yet tested:** rule v2 against always-checking at high leak loss (always-checking won 18
conditions in the map), the exact optimum, and real CostBench tasks.

---

# Confirmatory test H-always: rule v2 vs always-check (21 October 2026)

`PREREGISTRATION_confirm_always.md` was written before running. Fresh seeds 400–419, leak loss = 3,
63 conditions. Result in `results/confirm_always_20261021-145230/`.

- **Decision: NOT CONFIRMED.**
  - The rule had lower total loss on average: 151.1 against 158.3, a mean difference of −3.5%. The
    difference was significant (p = 5e-44 over all pairs; p = 1e-6 on per-seed means).
  - It won 42 of 63 conditions, which meets the 2/3 bar.
  - It missed the pre-set −5% size criterion.
- **Where always-check still wins:** when the tool stays good or drops only a little (95% or 90%),
  especially with accurate checks (q = 0.95). This accounts for 18 of the 21 conditions the rule did
  not win.
  - In those conditions the rule checks a bit less (4.2 against 5.2 checks per task with no drop).
  - That lets slightly more wrong answers through (leak rate 0.048 against 0.032), and wrong answers
    are expensive here.
  - It also occasionally switches when nothing is wrong (switches in 4 of 10 runs with no drop).
- **Where the rule wins clearly:** medium and large drops. For example, at a drop to 75% its total
  loss was 151.6 against 168.6 for always-check.

**Plain meaning:**
- If mistakes are expensive and the tool is probably fine, simply checking everything is about as
  good as being clever, and slightly better.
- If the tool may really be degrading, the decision rule saves money.
- No single strategy wins everywhere. That is itself the answer to RQ2.

---

# Distance to the perfect-knowledge optimum (21 October 2026)

`ereplan/optimum.py` computes, for each run, the lowest expected total loss possible if the agent
knew the true success rate of every tool at every step. It does this by exact enumeration of when to
switch and which steps to check. The formula is verified against simulation in the tests. It is a
lower bound. Results are in `results/checkmap_20261021-144627/gap_to_optimum.md`, covering seeds
200–209 and all 126 conditions. This is descriptive and not pre-registered; nothing was tuned on
these seeds.

| Strategy | Extra loss vs optimum, leak 1 | Extra loss vs optimum, leak 3 | Share of possible saving captured, leak 3 |
|---|---|---|---|
| Decision rule v2 | +2.5% | +2.8% | 91% |
| CUSUM change alarm | +2.8% | +11.8% | 58% |
| Always check | +8.3% | +4.1% | 86% |
| Fixed-rate check | +8.7% | +26.4% | 16% |
| Never check | +8.7% | +32.3% | 0% |
| Oracle (reference) | +0.4% | +0.0% | 99% |

**Plain meaning:**
- The decision rule is the only real strategy that stays close to the best possible both when
  mistakes are cheap and when they are expensive: within about 3% in both cases.
- Every other strategy is good in one case and poor in the other:
  - CUSUM is close when mistakes are cheap, but 12% off when they are expensive.
  - Always-check is close when mistakes are expensive, but 8% off when they are cheap.

**Caveat:** in 5 of 126 conditions some strategy's 10-seed mean fell slightly (>2%) below the
expected optimum. This is sampling noise, because the bound is an expectation.

---

# Real CostBench tasks (21 October 2026)

`PREREGISTRATION_costbench.md` was written at 16:32, before running. Results are in
`results/costbench_20261021-163406/report.md`.

**Setup:** 194 real CostBench test queries (commit 6424069) with CostBench's own prices and solver,
no LLM. 96 conditions and seeds 500–511. Strategy settings were frozen from the synthetic study and
not re-tuned.

**Finding 1 (descriptive, before the test):** in CostBench, the cheapest route that avoids the
most-used tool costs only 0–0.53% more (median 0.1%). CostBench's composite tools are priced at
about the sum of their parts, so avoiding a doubtful tool is almost free on its native prices. The
test therefore also varied the price gap: the route with the tool 10% or 20% cheaper.

**Finding 2 (H-cb, pre-registered): CONFIRMED.** Rule v2 had the lowest extra loss over the
perfect-knowledge optimum among the real strategies at both leak levels.

Median extra loss over the optimum:

| Strategy | Wrong answer costs 1 task | Wrong answer costs 3 tasks |
|---|---|---|
| Decision rule v2 | +0.9% | +1.4% |
| Never check | +1.5% | +8.5% |
| CUSUM | +2.4% | +7.3% |
| Fixed-rate check | +4.5% | +8.6% |
| Always check | +12.2% | +8.0% |

**Honest notes:**
- On native CostBench prices with cheap mistakes, never-checking (+1.7%) was marginally better than
  the rule (+1.9%).
- When mistakes are cheap, all differences are small.
- The oracle's slightly negative values (−0.1% to −0.5%) are sampling noise: realised losses
  against an expected-value bound.

---

# Exploratory: "false reassurance" from checks that share the tool's weakness (21 October 2026, not pre-registered)

**Model:** after the tool degrades, a check catches its silent failures with probability
q × (1 − corr) instead of q, because the check shares the failure source. The agent still assumes
q = 0.8. Spare seeds 700–711; check price 15%; total loss per task.

Results (correlation 0 → 0.5 → 0.9):

| Tool drops to | Wrong answer costs | Never check | Always check | CUSUM | Rule v2 |
|---|---|---|---|---|---|
| 75% | 1 task | 148.0 → 148.0 → 148.0 | 146.5 → 160.8 → 168.6 | 134.4 → 134.7 → 136.2 | 134.6 → 137.1 → 147.9 |
| 75% | 3 tasks | 224.4 → 224.4 → 224.4 | 165.4 → 215.5 → **245.0** | 172.6 → 173.6 → 177.8 | 150.2 → 156.9 → 168.1 |
| 60% | 1 task | 133.9 → 133.9 → 133.9 | 140.1 → 149.4 → 168.9 | 131.8 → 131.9 → 133.0 | 134.5 → 135.3 → 137.4 |
| 60% | 3 tasks | 173.0 → 173.0 → 173.0 | 147.1 → 173.9 → **233.8** | 164.0 → 164.3 → 167.6 | 147.1 → 151.4 → 156.4 |

**What it shows:**
- With a highly correlated check (0.9), always-checking is **worse than never checking** in all four
  cases: 168.6 against 148.0, 245.0 against 224.4, 168.9 against 133.9, and 233.8 against 173.0.
- **Mechanism:** the check misses the new failures, so the agent's estimate says the tool is still
  fine. It keeps paying for checks and never switches.
- Never-checking relies only on loud errors, which are not fooled, so it does not suffer this effect.
- Rule v2 and CUSUM are hurt much less, but rule v2 still loses ground.

**Idea for a method contribution (hypothesis):** loud errors give a free, unbiased signal of the
failure rate. Comparing it with what checks report could estimate the real catch rate while running,
and so detect a correlated check. This needs testing.

**Status:** exploratory. It needs a pre-registered test on fresh seeds and a literature check
before it can be claimed.

---

# Confirmed: false reassurance, and the self-calibrating rule v3 (21 October 2026)

`PREREGISTRATION_selfcal.md` was written at 23:41, before running. Fresh seeds 900–919; 32 conditions;
results in `results/confirm_selfcal_20261021-235119/`.

**H-FR (false reassurance): CONFIRMED.**
- With a check that shares the tool's weakness (correlation 0.9), always-checking was worse than
  never checking in **16 of 16** conditions.
- Mean total loss was 204.7 against 168.6, which is +21% (p = 2e-52).
- Paying for every check cost more than not checking at all.

**H-SC (the detector helps): CONFIRMED, but small.**
- With correlated checks, rule v3 had a mean total loss of 150.6 against 154.0 for v2.
- That is −2.2%, just over the pre-set −2% bar (p = 5e-27).

**H-NI (no harm when checks are fine): CONFIRMED.** With independent checks, v3 scored 145.5 against
145.7 for v2 (−0.1%).

**Mean total loss of every strategy:**

| Strategy | Independent checks | Correlated checks (0.9) |
|---|---|---|
| Rule v3 | **145.5** | **150.6** |
| Rule v2 | 145.7 | 154.0 |
| CUSUM | 149.7 | 155.0 |
| Always check | 159.0 | 204.7 |
| Never check | 168.6 | 168.6 |

Rule v3 had the lowest loss of all strategies in both settings.

**Development note:** v3's one setting (q prior strength 3) was chosen on dev seeds 800–805. Unit
test `test_selfcal_estimator_recovers_bad_checker` shows the joint estimate recovers a 10% catch rate
when the agent assumes 80%.

---

# Real AI agent test: built, not yet run (21 October 2026)

**Tasks:** `ereplan/realagent.py` uses real GSM8K maths problems (MIT licence, commit 3101c7d).

**Roles of the local LLM (via Ollama):** the same model plans the calculator steps and judges whether
results are correct.
- Tools are real Python calculators. Service A degrades into subtle wrong answers.
- The judge's real catch rates are measured first, and strategies are told the catch rate on obvious
  faults.

**Predictions:** R1–R4 were written in `PREREGISTRATION_realagent.md` before any real data existed.

**Status:**
- The pipeline is verified end to end with a stand-in model and a simulated judge. Those numbers are
  not results.
- The real run must happen on the student's laptop, because this environment cannot download models.
  `RUN_REAL_AGENT.md` gives the steps, which take about 3–5 hours on a CPU.
