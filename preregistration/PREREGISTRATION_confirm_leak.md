# Pre-registration: confirmatory test (written 21 October 2026, before running seeds 300-319)

Exploratory finding (check-worth map, seeds 200-209): on total loss per task, decision rule v2 was
cheaper than the CUSUM change alarm when a wrong answer costs 3 tasks (mean -8.5%), but not when it
costs 1 task (mean -0.7%).

Hypothesis H-leak: with leak loss = 3 task costs, decision rule v2 has lower total loss per task than
CUSUM (B4).

Test: same 63 conditions as the map at leak loss 3 (7 drop levels x 3 catch rates x 3 check prices);
fresh seeds 300-319 (never used before); the same frozen settings (rule v2: window 60, epsilon 0.02,
k 3, session horizon 50; CUSUM: h 6, p1 0.8; neither re-tuned).
Pass if ALL hold:
  (1) one-sided paired Wilcoxon (rule < CUSUM) over all condition-seed pairs, p < 0.01;
  (2) mean relative difference at most -5%;
  (3) the rule is cheaper (median over seeds) in at least 2/3 of the 63 conditions.
Because pairs share seeds across conditions, a second check repeats (1) on per-seed means
(20 pairs), and must also give p < 0.05.
