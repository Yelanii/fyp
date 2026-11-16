# Pre-registration: correcting the check criterion (net protection value)

**Written:** 16 November 2026, before any run on the confirmatory seeds. The run is done on the author's laptop.

## Why
A review of paper draft v0.5.2 (16 Nov 2026) found a mathematical inconsistency in the check criterion of the
proposed rule (rule v5):

- The rule checks when `PV + DV - FA >= check price`, with `PV = q (1-p)(1-rho) L`.
- `PV` counts the whole wrong-answer loss `L` as saved whenever a check catches a silent failure.
- But in rule v5 a caught failure is also resolved by a cross-check. That costs one call on the alternative tool,
  can still end in a wrong answer if the alternative is silently wrong, and needs a retry if the alternative
  fails loudly. The paper's own Table 3 includes these costs for every flag, true or false.
- The rule subtracts this resolution cost only for false alarms (the `FA` term), not for true catches.

Write `s = (1-p)(1-rho)` and `R = c_alt + (1-a)(1-rho) L + (1-a) rho (c_cur + c_check)` (the cost of resolving one
flag by a cross-check). Comparing "check and cross-check" with "do not check" for one attempt gives

    check when   q s (L - R) - p f R >= check price.

Rule v5 uses `q s L - p f R`. It omits the term `q s R`, so it over-values a check. The reviewer is correct.

The corrected rule (`Rule_v5_net`, class `CrossCheckRuleNet` in `ereplan/crosscheck.py`) uses
`PV_net = q s (L - R)`. Nothing else differs. `Rule_v5_x` is unchanged, so all saved results still replay exactly
(checked on 6 saved runs on 16 Nov).

## Development (not results)
Seeds 8000-8003, run on the cloud machine on 16 Nov with rule v5, the corrected rule and the retrying rule told
q and f: mean loss 141.0, 140.5 and 143.2. The corrected rule checked less often (0.41 against 0.46 checks per
task). This run was used only to decide that a confirmatory test is worth doing. No setting was tuned.

## Design
- Driver: `run_netpv.py`. Simulator and condition grid identical to the pre-registered rule v5 test
  (`ereplan/v5_exp.py`): tool A drops to 95, 85, 75 or 60%; q in {0.8, 0.95}; wrong-answer cost 1x or 3x a task;
  f in {0.05, 0.15}; pi in {0, 1}. 64 conditions per seed.
- Strategies: never check; the retrying rule told q and f; rule v5 told q and f; rule v5 (gross PV, no labels);
  the corrected rule (net PV, no labels).
- Seeds: **8100-8119**, run once. Metric: total loss per task. Unit of analysis: the seed.

## Hypotheses
- **H-P1 (not worse).** The corrected rule's loss is at most 1% above rule v5's: the upper bound of the 95%
  bootstrap CI of the percentage difference is <= +1%.
- **H-P2 (better).** The corrected rule has lower loss than rule v5 (one-sided paired Wilcoxon, alpha = 0.05).
- **H-P3 (still matches the labelled rule).** The corrected rule is within +3% of the retrying rule told q and f
  (upper bound of the 95% bootstrap CI <= +3%).

## What each outcome means
- **H-P1 holds:** the corrected rule becomes the proposed rule for all new experiments (D1 onwards). The paper
  states the corrected criterion, says that earlier experiments used the gross version, and reports this test as
  the measured size of the difference.
- **H-P1 fails:** the corrected criterion performs worse in practice although it is the right one-step
  comparison. The paper reports that, and the one-step derivation is then examined (for example, whether the
  over-valuation was compensating for something else, such as the value of information from extra checks).
- **H-P2 fails but H-P1 holds:** the correction is right in principle and makes no measurable difference here.
- **H-P3 fails:** the claim "matches a rule given the true rates" does not carry over to the corrected rule and
  must be re-tested before it is repeated.

## Limits
- Simulator only. The correction's effect with real checkers is tested in D1.
- The retrying rule's protection value has the same kind of omission (a caught failure costs a retry). It is a
  baseline here and is left as pre-registered; the paper will say so.
