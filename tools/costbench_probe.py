"""Probe: build CostBench tools for one query (no LLM) and solve the cheapest route."""
import sys, json, hashlib
ROOT = sys.argv[1]
sys.path.insert(0, ROOT)
from env.domains.travel.tool_registry import tools_ready_in_memory
from env.core.base_types import create_tool_from_dict
from env.utils.solver import GroundtruthSolver

def stable_int(s): return int(hashlib.sha256(s.encode()).hexdigest(), 16) % (2**31 - 1)
q = json.load(open(f"{ROOT}/env/data/runtime/queries/queries.json"))[0]
seed = stable_int(f"42:{q['query_id']}")
d = tools_ready_in_memory(refinement_level=2, min_atomic_cost=15, max_atomic_cost=25, noise_std=0.1,
                          random_seed=seed, ban_longest_tool=True)
tools = {n: create_tool_from_dict({**t, "name": n}) for n, t in d["tools"].items()}
print("task", q["task"], "n tools", len(tools))
sample = list(d["tools"].items())[:3]
for n, t in sample: print(n, {k: t[k] for k in t if k in ("type", "cost", "component_count", "components", "input_types", "output_type")})
solver = GroundtruthSolver(tools_with_costs=tools)
res = solver.solve(q["task"]) if "task" in solver.solve.__code__.co_varnames else solver.solve(task=q["task"])
print(res)
