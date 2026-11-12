# Pre-registration: false reassurance and the self-calibrating rule (written 21 October 2026, before running seeds 900-919)

Development so far: exploratory runs on seeds 700-711; rule v3 developed and its one setting
(q_prior_strength = 3, chosen from {3, 6, 12}) picked on dev seeds 800-805. Nothing below has been run on seeds 900-919.

Environment: synthetic, three tools; the cheap tool drops from 95% to {85%, 80%, 75%, 60%} at a random call;
true and assumed catch rate q = 0.8; check-failure correlation corr in {0, 0.9}: once the tool has degraded,
its silent failures are caught with q x (1 - corr). Check price {15%, 30%}; leak loss {1, 3} task costs.
32 conditions x 20 seeds (900-919). Metric: total loss per task.
Strategies (frozen settings): never check (B2, window 30), always check (B1, window 30), CUSUM (h 6, p1 0.8),
rule v2 (window 60, epsilon 0.02, k 3, session horizon 50), rule v3 (= v2 + joint (p, q) estimate, q prior strength 3).

H-FR (false reassurance exists): at corr = 0.9, always-check has HIGHER mean total loss than never-check
  in at least 2/3 of the 16 conditions, and a one-sided paired Wilcoxon over condition-seed pairs gives p < 0.01.
H-SC (self-calibration helps): at corr = 0.9, rule v3 has lower total loss than rule v2: mean relative
  difference <= -2% and one-sided paired Wilcoxon p < 0.01.
H-NI (no harm when checks are fine): at corr = 0, rule v3's mean total loss is at most 1% above rule v2's.
Each hypothesis is judged separately; all three results will be reported whatever they are.
