# Full implementation: results and what they mean (6–10 November 2026)

Student: Yelani Hanwella (w1956183). Code: `ereplan`. Every test below was pre-registered before it was run,
except FR13, which is a descriptive sweep. 76 automated tests pass.

## 1. What was built and run

| Item | What it is | Seeds (run once) | Result |
|---|---|---|---|
| FR19 | Rule v5.1: third source, small labelled audit, fall-back to v4 | – | Built; 8 unit tests |
| FR21 | Ablation: remove one of five ingredients | 1800–1819 | 4 of 5 confirmed |
| FR20 | Learn the loud share ρ | 1900–1919 | 2 of 2 confirmed (simulator) |
| FR13 | Gradual drift and cost-weight sweep (descriptive) | 1950–1969 | A limit found for v5.1 |
| FR11 | CostBench with the error rates of four real checkers | 2800–2817 | 3 of 3 confirmed |
| FR16, FR17 | FreshQA with two real judge families | 2700–2719 | Main claim **not** confirmed; 1 of 4 confirmed |
| FR18 | Rule v6 (re-test a left tool); any tool can degrade | 5200–5219 | 3 of 5 confirmed |
| Boundary | Monitoring vs buying the better tool, 25-cell map | 5100–5119 | 1 of 2 confirmed |
| NFR2 | At least 50 unit tests | – | 76 |

## 2. Results in detail

### FR21 ablation (loss when one ingredient is removed from rule v5.1)
| Removed | Change in loss | Verdict |
|---|---|---|
| Switching | +18.3% | Confirmed |
| Change detection | +3.0% | Confirmed |
| False-alarm term | +2.3% | Confirmed |
| Cross-check (persistence) | +0.2% | Confirmed, but tiny |
| Label-free learning (told q, f instead) | −0.1% | Not confirmed (p = 0.92) |

Reading: label-free learning does not lower loss. It removes the need for labelled calibration at no cost.

### FR20 learning ρ (simulator; true ρ of 0, 0.1 or 0.3 while the old rule assumes 0.5)
- Learning ρ vs the fixed wrong value: 145.5 vs 150.4 (−3.2%, p = 9.5e-07). Confirmed.
- Within 5% of a rule told the true ρ: 145.5 vs 147.4. Confirmed.
- Median error of the learned ρ: 0.083. When 0.5 was already right, learning cost +2.0%.

### FR13 sensitivity (descriptive, no tests)
- Gradual drift: v5.1 137.6, v5 137.4, v4 137.6, never 148.3, always 188.8.
- Cost-weight sweep (25 cells): v5.1's mean loss was not below v4's in 10 cells, mostly where a wrong answer costs
  2 tasks or more. The differences are small (mostly under 1%) and were not tested. v5.1 is not a free upgrade.

### FR11 CostBench with real-checker rates
Profiles: Qwen2.5 1.5B (q 0.98, f 0.14), Qwen2.5 3B (0.99, 0.05), Phi-4 Mini (0.81, 0.56), Llama 3.1 8B (0.76, 0.52);
all repeat their verdict on a retry.

| Hypothesis | Result | Verdict |
|---|---|---|
| v5 (no labels) below v4 without labels | 111.0 vs 128.1 (−13.3%) | Confirmed |
| v5 below cross-checking everything | 111.0 vs 147.2 (−24.6%) | Confirmed |
| v5 (no labels) equivalent to v4 with labels, ±3% | 111.0 vs 110.9 (+0.1%) | Confirmed |

Limits: v5 beats never checking by only 1.2–3.0%; its learned catch rate is poor (median error 0.26–0.49). The
rates are real but were measured on arithmetic and question-answering tasks, not on CostBench outputs.

### FR16 and FR17 FreshQA with real judges (the proposal's main-claim test)
| Strategy | Mean loss | Wrong answers kept | Failed tasks |
|---|---|---|---|
| Buy the fresher tool B from the start | 142.4 | 0.0% | 0.0% |
| v5 | 152.3 | 4.5% | 0.0% |
| Rule with learned ρ (noaudit variant) | 154.0 | 3.7% | 0.0% |
| **Rule with learned ρ (proposed)** | **154.5** | 3.8% | 0.0% |
| v4 (told q, f) | 156.8 | 3.1% | 5.1% |
| Never check | 194.1 | 22.2% | 0.1% |
| Cross-check everything | 254.8 | 4.7% | 0.3% |

| Hypothesis | Result | Verdict |
|---|---|---|
| H-F1 rule below "buy B" (main claim) | +8.5% (CI +4.1% to +13.2%) | **Not confirmed** |
| H-F2 rule below never checking | −20.4%, p = 9.5e-07 | Confirmed |
| H-F3 rule below v5 (learning ρ helps) | +1.5%, p = 0.91 | **Not confirmed** |
| H-F4 rule below "buy B" when staleness is rare (25%) | −1.3%, p = 0.27 | **Not confirmed** |

The rule was cheaper than "buy B" in 2 of 12 cells (staleness 25% and B priced at 30: −3.3% and −10.5%); this is
descriptive only. Phi-4 Mini and Llama 3.1 8B give the same picture (154.0 and 155.1).

### FR18 any tool can degrade (which tool breaks is random, so no tool can be bought safely in advance)
| Hypothesis | Result | Verdict |
|---|---|---|
| Rule below fixed tool A | 148.6 vs 175.5 (−15.3%) | Confirmed |
| Rule below fixed tool B | 148.6 vs 199.3 (−25.4%) | Confirmed |
| Rule below fixed tool C | 148.6 vs 203.2 (−26.9%) | Confirmed |
| Rule below never checking | 148.6 vs 149.1 (−0.3%, p = 0.52) | **Not confirmed** |
| Re-testing (v6) below v5 where a tool is repaired | +0.1%, p = 0.61 | **Not confirmed** |

Reading: adapting beats committing to any tool, but here the gain comes from switching, not from paid checks.
Re-testing a left tool did not help, so v5 remains the proposed rule.

### Boundary map (simulator): rule vs buying tool B; negative = the rule is cheaper
| Tool A degrades in | B +10% | B +20% | B +35% | B +50% | B +100% | Break-even premium |
|---|---|---|---|---|---|---|
| 0% of runs | −6.1% | −12.5% | −20.2% | −26.8% | −43.1% | rule always cheaper |
| 25% | −1.1% | −6.2% | −12.9% | −18.2% | −31.3% | rule always cheaper |
| 50% | +1.1% | −3.6% | −8.8% | −14.0% | −25.4% | about +12% |
| 75% | +2.9% | −1.4% | −5.4% | −9.2% | −18.9% | about +17% |
| 100% | +3.3% | +0.2% | −2.7% | −6.7% | −15.7% | about +21% |

Monitoring region (B at least 50% dearer, A degrades in at most half of runs): rule −27.3%, confirmed. Buying region
(B at most 20% dearer, A degrades in at least 75% of runs): buying only 1.2% cheaper, p = 0.077, not confirmed.
The simulator and FreshQA disagree in strength (on FreshQA the rule lost by 7–24% at +20% and +50%); the likely
reason, untested, is that FreshQA staleness is silent and the cheap judges cannot detect it.

## 3. What the evidence supports now

**Supported**
1. On the simulator and on CostBench, the rule without labelled calibration matches the rule that is given labels,
   and beats the no-label alternative (FR11, earlier CostBench part 2).
2. Switching, change detection and the false-alarm term each lower loss (FR21).
3. Methods that retry a flagged step fail tasks when real checkers repeat their verdicts; cross-check rules do not
   (v4 5.1% failed vs 0.0% on FreshQA; v4 without labels 15.3% vs 0.1% on CostBench).
4. Monitoring beats not monitoring on FreshQA (−20.4%).
5. When it is not known which tool will degrade, the rule beats committing to any one tool by 15–27% (FR18).
6. On the simulator, buying the better tool pays only when it costs at most about 12–21% more and the cheap tool
   is likely to degrade (boundary map).

**Not supported**
1. The main claim on real data: the rule does not beat simply paying for the better tool on FreshQA.
2. Learning ρ helps on the simulator but not on FreshQA.
3. Label-free learning as a source of lower loss (it is cost-free, not beneficial).
4. Rule v5.1 as a general improvement over v4 and v5.
5. Paid checks adding value over switching alone when half of failures are loud (FR18: rule vs never, −0.3%).
6. Re-testing a tool the rule has left (v6).
7. One boundary for both testbeds: the simulator's break-even (12–21%) does not match FreshQA.

**Honest scope for the thesis and paper:** the rule is useful when the better tool is not known in advance or
costs clearly more and degradation is uncertain; when a reliably better tool costs only 20–50% more, buying it wins.

## 4. Decisions that need the supervisor's sign-off
1. Rule v5.1 estimates the shared-mistake rate with a method of moments, a simplification of the three-source estimator.
2. Rule v5.1's fall-back changes only the decision; it still pays for cross-checks.
3. The ablation removes "persistence" by switching the cross-check off.
4. The FreshQA test fixed the proposed rule as the FR20-confirmed variant, not the development-best one.
5. How to reframe the main claim after H-F1 failed (section 3).

## 5. Limits that still apply
- No model was called in these runs. FreshQA verdicts are cached real verdicts; FR11 uses measured rates.
- On FreshQA, when A goes stale, question order and timeouts are simulated.
- The cheap judges cannot detect staleness on fast-changing questions (q − f at most 0.06).
- Rule v5.1's shared-mistake estimate stays near zero in full runs; its accuracy is not validated.
- Rule v5.1 and the ρ-learning rule are separate classes; no rule combines both.
- The proposed rule is v5. Rules v5.1, v6 and the ρ-learning rule are tested extensions that did not earn a place in it.

## 6. Where everything is
Pre-registrations with outcomes: `PREREGISTRATION_ablation_v51.md`, `_rho.md`, `_fr11_realcheckers.md`, `_freshqa.md`.
Drivers: `run_ablation.py`, `run_rho.py`, `fr13_sensitivity.py`, `run_fr11.py`, `run_freshqa_confirm.py`,
`run_anytool.py`, `run_boundary.py`. More pre-registrations: `PREREGISTRATION_anytool.md`, `_boundary.md`.
Reports and raw rows: `results/ablation_confirm_20261109-202104`, `rho_confirm_20261110-022819`,
`fr13_20261110-025300`, `fr11_confirm_20261110-202709`, `freshqa_confirm_20261110-204328`. Decision log: `README.md`.
