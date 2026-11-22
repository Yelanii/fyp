# Pre-registration: N1, does detectability move the boundary between monitoring and buying?

**Written:** 20 November 2026, before the confirmatory run. The confirmatory run is done once, on the author's laptop.

## Why
The paper (Discussion, "Why the testbeds disagree: detectability") conjectures that the rule beat buying the
reliable tool on the simulator but lost on FreshQA because degradation on FreshQA is less detectable: the judges
separate right from wrong answers weakly (q - f about 0.25) and stale answers are never loud (rho = 0). The
conjecture was stated as untested. This test varies only those two quantities on the boundary-map design.

## Design
- **Driver:** `python run_detect.py confirm` (sets `EREPLAN_NETPV=1` and `EREPLAN_FMAX=0.95` itself).
- **Base design:** the boundary map (`run_boundary.py`): tools A (price 20), B (20 x (1 + premium)) and C (B + 6);
  tool A drops to 60% in a share of runs; same absolute wrong-answer cost and check price in every condition; fully
  repeated verdicts (pi = 1).
- **Factors:**
  - detectability (q, f): high (0.95, 0.15), mid (0.85, 0.35), low (0.80, 0.55); q - f = 0.80, 0.50, 0.25.
    "Low" matches the FreshQA judges (Phi-4 Mini q 0.81, f 0.56; Llama 3.1 8B q 0.76, f 0.52).
  - share of failures that are loud: rho in {0.5, 0}.
  - share of runs in which A degrades: 25, 50, 100%.
  - premium of B: +10, +20, +35, +50, +100%.
  - wrong-answer cost: 1x or 3x a task.
- **Strategies:** the rule as in the boundary map (`Rule_v6`, no labels) and buying B from the start (`R_fix_B`).
- **Seeds:** 9200-9219, run once (7,200 runs). Unit: the seed.
- **Metric:** per seed, the gap = (mean loss of the rule / mean loss of buying B - 1) in %, over the grid of
  degradation share x premium x wrong-answer cost, at each (detectability, rho).
- **Change from the boundary map:** the f grid of the rule's checker posterior reaches 0.95 (needed for f = 0.55);
  it is the same for every condition here, so the comparisons within this test are like for like, but the numbers are
  not directly comparable to the boundary map.

## Hypotheses (one-sided Wilcoxon signed-rank over the 20 seeds, Holm correction over the three, alpha = 0.05)
- **N1-1.** At rho = 0.5, the gap is larger (worse for the rule) at low than at high detectability.
- **N1-2.** At rho = 0, the gap is larger at low than at high detectability.
- **N1-3.** At high detectability, the gap is larger with rho = 0 than with rho = 0.5.
- **N1-4 (descriptive).** Whether the gap rises from high to mid to low at each rho.
- **Reported regardless of outcome:** the break-even premium for every (detectability, rho, degradation share), and
  the gap in every cell.

## Disclosure
The development check (`dev`, seeds 4960-4961, 720 runs) was run on the cloud machine on 19 Nov 2026 before this
file was written, to test the code. Its means were seen: the gap rose from high to low detectability at both rho
values, and rho = 0 was worse for the rule than rho = 0.5. Those two seeds are not used in the confirmatory test.

## What the outcomes would mean
- **N1-1 to N1-3 confirmed:** the boundary moves with detectability as conjectured; the paper turns the conjecture
  into a tested result for the simulator and states the size of the shift.
- **Only N1-3 confirmed:** loudness, not checker separation, moves the boundary; the paper says so.
- **None confirmed:** detectability as defined here does not explain the simulator-FreshQA difference; the paper
  withdraws the conjecture and says that other differences (for example the question streams) must explain it.

## Known limits
- Simulator only, with the checker's q and f set directly. It tests the mechanism, not FreshQA itself.
- Three detectability levels and two loudness levels.
