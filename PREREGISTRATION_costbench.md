# Pre-registration: CostBench-derived evaluation (written 21 October 2026, before running seeds 500-511)

Environment: real CostBench test queries (commit 6424069, refinement level 2, CostBench's own
per-query seeds and cost generator, no LLM). For each query: the cheapest route, and the cheapest
route that avoids the task type's most-used tool X (from CostBench's own Dijkstra solver).
194 of 381 queries have X on their cheapest route and are used.

Observation made before this test (descriptive): on CostBench's own prices, avoiding X costs only
0.0-0.53% more (median 0.1%). A price-gap factor therefore makes the route WITH X cheaper by
g in {native, 10%, 20%} (X's price lowered; everything else unchanged).

Run: 120 tasks sampled (with replacement, seeded) from one task type; the type rotates with the seed.
X's success rate drops from 95% to {95% (no drop), 85%, 75%, 60%} at a random task in [30, 70);
all other tools stay at 95%. A route is chosen at the start of each task; checks are chosen per step.
Strategies and settings are frozen from the synthetic study (no re-tuning): never/always/fixed-rate
check (B1-B3, price-only switch line), CUSUM (h 6, p1 0.8), rule v2 (window 60, epsilon 0.02,
k 3, leak-aware line, horizon 10 tasks), oracle. The perfect-knowledge optimum is computed exactly per
task (route + check pattern).
Grid: drop (4) x q {0.5, 0.95} x check price {5%, 30%} x leak loss {1, 3} x price gap (3) = 96
conditions; seeds 500-511 (12 seeds, 2 per task type).

Hypothesis H-cb (replicates the synthetic finding): at each leak level (1 and 3), rule v2 has the
lowest median excess total loss over the optimum among non-oracle strategies, and that median is at
most 5%.
Reported regardless of outcome: results separately for the native price gap.
