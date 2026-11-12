"""Build route data from CostBench (no LLM): for every test query, the cheapest route, and the cheapest
route that avoids one chosen tool X. Output: data/processed/costbench_routes.json

Usage: python -I tools/costbench_routes.py <path to CostBench clone> [refinement_level]
"""
import sys, json, hashlib, subprocess, collections, os, io, contextlib
ROOT = sys.argv[1]
LEVEL = int(sys.argv[2]) if len(sys.argv) > 2 else 2
sys.path.insert(0, ROOT)
from env.domains.travel.tool_registry import tools_ready_in_memory
from env.core.base_types import create_tool_from_dict
from env.utils.solver import GroundtruthSolver

def stable_int(s): return int(hashlib.sha256(s.encode()).hexdigest(), 16) % (2**31 - 1)

def build(q):
    seed = stable_int(f"42:{q['query_id']}")          # same per-query seed rule as CostBench run.py
    d = tools_ready_in_memory(refinement_level=LEVEL, min_atomic_cost=15, max_atomic_cost=25,
                              noise_std=0.1, random_seed=seed, ban_longest_tool=True)
    return {n: create_tool_from_dict({**t, "name": n}) for n, t in d["tools"].items()}, d["tools"]

def solve(tools, task):
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            return GroundtruthSolver(tools_with_costs=tools).solve(task)
        except Exception:
            return None

queries = json.load(open(f"{ROOT}/env/data/runtime/queries/queries.json"))
first = []
for q in queries:
    tools, raw = build(q)
    r = solve(tools, q["task"])
    first.append((q, tools, raw, r))
freq = collections.Counter(t for _, _, _, r in first if r for t in r.tools)
print("most frequent tools in cheapest routes:", freq.most_common(8), file=sys.stderr)
by_task = collections.defaultdict(collections.Counter)
for q, _, _, r in first:
    if r:
        for t in r.tools: by_task[q["task"]][t] += 1
out = {"costbench_commit": subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
       "refinement_level": LEVEL, "queries": []}
for q, tools, raw, r in first:
    if not r:
        continue
    X = by_task[q["task"]].most_common(1)[0][0]          # the most-used tool for this task type
    if X not in r.tools:
        continue
    alt = solve({n: t for n, t in tools.items() if n != X}, q["task"])
    if not alt:
        continue
    out["queries"].append(dict(query_id=q["query_id"], task=q["task"], X=X,
        with_X=[[t, raw[t]["cost"]] for t in r.tools], without_X=[[t, raw[t]["cost"]] for t in alt.tools]))
os.makedirs("data/processed", exist_ok=True)
json.dump(out, open("data/processed/costbench_routes.json", "w"), indent=1)
print(f"kept {len(out['queries'])} of {len(queries)} queries", file=sys.stderr)
print(json.dumps(collections.Counter((x['task'], x['X']) for x in out['queries']).most_common(), indent=0), file=sys.stderr)
