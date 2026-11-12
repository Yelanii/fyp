"""CostBench-derived evaluation (PREREGISTRATION_costbench.md).

Tasks and prices come from real CostBench test queries (data/processed/costbench_routes.json, built by
tools/costbench_routes.py from CostBench's own generator and Dijkstra solver; no LLM). Each task has two
routes: the cheapest route (uses tool X) and the cheapest route avoiding X. X may degrade silently.
At the start of each task a strategy picks a route; at each step it decides whether to check.

Usage: python -m ereplan.costbench_exp [--quick]
"""
import argparse, itertools, json, math, os, time, zlib
from multiprocessing import Pool
import numpy as np
from scipy.stats import binom

from .config import Setting
from .estimator import RangeEstimator, GRID

ROUTES = "data/processed/costbench_routes.json"
TYPES = ("accommodation", "attraction", "dining", "location", "shopping", "transportation")
N_TASKS, P_OK, RHO, R_MAX = 120, 0.95, 0.5, 2
DROPS, QS, PRICES, LEAKS, GAPS = (0.95, 0.85, 0.75, 0.60), (0.5, 0.95), (0.05, 0.30), (1.0, 3.0), (0.0, 0.10, 0.20)
SEEDS = tuple(range(500, 512))
STRATS = ("Never check (B2)", "Always check (B1)", "Fixed-rate check (B3)", "Change alarm, CUSUM (B4)",
          "Decision rule v2", "Oracle (knows truth)")


def _rng(*parts):
    return np.random.default_rng(zlib.crc32("|".join(map(str, parts)).encode()))


# --------------------------------------------------------------------------- world
class World:
    def __init__(self, data, drop, q, check_frac, leak_mult, gap, seed):
        ttype = TYPES[seed % len(TYPES)]
        qs = [x for x in data["queries"] if x["task"] == ttype]
        r = _rng("cb_world", seed)
        picks = r.integers(0, len(qs), N_TASKS)
        self.tasks = []
        for i in picks:
            x = qs[i]
            w = [[n, float(c)] for n, c in x["with_X"]]
            wo = [[n, float(c)] for n, c in x["without_X"]]
            if gap > 0:  # make the route with X cheaper by `gap` (lower X's price only)
                cw, cwo = sum(c for _, c in w), sum(c for _, c in wo)
                xp = next(c for n, c in w if n == x["X"])
                new = max(cwo / (1 + gap) - (cw - xp), 1.0)
                w = [[n, new if n == x["X"] else c] for n, c in w]
            self.tasks.append(dict(X=x["X"], routes=(w, wo)))
        t0 = int(r.integers(30, 70))
        self.pX = np.where(np.arange(N_TASKS) >= t0, drop, P_OK)
        self.t0 = t0
        self.q, self.drop = q, drop
        mean_route = np.mean([sum(c for _, c in t["routes"][0]) for t in self.tasks])
        mean_tool = np.mean([c for t in self.tasks for _, c in t["routes"][0]])
        self.L = leak_mult * mean_route
        self.check_price = check_frac * mean_tool
        ro = _rng("cb_outcomes", seed)
        self.U = ro.random((N_TASKS, 2, 12, R_MAX + 1, 3))   # task, route, step, attempt, (success, loud, catch)

    def p_of(self, i, name):
        return float(self.pX[i]) if name == self.tasks[i]["X"] else P_OK


# --------------------------------------------------------------------------- shared maths
def route_loss(steps, X, pX, L, leak_aware):
    tot = 0.0
    for n, c in steps:
        p = max(pX if n == X else P_OK, 1e-6)
        tot += c / p + ((1 - p) * (1 - RHO) * L if leak_aware else 0.0)
    return tot


def line_for(task, L, leak_aware):
    """Success rate of X at which both routes have equal expected cost (bisection)."""
    w, wo = task["routes"]
    target = route_loss(wo, task["X"], P_OK, L, leak_aware)
    f = lambda p: route_loss(w, task["X"], p, L, leak_aware)
    if f(1.0) >= target:
        return 1.0
    lo, hi = 1e-3, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > target else (lo, mid)
    return hi


def step_stats(p, price, check_price, checked, q):
    d = RHO + (1 - RHO) * q if checked else RHO
    f = (1 - p) * d
    e_att = sum((k + 1) * f**k * (1 - f) for k in range(R_MAX + 1)) + (R_MAX + 1) * f**(R_MAX + 1)
    return (price + (check_price if checked else 0)) * e_att, (1 - p) * (1 - d) * sum(f**k for k in range(R_MAX + 1)), f**(R_MAX + 1)


def best_task_plan(world, i):
    """Exact optimum for task i given the true success rates: (expected loss, route, check pattern)."""
    best = (math.inf, None, None)
    for ri, steps in enumerate(world.tasks[i]["routes"]):
        for pat in itertools.product((False, True), repeat=len(steps)):
            a0 = 1.0; a1 = spend = leak = 0.0
            for (n, c), chk in zip(steps, pat):
                e, pl, px = step_stats(world.p_of(i, n), c, world.check_price, chk, world.q)
                spend += (a0 + a1) * e; leak += a0 * pl
                a0, a1 = a0 * (1 - pl - px), a1 * (1 - px) + a0 * pl
            v = spend + world.L * leak
            if v < best[0]:
                best = (v, ri, pat)
    return best


# --------------------------------------------------------------------------- strategies
class Base:
    window, leak_aware = 30, False

    def __init__(self, world, seed):
        self.w, self.rng = world, _rng("cb_strategy", type(self).__name__, seed)
        self.est = RangeEstimator(self.window, RHO, world.q, P_OK, 20.0)

    def route(self, i):
        line = line_for(self.w.tasks[i], self.w.L, self.leak_aware)
        return 1 if self.est.summary()[2] < line else 0

    def check(self, i, step, name, isX):
        return False

    def observe(self, isX, checked, seen):
        if isX:
            self.est.update(checked, seen)


class Never(Base):
    pass


class Always(Base):
    def check(self, *a):
        return True


class Fixed(Base):
    def check(self, *a):
        return self.rng.random() < 0.2


class Cusum(Base):
    h, p1, audit = 6.0, 0.8, 0.05

    def __init__(self, world, seed):
        super().__init__(world, seed)
        self.S, self.avoid = 0.0, False

    def route(self, i):
        return 1 if self.avoid else 0

    def check(self, i, step, name, isX):
        return (isX and self.S > self.h / 2) or self.rng.random() < self.audit

    def observe(self, isX, checked, seen):
        if not isX or self.avoid:
            return
        d = RHO + (1 - RHO) * self.w.q if checked else RHO
        f0, f1 = (1 - P_OK) * d, (1 - self.p1) * d
        self.S = max(0.0, self.S + (math.log(f1 / f0) if seen else math.log((1 - f1) / (1 - f0))))
        if self.S > self.h:
            self.avoid = True


class RuleV2(Base):
    window, leak_aware, epsilon, k, horizon = 60, True, 0.02, 3, 10

    def _pv(self, p):
        return self.w.q * (1 - p) * (1 - RHO) * self.w.L

    def _dv(self, i, line):
        t = self.w.tasks[i]
        post = self.est.posterior()
        d_c = self.est.d_c
        pf = (1 - GRID) * d_c
        pmf = np.stack([binom.pmf(j, self.k, pf) for j in range(self.k + 1)])
        joint = pmf * post
        pj = joint.sum(1)
        means = (joint * GRID).sum(1) / np.maximum(pj, 1e-300)
        sw = self.horizon * route_loss(t["routes"][1], t["X"], P_OK, self.w.L, True)
        stay = lambda p: self.horizon * route_loss(t["routes"][0], t["X"], p, self.w.L, True)
        d0_stay = stay(float((post * GRID).sum())) <= sw
        sav = sum(pj[j] * ((stay(means[j]) if d0_stay else sw) - min(stay(means[j]), sw)) for j in range(self.k + 1))
        return sav / self.k

    def check(self, i, step, name, isX):
        if not isX:
            return self._pv(P_OK) >= self.w.check_price
        audit = self.rng.random() < self.epsilon
        mean, low, high = self.est.summary()
        line = line_for(self.w.tasks[i], self.w.L, True)
        value = self._pv(mean) + (self._dv(i, line) if low <= line <= high else 0.0)
        return value >= self.w.check_price or audit


class Oracle(Base):
    def route(self, i):
        self.plan = best_task_plan(self.w, i)
        return self.plan[1]

    def check(self, i, step, name, isX):
        return self.plan[2][step]


CLASSES = dict(zip(STRATS, (Never, Always, Fixed, Cusum, RuleV2, Oracle)))


# --------------------------------------------------------------------------- simulation
def simulate(world, strat):
    spend = 0.0
    leaks = checks = avoided = 0
    for i, task in enumerate(world.tasks):
        ri = strat.route(i)
        avoided += ri
        leaked = False
        for s, (name, price) in enumerate(task["routes"][ri]):
            isX = name == task["X"]
            p = world.p_of(i, name)
            chk = bool(strat.check(i, s, name, isX))
            done = False
            for a in range(R_MAX + 1):
                u = world.U[i, ri, s, a]
                spend += price + (world.check_price if chk else 0.0)
                checks += chk
                if u[0] < p:
                    strat.observe(isX, chk, False); done = True; break
                if u[1] < RHO or (chk and u[2] < world.q):
                    strat.observe(isX, chk, True); continue
                strat.observe(isX, chk, False); leaked = True; done = True; break
            if not done:
                break
        leaks += leaked
    return dict(total_loss=(spend + world.L * leaks) / N_TASKS, leak_rate=leaks / N_TASKS,
                checks_per_task=checks / N_TASKS, share_avoiding_X=avoided / N_TASKS)


def _job(key):
    drop, q, cf, lm, gap, seed = key
    data = json.load(open(ROUTES))
    world = World(data, drop, q, cf, lm, gap, seed)
    opt = sum(best_task_plan(world, i)[0] for i in range(N_TASKS)) / N_TASKS
    out = []
    for name in STRATS:
        r = simulate(world, CLASSES[name](world, seed))
        out.append(dict(strategy=name, drop=drop, q=q, check_frac=cf, leak_mult=lm, gap=gap, seed=seed,
                        optimum=opt, **r))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args(argv)
    seeds = SEEDS[:6] if a.quick else SEEDS
    keys = list(itertools.product(DROPS, QS, PRICES, LEAKS, GAPS, seeds))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = [r for rs in pool.map(_job, keys, chunksize=4) for r in rs]
    out = os.path.join("results", f"costbench_{time.strftime('%Y%m%d-%H%M%S')}{'_quick' if a.quick else ''}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    report(rows, out, time.time() - t0, seeds)


def report(rows, out, wall, seeds):
    conds = sorted({(r["drop"], r["q"], r["check_frac"], r["leak_mult"], r["gap"]) for r in rows})
    agg = {}
    for c in conds:
        rs = [r for r in rows if (r["drop"], r["q"], r["check_frac"], r["leak_mult"], r["gap"]) == c]
        opt = np.mean([r["optimum"] for r in rs if r["strategy"] == STRATS[0]])
        for st in STRATS:
            m = np.mean([r["total_loss"] for r in rs if r["strategy"] == st])
            agg.setdefault(st, []).append(dict(c=c, excess=m / opt - 1))
    L = ["# CostBench-derived evaluation", "",
         f"Seeds {seeds[0]}-{seeds[-1]}; {len(conds)} conditions; wall time {wall:.0f} s; routes from {ROUTES}.", ""]
    verdict = {}
    for lm in LEAKS:
        L += [f"## Leak loss = {lm:g}: median extra loss over the perfect-knowledge optimum", "",
              "| Strategy | All price gaps | Native CostBench prices | Gap 10% | Gap 20% |", "|---|---|---|---|---|"]
        meds = {}
        for st in STRATS:
            cells = [x for x in agg[st] if x["c"][3] == lm]
            by = lambda g: np.median([x["excess"] for x in cells if x["c"][4] == g]) * 100
            meds[st] = np.median([x["excess"] for x in cells]) * 100
            L.append(f"| {st} | {meds[st]:+.1f}% | {by(0.0):+.1f}% | {by(0.10):+.1f}% | {by(0.20):+.1f}% |")
        nonor = {k: v for k, v in meds.items() if not k.startswith("Oracle")}
        best = min(nonor, key=nonor.get)
        verdict[lm] = (best == "Decision rule v2") and (meds["Decision rule v2"] <= 5.0)
        L += ["", f"Lowest non-oracle: {best}. H-cb part for leak {lm:g}: {'met' if verdict[lm] else 'not met'}.", ""]
    L.append(f"**H-cb: {'CONFIRMED' if all(verdict.values()) else 'NOT CONFIRMED'}**")
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L))
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
