# Independent replay of part E3 (cloud machine, 25 October 2026, 01:44 Colombo time)

**Inputs** (copied from the student's laptop):
- `report.md` and `rows.json` from this folder;
- `llm_cache_qwen2.5_1.5b.json` (3,675 answers; a superset of the 1,891 cloud answers, with no value changed);
- `llm_cache_qwen2.5_3b.json` (2,949 answers).

**Code:** SHA-256 of `cat ereplan/*.py` begins `07ccb744629cbcd6`, the fingerprint pre-registered for E3.

**Command:** `EREPLAN_REPLAY=1 python -m ereplan.realagent persist --model qwen2.5:1.5b --seeds 10 --seed-start 4000`.
In replay mode no model is called, and every answer comes from the caches.

**Reconstructed inputs** (stated limit):
- `judge_calibration_qwen2.5_1.5b__judge_qwen2.5_3b.json` and the two part D files `repeat_qwen2.5_*_*.json` were
  not copied from the laptop.
- They were rebuilt from the `setup` block of `rows.json`, which records the exact f and q the laptop run used.
- E3 uses no other field from these files.

**Result:**
- report identical;
- 0 cache misses;
- all 640 rows identical in every field (exact floating-point equality).

**Also replayed with the full laptop cache:** Run 3 (`run --seeds 10 --seed-start 3000`) now matches the laptop
exactly: v4 73.8, CUSUM 81.0, never 82.0, v3 86.4, v2 95.2, always 108.9, with 0 misses. The earlier cloud replay
gave CUSUM 80.4 only because 53 answers were missing from the old cloud cache.

**Not yet replayed:** the part D run with the 3B checker. Its report needs fields (for example
`catch_rate_subtle`) that exist only in the original 3B calibration file.
