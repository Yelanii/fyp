# Pre-registration: the boundary between monitoring and buying the better tool

**Written:** 10 November 2026, before any run of this design.

## Why
FreshQA showed that buying the better tool beats the rule when the cheap tool is certain or likely to degrade and
the better tool costs 20-50% more. The PP slides promised to report "the point at which the proposed approach stops
outperforming the comparator". This test maps that point on the simulator.

## Design
- Tool A (price 20) drops to 60% in a share P of runs, P in {0, 25, 50, 75, 100}% (`pdrop_0.60@pNN`).
- Tool B never degrades and costs 10, 20, 35, 50 or 100% more than A (22, 24, 27, 30, 40); C costs B + 6.
- The wrong-answer cost and the check price are held at their standard absolute values while B's price changes
  (otherwise they would rise with the mean tool price). Wrong-answer cost {1, 3} tasks. q 0.95, f 0.15, pi 1.
- 50 conditions per seed. Strategies: v6 (the proposed rule), fixed tool B ("buy the better tool"), never check.
- Seeds: smoke test 4950-4951. Test: **5100-5119**, run once. Unit: the seed; one-sided Wilcoxon.

## Hypotheses (regions fixed in advance, from the FreshQA pattern)
- **H-B1 (monitoring region):** where B costs at least 50% more and A degrades in at most 50% of runs
  (2 x 3 x 2 = 12 cells), v6 has lower total loss than fixed tool B.
- **H-B2 (buying region):** where B costs at most 20% more and A degrades in at least 75% of runs (8 cells), fixed
  tool B has lower total loss than v6.
Holm over the two.

Descriptive: the full 5 x 5 map of (v6 - fixed B) / fixed B, and for each P the break-even price premium found by
linear interpolation.

## Reading the outcomes
Both confirmed: the claim has a measured boundary in both directions. H-B1 not confirmed: buying the better tool is
at least as good even where monitoring should be strongest; the rule's claim shrinks further. H-B2 not confirmed:
the FreshQA pattern does not show on the simulator, and the two testbeds disagree; reported as such.

## Outcome (added after the run, 10 November 2026; results/boundary_confirm_20261110-214056)
| Hypothesis | Result | Verdict |
|---|---|---|
| H-B1 monitoring region: v6 < fixed B | 152.6 vs 209.9 (-27.3%), p = 9.5e-07, 20 seeds | CONFIRMED |
| H-B2 buying region: fixed B < v6 | 148.3 vs 150.0 (-1.2%), p = 0.077 | **NOT CONFIRMED** |

Map of (rule - fixed B) / fixed B:

| A degrades in | B +10% | B +20% | B +35% | B +50% | B +100% | break-even premium |
|---|---|---|---|---|---|---|
| 0% of runs | -6.1% | -12.5% | -20.2% | -26.8% | -43.1% | rule always cheaper |
| 25% | -1.1% | -6.2% | -12.9% | -18.2% | -31.3% | rule always cheaper |
| 50% | +1.1% | -3.6% | -8.8% | -14.0% | -25.4% | about +12% |
| 75% | +2.9% | -1.4% | -5.4% | -9.2% | -18.9% | about +17% |
| 100% | +3.3% | +0.2% | -2.7% | -6.7% | -15.7% | about +21% |

Reading: on the simulator, buying the better tool wins only when it costs at most about 12-21% more and the cheap
tool is likely to degrade, and then only by 1-3%. **The simulator and FreshQA disagree in strength:** on FreshQA the
rule lost by 7-24% at premiums of 20% and 50% when staleness was certain or likely. A probable reason, not tested:
on FreshQA the judges cannot detect staleness (q - f at most 0.06) and stale answers are never loud, whereas the
simulator's checker has q = 0.95 and half of failures are loud. The boundary therefore depends on how detectable
the degradation is, and the simulator's boundary should not be quoted as if it held for FreshQA.
