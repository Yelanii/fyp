# Pre-registration: rule v2 vs always-check (written 21 October 2026, before running seeds 400-419)

Context: in the total-loss map with leak loss = 3 tasks (seeds 200-209), always-check (B1) was the
cheapest strategy in 18 of 63 conditions, so it is the strongest remaining competitor there.

Hypothesis H-always: with leak loss = 3 task costs, decision rule v2 has lower total loss per task
than always-check (B1).

Test: same 63 conditions (7 drop levels x 3 catch rates x 3 check prices) at leak loss 3; fresh seeds
400-419; frozen settings (rule v2: window 60, epsilon 0.02, k 3, session horizon 50; B1: window 30).
Pass criteria identical to H-leak:
  (1) one-sided paired Wilcoxon (rule < B1) over all condition-seed pairs, p < 0.01;
  (2) mean relative difference at most -5%;
  (3) rule cheaper (median over seeds) in at least 2/3 of the 63 conditions;
  (4) per-seed-mean Wilcoxon p < 0.05.
Reported in addition (descriptive, not a pass criterion): where B1 still wins, by condition.
