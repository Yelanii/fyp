# Pre-registration: re-running the confirmatory experiments with the corrected rule

**Written:** 16 November 2026, before any run on the seeds below. The runs are done on the author's laptop.

## Why
A review of paper draft v0.5.3 (16 Nov 2026, methodological soundness 5.0/10) stated: "The central decision rule
has a known mathematical omission in the experiments supporting the main performance claims. The corrected rule
must be evaluated before those claims can be considered established."

The omission is described in `PREREGISTRATION_netpv.md`: the rule's check criterion counted the whole
wrong-answer loss as saved by a catch and did not subtract the cost of resolving the caught failure by a
cross-check. `run_netpv.py` measures the direct difference between the evaluated rule and the corrected rule on
one design. That is not enough: every claim about the proposed rule rests on experiments run with the uncorrected
criterion. This suite repeats those experiments with the corrected rule.

## What changes and what does not
- **Changed:** the environment variable `EREPLAN_NETPV=1` switches every cross-checking rule (`Rule_v5_x` and
  the rules built on it: told, learning rho, third source, re-test, and the CostBench version) to the corrected
  criterion `q s (L - R) + DV - p f R >= check price`.
- **Changed:** the seeds (table below). None has been used before.
- **Not changed:** designs, conditions, baselines, tuned baseline settings, metrics, hypotheses, margins,
  statistical tests and report code. Each experiment uses its original pre-registration file. Baselines that do
  not cross-check (never, always, CUSUM, the retrying rules, the published-method adaptations, fixed tools) are
  not affected by the switch.
- Without the variable, all earlier saved results still replay exactly (checked on 16 Nov for the simulator and
  CostBench).

## Experiments and seeds
| Name | Original pre-registration | Original seeds | New seeds |
|---|---|---|---|
| sim | PREREGISTRATION_v5.md (label-free rule, simulator) | 1700-1719 | 8200-8219 |
| stress | PREREGISTRATION_v5.md, part C (unreliable comparisons) | 1720-1729 | 8220-8229 |
| bayes | PREREGISTRATION_v5.md, Bayes-optimal comparison | 1820-1839 | 8240-8259 |
| core2 | PREREGISTRATION_core2.md (published methods) | 2410-2429 | 8300-8319 |
| cb15 | PREREGISTRATION_costbench_v5.md | 2000-2017 | 8340-8357 |
| cb5 | PREREGISTRATION_costbench_v5_part2.md | 2200-2217 | 8360-8377 |
| fr11 | PREREGISTRATION_fr11_realcheckers.md | 2800-2817 | 8400-8417 |
| robust | PREREGISTRATION_robustness.md | 6100-6119 | 8500-8519 |
| freshqa | PREREGISTRATION_freshqa.md | 2700-2719 | 8600-8619 |
| anytool | PREREGISTRATION_anytool.md | 5200-5219 | 8700-8719 |
| boundary | PREREGISTRATION_boundary.md | 5100-5119 | 8800-8819 |
| ablation | PREREGISTRATION_ablation_v51.md | 1800-1819 | 8900-8919 |
| rho | PREREGISTRATION_rho.md | 1900-1919 | 9000-9019 |

Driver: `python run_corrected_suite.py all`. Each seed set is run once.

Not in this suite: the two GSM8K real-agent experiments (seeds 4000-4009 and 4100-4109). The first does not
involve the cross-checking rule. The second needs new live model calls and is repeated inside D1.

## Smoke test (not results)
Each experiment was started once with a single throwaway seed (9900-9949, and 9990 for boundary) on the cloud machine on 16 Nov, only to
check that the suite runs. No number from those runs is used.

## How the results will be used
1. **The paper's main results become the corrected-rule results** from this suite. The earlier results are kept in
   the repository and reported in the paper as the uncorrected version, in a short comparison table.
2. For every hypothesis, the paper reports the outcome with the corrected rule, whether or not it agrees with the
   earlier outcome. A hypothesis that was confirmed before and is not confirmed now is reported as not
   confirmed.
3. No hypothesis, margin or condition is changed after seeing these results.

## What different outcomes would mean
- **Outcomes agree with the earlier ones:** the omission did not drive the conclusions; the claims stand, now on
  the corrected rule.
- **Some outcomes change:** the affected claims are rewritten to match, and the paper says which.
- **The corrected rule is worse overall:** this is reported; the cause is then investigated in development on
  separate seeds (for example, whether extra checks had information value that the one-step criterion ignores).

## Limits
- All of these are simulator, CostBench-route or cached-verdict experiments. Real-tool evidence comes from D1.
- The retrying rules' protection value has the same kind of omission (a caught failure costs a retry). They are
  baselines and are left as pre-registered; the paper says so.
