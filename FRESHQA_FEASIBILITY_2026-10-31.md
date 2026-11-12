# FreshQA feasibility check (31 Oct 2026, exploratory, not pre-registered)

## 1. Natural degradation measured from data (no simulation)
Two FreshQA snapshots (24 Nov 2025 and 21 Apr 2026; Apache-2.0), matched by question text (ids are reassigned
between versions): 574 of 600 questions matched; 26 were reworded or new. A stale tool answering from the November
snapshot gives an answer that the April snapshot no longer accepts on:

| Question type | n | Stale answer no longer accepted |
|---|---|---|
| fast-changing | 142 | 72 (50.7%) |
| slow-changing | 211 | 10 (4.7%) |
| never-changing | 221 | 1 (0.5%; a correction, not a change) |
| all | 574 | 83 (14.5%) |

Check of the count: of the 83, 16 have very similar old/new wording; 15 are genuine updates (counts, dates, ages)
and 1 is a rewording (X Corp CEO). So about 81 of 83 are real changes. Stale answers never produce an error message.

## 2. Rules on real fault patterns (checker still simulated)
Tool A = November snapshot (price 20), B = April snapshot (24), C = premium (30). From a random call t0 in [150, 350)
tool A is wrong exactly on the questions whose answer changed, and silently so. Simulated checker q 0.95, f 0.15,
repeating (as measured for the Qwen checkers). Seeds 2300-2309, wrong answer = 3 tasks.

| Strategy | news stream (fast-changing) vs never | mixed stream vs never | wrong answers kept (news) |
|---|---|---|---|
| always check | -40.2% | -21.6% | 1.3% (but 54.7% of tasks fail) |
| CUSUM | -40.1% | -26.7% | 20.2% |
| rule v4 | -5.7% | -13.4% | 60.1% |
| check all + cross-check | -51.1% | -34.8% | 3.1% |
| rule v5 (final) | -45.3% | -35.9% | 14.6% |

## 3. What it means (interpretation)
- Natural degradation is large for fast-changing facts: about half of a 5-month-old snapshot's answers are out of date.
- Rule v4 mostly misses it. It notices degradation mainly through free loud errors and assumes half of all failures
  are loud (rho = 0.5); stale answers are never loud, so v4 rarely checks and keeps 60% wrong answers on the news stream.
  This is a real weakness that the simulated experiments could not reveal.
- Rule v5 does much better (-45% / -36%) and is best on the mixed stream, but checking everything with cross-checks is
  best on the news stream, where half the answers are wrong and checking almost always pays.
- Design implication for the main work: the share of failures that are loud must be learned, not assumed, and a small
  audit rate is needed when failures can be entirely silent. The planned "wrong rho" robustness test becomes core work.

## 4. Limits
Exploratory, 10 seeds, checker simulated (not a real LLM judge), degradation modelled as a sudden switch at t0,
5-month gap between snapshots, staleness counted by exact match of normalised answers.

## 5. First attempt to fix the silent-failure weakness (development seeds 2300-2309 only)
Rule v5.1 = rule v5 that learns the loud share rho from checked calls (ereplan/rule_v51.py).

| Variant | news vs never | mixed vs never |
|---|---|---|
| rule v5 (assumes rho = 0.5) | -45.3% | -35.9% |
| v5.1, learns rho | -39.4% | -34.7% |
| v5.1, learns rho + more audits when failures are silent | -41.2% | -35.6% |
| check all + cross-check | -51.1% | -34.8% |

Diagnosis (from traces): once the rule learns that failures are silent, it also learns that unchecked calls carry no
information, so its estimate of the tool stops moving and it stops checking. Extra audits reduce this but do not beat v5.
Decision: do NOT adopt v5.1 and do not run a confirmatory test of it. Rule v5 already handles silent staleness well
(the v4 weakness is fixed by v5's cross-check), and is best on the mixed stream. The remaining gap is on the news stream,
where half of all answers are wrong and checking everything pays; closing it needs faster switching, not a learned rho.
Next design to try in December (on development seeds first): fold rho into the joint likelihood with the other
parameters, and add an explicit value of information for the rule's own learning when failures are invisible.
