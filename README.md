# e-Replan: implementation and experiments

Implementation for the final-year project *When to Pay for a Check: Cost-Aware Checking and Switching for LLM
Tool-Use Agents under Silent Tool Degradation* (Yelani Hanwella, w1956183).

- **Run and check it on your own machine:** `RUN_LOCAL.md`
- **What was built and what the results mean:** `IMPLEMENTATION_RESULTS_2026-11-10.md`
- **Decision log:** the dated entries further down this file.

## History: the October pilot (the first stage of this implementation)

The pilot from Section 3.3.5.10 of the proposal *Check What Matters*. It is a CPU-only Python
simulation: no LLM, no API keys, and every price is a simulated number.

## Run it (about 10 minutes in total)

```bash
pip install numpy scipy matplotlib pytest      # Python 3.11+ (tested on 3.13)
python -m pytest -q                            # 20 tests (worked examples, optimum formula, false alarms, persistence)
python -m ereplan.pilot --quick                # 1-minute smoke run
python -m ereplan.pilot                        # the real pilot: tune on seeds 50-59, judge on 0-19
python -m ereplan.demo --params results/<pilot folder>/manifest.json
```

More experiments (added 21 October):
```bash
python -m ereplan.checkmap                      # check-worth map, 126 conditions (about 3 min)
python -m ereplan.confirm leak                  # confirmatory test: rule v2 vs CUSUM, seeds 300-319
python -m ereplan.confirm always                # confirmatory test: rule v2 vs always-check, seeds 400-419
python -m ereplan.gap                           # distance to the perfect-knowledge optimum (about 10 min)
python -I tools/costbench_routes.py <CostBench clone>   # build data/processed/costbench_routes.json
python -m ereplan.costbench_exp                 # evaluation on real CostBench tasks (about 1 min)
python -m ereplan.confirm_selfcal               # false reassurance + self-calibrating rule v3, seeds 900-919
python -m ereplan.realagent ...                 # REAL AI agent test on your laptop: see RUN_REAL_AGENT.md
python -m ereplan.falsealarm_exp map            # check-worth map WITH checker false alarms (added 22 Oct)
python -m ereplan.falsealarm_exp confirm        # confirmatory test of rule v4 (false-alarm aware), seeds 1200-1219
python -m ereplan.showcase                      # FIVE-MINUTE DEMO for the supervisor (see DEMO_SCRIPT.md)
python -m ereplan.persistence_exp dev           # part E: tune the 3 literature baselines on dev seeds 1500-1505 (under 1 min)
python -m ereplan.persistence_exp confirm       # part E: persistence + literature baselines, seeds 1400-1419 (about 1 hour)
python -m ereplan.realagent persist --seeds 10 --seed-start 4000   # part E3: v4 vs v4_ind with the REAL checkers (Ollama; see RUN_PART_E3.md)
EREPLAN_REPLAY=1 python -m ereplan.realagent run --model qwen2.5:1.5b   # replay a real-agent run from the saved LLM answers, no Ollama needed
```
Each test's plan was written before it ran: see the `PREREGISTRATION_*.md` files.

Each pilot run writes a folder in `results/` containing:
- `pilot_report.md`: the go/no-go decision and every table;
- `runs.csv`: one row per strategy, setting, scenario and seed;
- `manifest.json`: seeds, settings hash, tuned parameters, Python version and CPU time;
- `cost_per_success.png`: a box plot comparing the strategies.

The demo prints the rule's decision messages and saves the plot of the range against the switch line.

## What each file does (read them in this order)

| File | What it is | Proposal section |
|---|---|---|
| `ereplan/config.py` | The three tools, their simulated prices, and the pilot grid (q in {0.5, 0.8}, check price 15% or 30%) | Table 3.16 |
| `ereplan/env.py` | The hidden success rates for S1–S3, and every random outcome drawn in advance so that all strategies face the same luck ("common random numbers") | 3.3.5.9, Table 3.12 |
| `ereplan/estimator.py` | The check-corrected success-rate range: a grid posterior over the last W calls, where a failure is seen with probability (1 − p)·d | 3.3.5.5 "Range", 2.4.5 |
| `ereplan/strategies.py` | The switch line, the protection value, the decision value, the three-zone rule, and baselines B1–B4, B6 and B8 | 3.3.5.4–3.3.5.5 |
| `ereplan/runner.py` | Runs one strategy for 120 tasks of 5 calls and computes the Table 3.14 metrics | 3.3.5.9 |
| `ereplan/pilot.py` | Tuning (at most 8 configurations per strategy), judging, paired Wilcoxon tests and the three GO criteria | Table 3.16 |
| `ereplan/demo.py` | The working demonstration | 3.3.5.10 |
| `tests/test_core.py` | The 60/77 switch-line example, the 18%-vs-82% bias example, decision value = 0 far from the line, and reproducibility | 2.4.5, 3.3.5.5 |

## How one call works (follow `runner.py`)

1. The rule computes the **switch line**. This is the success rate below which moving to the
   cheapest alternative tool is cheaper for the rest of the plan:
   `u·c / (R_alt + c_switch)`. For example, with 5 calls left, price 20 and an alternative
   costing 24 at 95% success, the line is 100 / (126.3 + 5), about 76%.
2. It reads the tool's **95% range** from the estimator.
   - If the whole range is below the line, it switches.
   - If the range crosses the line, it checks when the **protection value** plus the
     **decision value** is at least the check price.
   - If the range is above the line, it checks only when the protection value alone pays for
     the check.
   - In every zone it also checks at random, with probability ε.
3. The environment decides the outcome:
   - success;
   - a loud failure, which is seen for free and retried;
   - a silent failure caught by a check, which is retried;
   - a **leak**, a silent failure that went unchecked, so the task fails.
4. The estimator is updated with whether a failure was *seen*, corrected for the checks that miss
   failures.

## Design choices made while building (not stated in the proposal)

These need your sign-off and a line in the decision log.

- **Planner keeps its tool across tasks.** It picks the cheapest tool once and moves only when the
  switch rule says so. Re-planning at every task made the agent ping-pong between tools.
- **Prior for tools with no data.** Each tool starts from its advertised rate (95%), worth 20 calls.
  This weight fades to zero as the window fills, so a full window uses the uniform prior the
  proposal specifies. Without it, an unused alternative looks 50% reliable and the agent never
  switches.
  - The first pilot run used a prior that did *not* fade. This kept pulling estimates up after a
    real drop. That run is kept in `results/superseded/` for transparency.
- **One capability per task.** All 5 calls in a task use interchangeable tools, so R_rest = 0.
  CostBench tasks are not loaded yet; this is the proposal's "own CostBench-style tasks" fallback.
- **Latency weight λ = 0** in the pilot, so cost is price only.
- **Exploratory variants.** `Rule_session` and `Rule_leakaware` were added *after* seeing the first
  results. They appear in the report but are not part of the go/no-go decision.

## Decision log

- **6 Nov 2026 — renamed `rule_v51.py` to `rule_rho.py`.** The class inside (`LoudShareRule`,
  registry name was `Rule_v5_1`) learns the share of loud failures, rho (FR20). The proposal uses
  "rule v5.1" for a *different* requirement (FR19: a third source of a different model family on
  flagged calls, a small labelled audit, and a fallback to rule v4 when shared mistakes are
  common). The two were never the same rule; the file name was a leftover from an earlier dev
  session and would have caused real confusion once FR19 is built. Renamed to `rule_rho.py` /
  `Rule_v5_rho` (and its variants `Rule_v5_rho_mean`, `Rule_v5_rho_lcb`, `Rule_v5_rho_noaudit`).
  No behaviour changed; all 48 tests still pass. Historical results in `results/` that used the old
  names are untouched and are read as `Rule_v5_1` in their own CSVs — this mapping is the record of
  what they are.

- **6 Nov 2026 — built FR19, rule v5.1** (`ereplan/rule_v5_1.py`, registry name `Rule_v5_1`): a third source
  on a sample of flags, a small labelled audit, and a fallback to a v4-style decision when the believed
  shared-mistake rate (sigma_hat) is high. All label-free except the audit, by design (see the module
  docstring for the exact mechanism and two design choices that need the supervisor's sign-off: the
  method-of-moments simplification of the three-source estimator, and the decision-level — not full
  behavioural — meaning of "fallback"). 8 new unit tests (`tests/test_v5_1.py`) check the sigma estimator,
  the audited q/f, and the fallback trigger directly (isolated from the simulator) and pass; all 48 earlier
  tests are unaffected (56/56 total).
  **Known limitation, not yet resolved:** in full simulation runs, sigma_hat stays low even at xc_shared =
  0.7, because Rule_v5_1 (like v5 and v5_s) checks only a small share of calls, so evidence for the third
  source and the audit accumulates slowly. The isolated unit tests confirm the estimator itself is sound;
  whether it accumulates enough evidence to matter inside a real run — and whether fallback actually helps
  total loss when it does trigger — is exactly what the FR21 ablation and a dedicated confirmatory test
  (next) need to establish. Flagging this now rather than after the ablation is run, so it isn't mistaken
  for a finding.

- **9 Nov 2026 — ran the FR21 ablation** (`ereplan/ablation_v51.py`, `run_ablation.py`,
  `PREREGISTRATION_ablation_v51.md`): rule v5.1 with each of its five ingredients removed in turn
  (false-alarm term, persistence/cross-check, switching, label-free learning, change detection),
  pre-registered before any multi-condition run, dev smoke test on seeds 1750-1755 (6 seeds, no
  bugs, nothing tuned), then the confirmatory test on seeds 1800-1819 (20 seeds, run once; full
  report in `results/ablation_confirm_20261109-202104/report.md`). **4 of 5 primary hypotheses
  CONFIRMED** (removing the false-alarm term, persistence/cross-check, switching, or change
  detection each raises total loss, Holm-corrected p < 0.05): switching matters most (+18.3%
  without it), then change detection (+3.0%), then the false-alarm term (+2.3%), then persistence/
  cross-check (+0.2%, smallest but still significant). **H-A4 (label-free learning) was NOT
  confirmed**: with the checker told the true q and f instead of learning them, loss was actually
  very slightly (and not significantly) lower than the full rule's (-0.1%, p = 0.92). Reported here
  as a genuine negative result, not hidden or re-run to force significance: at these conditions
  (q_assumed = q_true, i.e. the full rule's own prior already starts correct), learning q and f from
  scratch costs essentially nothing extra, which is a reasonable finding given rule v5's own H-V4 in
  PREREGISTRATION_v5.md showed learning costs little there too. This also means FR19's sigma_hat
  limitation flagged above did not materially hurt the full rule in these conditions, but it does
  NOT establish sigma_hat is accurate — that remains the open, unresolved limitation above.

  This directly answers the question that limitation raised: fallback/learning did not need to be
  perfect to avoid hurting the full rule's loss here, but C5's ablation claim about the label-free
  ingredient specifically is not supported by this run and should be reported as such in the thesis,
  alongside the 4 ingredients that are supported.

- **9-10 Nov 2026 — ran the FR20 confirmatory test** (`ereplan/rule_rho.py`'s `Rule_v5_rho` and variants,
  `run_rho.py`, `PREREGISTRATION_rho.md`): does learning the loud-failure share rho beat the old fixed
  assumption (rho = 0.5) when that assumption is actually wrong (true rho in {0, 0.1, 0.3}, i.e. failures
  are mostly or entirely silent, as in the FreshQA motivating case)? This needed a new, additive mechanism
  first: `runner.run()` gained an optional `rho_belief` override (3 lines; default `None` reproduces the
  old behaviour exactly) so a strategy can be handed a WRONG fixed belief while the environment still
  generates failures at the TRUE rho — previously the same `Setting` object fed both, so this mismatch
  couldn't be simulated at all. 5 new unit tests (`tests/test_rho_belief.py`) check the override reaches
  only the strategy, not the environment, and that `rho_hat` reproduces; all 67 tests pass (62 earlier +
  5 new). Pre-registered before any multi-condition run; dev smoke test on seeds 1850-1855 (6 seeds, no
  bugs, nothing tuned), then the confirmatory test on seeds 1900-1919 (20 seeds, run once; full report in
  `results/rho_confirm_20261110-022819/report.md`).

  **Both primary hypotheses CONFIRMED.** H-R1: the rule that learns rho (cap mode, proposal default) beats
  the old fixed-wrong assumption by 3.2% (Holm-corrected p = 9.5e-07). H-R2: it is within 5% of an oracle
  told the true rho directly — in fact it slightly *beat* the oracle (145.5 vs 147.4, -1.2%), which needs
  an honest caveat: the "told" baseline here is just `Rule_v5_x` with the correct rho and no extra audit
  mechanism, while `Rule_v5_rho`'s cap mode also raises its audit rate when rho_hat looks lower than the
  default (`audit_gain`, a design choice from 31 Oct). The gain over the oracle is plausibly that extra
  auditing improving the checker's (q, f) estimates generally, not evidence that learning rho itself beats
  knowing it — `rho_noaudit` (same learning, no extra audits) scores almost identically to `rho_cap`
  (145.4 vs 145.5), which is consistent with that reading and is reported here rather than left to look
  like a stronger result than it is. Descriptively, `rho_lcb` (the pessimistic lower-credible-bound mode)
  was the worst of the four learning modes (149.1), and the learned `rho_hat` had a median error of 0.083
  against the true value — a real but non-trivial residual, consistent with FR19's own note (6 Nov entry
  above) that infrequent checking slows learning. The sanity conditions (true rho = 0.5, the old assumption
  actually correct) confirm learning does not materially hurt there either (+2.0% of the fixed baseline's
  loss).

- **10 Nov 2026 — ran FR13 (gradual drift + cost-weight sensitivity)** (`fr13_sensitivity.py`,
  `results/fr13_20261110-025300/report.md`). Descriptive/exploratory, not a confirmatory pre-registered
  test (consistent with how the other descriptive sweeps here, e.g. H-A6, H-R3/H-R4, are labelled) -- 20
  seeds, nothing tuned against the result.

  **Part A (S2_gradual, a slow onset instead of a sudden drop):** Rule_v5_1's mean loss (137.6) was NOT the
  lowest -- plain Rule_v5 (137.4, no third source/audit/fallback) and rule v4 (137.6, tied) both matched or
  beat it, though the gap is tiny (0.2, well inside likely noise at this sample size; no formal test was
  run since this was not pre-registered as confirmatory). Reported as observed rather than rounded in
  v5.1's favour.

  **Part B (cost-weight sweep, leak_mult in {0.5..5} x check_frac in {0.05..0.30}, S1_sudden):** a more
  important, genuine finding. **Rule_v5_1 does NOT consistently beat rule v4 across this grid** -- it loses
  (higher mean loss) in 10 of 25 cells, concentrated at leak_mult >= 2 (higher wrong-answer cost) regardless
  of check_frac. The full cell list is in the saved report, not cherry-picked. A plausible reading, stated
  as a hypothesis for later work rather than an established fact: FR19's extra machinery (the third source
  and the labelled audit) has its own cost (third_check_price, audit_price) that must be earned back by
  catching shared mistakes, and on S1_sudden with xc_shared = 0.3 (a moderate, not extreme, shared-mistake
  rate) that trade may not pay once wrong answers are already expensive enough that rule v4's simpler,
  cheaper policy is competitive on its own. **This qualifies FR19's claim: rule v5.1 is not a free upgrade
  over v4/v5 across the whole cost-weight range, and the thesis should report this limitation explicitly
  rather than only the conditions (PREREGISTRATION_v5.md's own grid; FR21's ablation grid) where it was
  shown to help.** This is exactly the kind of result the project's academic-integrity rules ask to be
  surfaced, not smoothed over, and is flagged here for the supervisor and for the thesis's limitations
  section.

- **10 Nov 2026 — FR11 done: CostBench with error rates of real checkers** (`run_fr11.py`,
  `PREREGISTRATION_fr11_realcheckers.md`, `results/fr11_confirm_20261110-202709`). The synthetic (q, f, pi) grid was
  replaced by the four checker profiles measured in this project (Qwen2.5 1.5B and 3B on arithmetic; Phi-4 Mini and
  Llama 3.1 8B on FreshQA; all repeat their verdicts). Seeds 2800-2817, run once. All three hypotheses CONFIRMED:
  v5 without labels beats v4 without labels (-13.3%), beats always_x (-24.6%) and matches v4 told q and f (+0.1%).
  Limits: the rates are real but were measured on other tasks (no model judged CostBench outputs; Ollama cannot run
  on the cloud machine); v5 beats never checking by only 1-3%; its learned q is poor (median error 0.26-0.49).

- **10 Nov 2026 — FR16/FR17 done: FreshQA confirmatory test with two real judge families** (`run_freshqa_confirm.py`,
  `PREREGISTRATION_freshqa.md`, `results/freshqa_confirm_20261110-204328`). Uses the cached verdict files collected
  on the laptop; the design varies staleness probability (100/50/25%) and B's price (24/30), as the proposal
  required. Development run on seeds 2500-2509, then seeds 2700-2719 once. **The main claim was NOT confirmed:** the
  rule (rho_cap) lost to "buy tool B from the start" by 8.5%. Learning rho did not beat plain v5 on fresh seeds
  (+1.5%, the development gain did not replicate), and the 25%-staleness subset was not significant (-1.3%,
  p = 0.27). Confirmed: the rule beats never checking by 20.4%. Design choice needing sign-off: the proposed rule was
  fixed as rho_cap (the variant FR20 confirmed) instead of the development-best rho_noaudit; the two ended within
  0.5 of each other.

- **10 Nov 2026 — state at the end of the implementation.** 71 tests pass. Every FR marked "Must" has a result.
  What the evidence now supports, and what it does not, is in `IMPLEMENTATION_RESULTS_2026-11-10.md`.


- **10 Nov 2026 — FR18 built and tested: rule v6 and "any tool can degrade"** (`ereplan/rule_v6.py`, `run_anytool.py`,
  `PREREGISTRATION_anytool.md`, seeds 5200-5219). The rule beats committing to any single tool by 15-27% (three
  hypotheses confirmed). Two NOT confirmed: it does not beat never checking (-0.3%), so in this setting the gain is
  from switching, not from paid checks; and re-testing a left tool (v6) does not beat v5 (+0.1% where a tool is
  repaired, +0.8% overall). Per the pre-registration, v5 stays the proposed rule and v6 is a reported negative result.
  Design choice: v6's waiting time (150 calls, doubling) was fixed before any run and never tuned.

- **10 Nov 2026 — boundary map: monitoring vs buying the better tool** (`run_boundary.py`, `PREREGISTRATION_boundary.md`,
  seeds 5100-5119). Monitoring region confirmed (-27.3%). Buying region NOT confirmed (fixed B only 1.2% cheaper,
  p = 0.077). Break-even premium on the simulator: about 12-21%. The simulator and FreshQA disagree in strength; see
  the outcome section of the pre-registration. 76 tests pass.

