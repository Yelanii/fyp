# FreshQA with real AI judges: development findings (1 Nov 2026, exploratory, not pre-registered)

Code: `ereplan/freshqa_real.py`.
- Real verdicts collected on the student's laptop: Qwen2.5 1.5B/3B, Phi-4 Mini and Llama 3.1 8B, all at temperature 0.
- False-alarm grid extended for these runs only: `EREPLAN_FMAX=0.95`. The default stays 0.5, so earlier results are unchanged.
- Development seeds 2500–2519.

## 1. How good are cheap AI judges at spotting out-of-date answers? (real measurement)
q = the share of stale answers the judge says NO to. f = the share of correct answers it says NO to. J = q − f; a judge with J = 0 is guessing.

| Judge (prompt) | All questions: q / f / J | Fast-changing only: q / f / J |
|---|---|---|
| Qwen2.5 1.5B (dated prompt) | 0.99 / 0.96 / +0.03 | 0.99 / 0.99 / 0.00 |
| Qwen2.5 3B (dated prompt) | 1.00 / 0.99 / +0.01 | 1.00 / 1.00 / 0.00 |
| Qwen2.5 1.5B (plain prompt) | 0.99 / 0.88 / +0.11 | 0.99 / 0.93 / +0.06 |
| Qwen2.5 3B (plain prompt) | 0.98 / 0.91 / +0.07 | 0.99 / 0.99 / 0.00 |
| Phi-4 Mini (plain prompt) | 0.81 / 0.56 / +0.25 | 0.83 / 0.78 / +0.05 |
| Llama 3.1 8B (plain prompt) | 0.76 / 0.52 / +0.24 | 0.79 / 0.77 / +0.02 |

Finding 1: none of these cheap judges can tell a stale answer from a fresh one on fast-changing facts (J ≤ 0.06).
- Their J of about 0.25 on all questions comes from saying YES more often to stable facts.
- All stale answers are fast-changing questions. So the judge is detecting the type of question, not staleness.
- The dated prompt ("Today is 21 April 2026") made the Qwen judges say NO to almost everything (99–100% of answers).

Finding 2: comparing two answers works.
- A stale answer and a fresh answer were wrongly called "the same" 0–10% of the time.
- So the cross-check step of rule v5 is reliable with real models.

## 2. Rules with real verdicts (phi4-mini, development seeds 2500–2509, loss vs never checking)
| Strategy | News stream | Mixed stream | Failed tasks (news) |
|---|---|---|---|
| v4 (told q, f) | −45.5% | −27.1% | 6.7% |
| v5 (no labels) | −45.3% | −30.2% | 0.0% |
| always check | −26.7% | +11.6% | 98.6% |
| cross-check all | −11.1% | +16.8% | 0.2% |
| Kiyani-style SSV | −10.8% | +16.5% | 48.5% |
| Hou-style RDE-CUSUM | −27.6% | +4.8% | 93.9% |
| GLR-klUCB | −25.7% | +11.7% | 97.7% |
| **use tool B from the start (reference)** | **−57.3%** | **−37.5%** | 0.0% |

Llama 3.1 8B gives the same picture.

Finding 3: repeated false alarms from real judges break retry-based methods. always-check, RDE-CUSUM and GLR-klUCB fail 94–99% of news tasks. This is the theory (Core 3) on real data.

Finding 4: in this setup, simply paying for the fresh tool B beats every adaptive rule, including v5.
- Tool B costs only 20% more than A.
- Tool A always goes stale in this setup, and badly.
- Diagnosis from traces, on runs where A never goes stale (`fqr_mixed@p0`):
  - v4 and v5 switch away from the healthy A within 27–46 calls, and never return. They spend 92–95% of calls on B, and their loss (131–146) is above never checking (105).
  - Cause: the rules assume half of all failures are silent (ρ = 0.5). In this testbed, every routine failure of A is loud (a timeout), so a few loud errors make the rules expect many hidden wrong answers.
- This is the wrong-ρ weakness already seen in the 31 Oct feasibility check. Rule v5.1, which tries to learn ρ, did not fix it then.

Finding 5: in the simulator grid, v5 still beats "use B from the start".
- Seeds 2410–2412, all 64 conditions: v5 145.3 vs use_B 153.5 vs never 161.0.
- v5 wins most clearly when no degradation happens (135.6 vs 157.3).
- Monitoring therefore pays when degradation is uncertain. It does not pay when degradation is certain and severe, and a fresh tool costs only a little more.

## 3. What follows (decisions, 1 Nov 2026)
1. "Use the better tool from the start" becomes a standard baseline in every experiment. Reviewers will ask for it.
2. Core 1 is not ready for a confirmatory test. Two things come first:
   - (a) The rule must handle failures that are all loud or all silent. Learning ρ inside the joint likelihood is the planned fix; v5.1's simple version failed.
   - (b) The FreshQA design must vary how likely staleness is and the price gap. Exploratory: staleness in 100/50/25% of runs, via `stream@pNN`.
3. Findings 1–3 can already be reported as measured facts (judge quality, comparison reliability, retry failure). Findings 4–5 are development results and go into the plan, not into claims.
