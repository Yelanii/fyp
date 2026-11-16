"""Rules v4 and v5 on CostBench-derived tasks (28 October 2026). See PREREGISTRATION_costbench_v5.md.

The first CostBench evaluation (costbench_exp.py, 21 Oct) tested rule v2 with a perfect checker. This one adds what
the later rules were built for: a checker that sometimes flags a CORRECT result (false alarm, rate f), which may
repeat its verdict on a retry (persistence pi), and the cross-check that rule v5 uses to resolve a flag.

Tasks and prices: real CostBench test queries (data/processed/costbench_routes.json, built by
tools/costbench_routes.py from CostBench's own generator and solver). Per task: the cheapest route (uses tool X) and
the cheapest route avoiding X. X's success rate drops silently at a random task; every other tool stays at 95%.

Cross-check (rule v5 and B12): a flagged step is re-done by an alternative and the two outputs are compared.
  - flagged step on X: the alternative is CostBench's own route around X, priced at
        c_X + (cost of the route without X - cost of the route with X),
    i.e. what doing X's job another way costs on CostBench's prices;
  - flagged step on another tool: a second provider of the same tool at the same price (an assumption: CostBench
    does not list duplicate providers).
  The alternative succeeds with 95%; its failures are loud with share rho, otherwise silently wrong. Two wrong
  outputs are assumed never to agree (as in the main v5 test).

Usage:  python -m ereplan.costbench_v5 dev       # smoke test, seeds 1990-1991 (no tuning; not a test)
        python -m ereplan.costbench_v5 confirm   # pre-registered test, seeds 2000-2017
        python -m ereplan.costbench_v5 cheap     # part 2: checks cost 5% of a tool call, seeds 2200-2217
"""
import argparse, itertools, json, os, time
from multiprocessing import Pool
import numpy as np
from scipy.stats import binom, wilcoxon

from .costbench_exp import (ROUTES, N_TASKS, P_OK, RHO, R_MAX, World, _rng, route_loss, line_for,
                            Never, Always, Cusum, RuleV2)
from .fa_rule import JointEstimatorFA
from .crosscheck import CheckerMemory, JointEstimatorV5, FLAG_KINDS, NETPV
from .selfcal import PG, QG

CHECK_FRAC = 0.15
DROPS, QS, FS, PIS, LEAKS, GAPS = (0.95, 0.85, 0.75, 0.60), (0.8, 0.95), (0.05, 0.15), (0.0, 1.0), (1.0, 3.0), (0.0, 0.20)
TEST_SEEDS, DEV_SEEDS = tuple(range(2000, 2018)), (1990, 1991)
CHEAP_FRAC, CHEAP_GAPS, CHEAP_SEEDS = 0.05, (0.0, 0.20), tuple(range(2200, 2218))   # part 2, PREREGISTRATION_costbench_v5_part2.md


# --------------------------------------------------------------------------- world
class WorldFA(World):
    def __init__(self, data, drop, q, f, pi, lm, gap, seed, check_frac=None):
        super().__init__(data, drop, q, CHECK_FRAC if check_frac is None else check_frac, lm, gap, seed)
        self.f, self.pi = f, pi
        A = R_MAX + 1
        u = _rng("cb_fa", seed).random((N_TASKS, 2, 12, A))
        if 0.0 < pi < 1.0:                       # a retry repeats the previous verdict with probability pi
            up = _rng("cb_fapersist", seed).random((N_TASKS, 2, 12, A))
            for a in range(1, A):
                u[..., a] = np.where(up[..., a] < pi, u[..., a - 1], u[..., a])
        elif pi >= 1.0:
            u[...] = u[..., :1]
        self.UFA = u
        self.UALT = _rng("cb_alt", seed).random((N_TASKS, 2, 12, A, 2))   # alternative: (success, loud)
        self.alt_X = []
        for t in self.tasks:
            w, wo = t["routes"]
            cx = next(c for n, c in w if n == t["X"])
            self.alt_X.append(cx + max(0.0, sum(c for _, c in wo) - sum(c for _, c in w)))

    def alt_price(self, i, name, price):
        return self.alt_X[i] if name == self.tasks[i]["X"] else price


# --------------------------------------------------------------------------- rules v4 and v5 on CostBench
class _Joint:
    """Shared parts of v4 and v5: route choice and the decision value from a joint (p, q) posterior over X."""
    window, epsilon, k, horizon = 60, 0.02, 3, 10
    crosscheck = False

    def __init__(self, world, seed):
        self.w, self.rng = world, _rng("cb_strategy", self.rng_name, seed)

    def route(self, i):
        _, _, high = self.est.summary()
        return 1 if high < line_for(self.w.tasks[i], self.w.L, True) else 0

    def _dv(self, i, f):
        t = self.w.tasks[i]
        w = self.est.joint()
        seen = (1 - PG) * (RHO + (1 - RHO) * QG) + PG * f          # P(failure seen | checked)
        sw = self.horizon * route_loss(t["routes"][1], t["X"], P_OK, self.w.L, True)
        stay = lambda p: self.horizon * route_loss(t["routes"][0], t["X"], p, self.w.L, True)
        pbar = float((w.sum(axis=1) * PG[:, 0]).sum())
        d0_stay = stay(pbar) <= sw
        sav = 0.0
        for j in range(self.k + 1):
            lj = w * binom.pmf(j, self.k, seen)
            pj = lj.sum()
            if pj <= 0:
                continue
            mj = float((lj.sum(axis=1) * PG[:, 0]).sum() / pj)
            sav += pj * ((stay(mj) if d0_stay else sw) - min(stay(mj), sw))
        return sav / self.k

    def check(self, i, step, name, isX, ri, price):
        cp, L = self.w.check_price, self.w.L
        if isX:
            mean, low, high = self.est.summary()
            q = self.est.q_hat
            line = line_for(self.w.tasks[i], L, True)
            dv = self._dv(i, self.f_now()) if low <= line <= high else 0.0
            audit = self.rng.random() < self.epsilon
        else:
            mean, q, dv, audit = P_OK, self.q_other(), 0.0, False
        pv = q * (1 - mean) * (1 - RHO) * L
        fa = self.fa_cost(i, ri, name, price, mean)
        pv -= self.catch_cost(i, ri, name, price, mean, q)     # 0 unless the corrected (net) criterion is on
        return (pv + dv - fa) >= cp or audit

    def catch_cost(self, i, ri, name, price, mean, q):
        return 0.0


class RuleV4CB(_Joint):
    """Rule v4: told q and f (labelled calibration); a flagged step is retried."""
    rng_name = "v4"

    def __init__(self, world, seed, q_told=None, f_told=None):
        super().__init__(world, seed)
        self.q = world.q if q_told is None else q_told
        self.f = world.f if f_told is None else f_told
        self.est = JointEstimatorFA(self.window, RHO, self.q, 3.0, P_OK, 20.0, f=self.f)

    def f_now(self):
        return self.f

    def q_other(self):
        return self.q

    def fa_cost(self, i, ri, name, price, mean):
        task_cost = sum(c for _, c in self.w.tasks[i]["routes"][ri])
        return mean * self.f * (task_cost + R_MAX * (price + self.w.check_price))

    def observe(self, i, name, isX, checked, kind):
        if isX:
            self.est.update(checked, "caught" if kind in FLAG_KINDS else kind)


class RuleV4NoCal(RuleV4CB):
    """Rule v4 without labelled calibration: assumes f = 0 and q prior mean 0.5 (as in the v5 study)."""
    def __init__(self, world, seed):
        super().__init__(world, seed, q_told=0.5, f_told=0.0)


class RuleV5CB(_Joint):
    """Rule v5: learns (q, f) without labels; a flagged step is cross-checked on the alternative."""
    rng_name = "v5"
    crosscheck = True
    told = False

    def __init__(self, world, seed):
        super().__init__(world, seed)
        self.cm = CheckerMemory(RHO, fixed=(world.q, world.f) if self.told else None)
        self.est = JointEstimatorV5(self.window, RHO, P_OK, 20.0, self.cm)

    def f_now(self):
        return self.cm.f_mean

    def q_other(self):
        return self.cm.q_mean

    def fa_cost(self, i, ri, name, price, mean):
        a = P_OK
        alt = self.w.alt_price(i, name, price)
        return mean * self.cm.f_mean * (alt + (1 - a) * (1 - RHO) * self.w.L + (1 - a) * RHO * (price + self.w.check_price))

    def catch_cost(self, i, ri, name, price, mean, q):
        """Net protection value (16 Nov 2026): cost of resolving a caught failure by the cross-check."""
        if not NETPV:
            return 0.0
        a = P_OK
        alt = self.w.alt_price(i, name, price)
        R = alt + (1 - a) * (1 - RHO) * self.w.L + (1 - a) * RHO * (price + self.w.check_price)
        return q * (1 - mean) * (1 - RHO) * R

    def observe(self, i, name, isX, checked, kind):
        kind = kind if kind in ("loud",) + FLAG_KINDS else "none"
        if checked:
            self.cm.update(kind, self.est.mean if isX else P_OK, P_OK)
            self.est.invalidate()
        if isX:
            self.est.update(checked, kind, P_OK)


class RuleV5ToldCB(RuleV5CB):
    told = True


class _Old:
    """Adapter for the 21 Oct strategies: a flag counts as a failure seen (they cannot tell a false alarm)."""
    def __init__(self, inner):
        self.inner = inner

    def route(self, i):
        return self.inner.route(i)

    def check(self, i, step, name, isX, ri, price):
        return self.inner.check(i, step, name, isX)

    def observe(self, i, name, isX, checked, kind):
        self.inner.observe(isX, checked, kind in ("loud", "caught", "flag_disagree", "flag_altloud"))


class AlwaysX(_Old):
    crosscheck = True


STRATS = {
    "never": lambda w, s: _Old(Never(w, s)),
    "always": lambda w, s: _Old(Always(w, s)),
    "cusum": lambda w, s: _Old(Cusum(w, s)),
    "v2": lambda w, s: _Old(RuleV2(w, s)),          # the rule confirmed on CostBench on 21 Oct (perfect-checker design)
    "v4": RuleV4CB,                                  # told q and f
    "v4_nocal": RuleV4NoCal,                         # no calibration labels
    "always_x": lambda w, s: AlwaysX(Always(w, s)),  # check everything, cross-check every flag
    "v5_told": RuleV5ToldCB,                         # ablation: cross-check, told q and f
    "v5": RuleV5CB,                                  # rule v5: cross-check, learns q and f, no labels
}


# --------------------------------------------------------------------------- simulation
def simulate(w, strat):
    spend = fail_cost = 0.0
    leaks = fails = checks = xchecks = fa_resolved = false_alarms = 0
    xc = bool(getattr(strat, "crosscheck", False))
    for i, task in enumerate(w.tasks):
        ri = strat.route(i)
        steps = task["routes"][ri]
        leaked = failed = False
        for s, (name, price) in enumerate(steps):
            isX = name == task["X"]
            p = w.p_of(i, name)
            chk = bool(strat.check(i, s, name, isX, ri, price))
            done = False
            for a in range(R_MAX + 1):
                u = w.U[i, ri, s, a]
                spend += price + (w.check_price if chk else 0.0)
                checks += chk
                if u[0] < p:                                         # correct output
                    if not (chk and w.UFA[i, ri, s, a] < w.f):
                        strat.observe(i, name, isX, chk, "none"); done = True; break
                    false_alarms += 1; correct = True                # flagged although correct
                elif u[1] < RHO:                                     # loud failure, seen for free
                    strat.observe(i, name, isX, chk, "loud"); continue
                elif chk and u[2] < w.q:                             # silent failure caught by the check
                    correct = False
                else:                                                # silent failure not caught: a leak
                    strat.observe(i, name, isX, chk, "none"); leaked = True; done = True; break
                if not xc:                                           # retry the same tool
                    strat.observe(i, name, isX, chk, "caught"); continue
                spend += w.alt_price(i, name, price); xchecks += 1
                ua = w.UALT[i, ri, s, a]
                alt = "ok" if ua[0] < P_OK else ("loud" if ua[1] < RHO else "wrong")
                if alt == "loud":
                    strat.observe(i, name, isX, chk, "flag_altloud"); continue
                if correct and alt == "ok":                          # outputs agree: keep the original
                    strat.observe(i, name, isX, chk, "flag_agree"); fa_resolved += 1; done = True; break
                strat.observe(i, name, isX, chk, "flag_disagree")    # use the alternative's output
                leaked = leaked or alt == "wrong"; done = True; break
            if not done:
                failed = True
                break
        if leaked:
            leaks += 1
        elif failed:
            fails += 1
            fail_cost += sum(c for _, c in steps)                    # a known failure has to be redone
    n = N_TASKS
    out = dict(loss=(spend + w.L * leaks + fail_cost) / n, spend=spend / n, leak_rate=leaks / n, fail_rate=fails / n,
               checks=checks / n, crosschecks=xchecks / n, fa_resolved=fa_resolved / n, false_alarms=false_alarms / n)
    cm = getattr(strat, "cm", None)
    if cm is not None:
        out.update(f_hat=cm.f_mean, q_hat=cm.q_mean)
    return out


_DATA = None


def _job(key):
    global _DATA
    drop, q, f, pi, lm, gap, seed = key[:7]
    cf = key[7] if len(key) > 7 else None                 # part 2 (cheap checks) passes the check price
    if _DATA is None:
        _DATA = json.load(open(ROUTES))
    w = WorldFA(_DATA, drop, q, f, pi, lm, gap, seed, check_frac=cf)
    rows = []
    for name, make in STRATS.items():
        r = simulate(w, make(w, seed))
        rows.append(dict(strategy=name, drop=drop, q=q, f=f, pi=pi, leak_mult=lm, gap=gap, seed=seed, **r))
    return rows


# --------------------------------------------------------------------------- report
def _p(x, y):
    x, y = np.asarray(x), np.asarray(y)
    return 1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative="less").pvalue)


def _boot_ci(x, y, n=10000, seed=0):
    x, y = np.asarray(x), np.asarray(y)
    idx = np.random.default_rng(seed).integers(0, len(x), (n, len(x)))
    d = 100 * (x[idx].mean(axis=1) / y[idx].mean(axis=1) - 1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def report(rows, seeds, title, secs):
    by = {}
    for r in rows:
        by.setdefault(r["strategy"], []).append(r)
    sm = lambda k, filt=lambda r: True: np.array([np.mean([r["loss"] for r in by[k] if r["seed"] == sd and filt(r)])
                                                  for sd in seeds])
    ncond = len(rows) // (len(STRATS) * len(seeds))
    L = [f"# {title}", "",
         f"CostBench tasks and prices ({ROUTES}); seeds {seeds[0]}-{seeds[-1]}; {ncond} conditions per seed; "
         f"{len(rows)} runs; {secs:.0f} s.",
         "Unit of analysis: the seed (mean over the conditions). Metric: total loss per task = spend + leak loss x "
         "leaks + route cost x failed tasks.", "",
         "## Mean outcomes per strategy", "",
         "| Strategy | total loss | spend | wrong answers kept | failed tasks | checks/task | cross-checks/task | false alarms resolved/task |",
         "|---|---|---|---|---|---|---|---|"]
    for k in STRATS:
        g = lambda f: np.mean([r[f] for r in by[k]])
        L.append(f"| {k} | {g('loss'):.1f} | {g('spend'):.1f} | {g('leak_rate'):.1%} | {g('fail_rate'):.1%} | "
                 f"{g('checks'):.2f} | {g('crosschecks'):.2f} | {g('fa_resolved'):.2f} |")
    L += ["", "## Mean total loss by condition", "",
          "| Strategy | leak 1 | leak 3 | pi 0 | pi 1 | f 0.05 | f 0.15 | native prices | X 20% cheaper |", "|---|---|---|---|---|---|---|---|---|"]
    for k in STRATS:
        g = lambda fn: np.mean([r["loss"] for r in by[k] if fn(r)])
        L.append(f"| {k} | {g(lambda r: r['leak_mult'] == 1):.1f} | {g(lambda r: r['leak_mult'] == 3):.1f} | "
                 f"{g(lambda r: r['pi'] == 0):.1f} | {g(lambda r: r['pi'] == 1):.1f} | {g(lambda r: r['f'] == 0.05):.1f} | "
                 f"{g(lambda r: r['f'] == 0.15):.1f} | {g(lambda r: r['gap'] == 0):.1f} | {g(lambda r: r['gap'] > 0):.1f} |")
    L += ["", "## Mean total loss by degradation of X", "", "| Strategy | " + " | ".join(f"X at {int(d * 100)}%" for d in DROPS) + " |",
          "|---|" + "---|" * len(DROPS)]
    for k in STRATS:
        L.append(f"| {k} | " + " | ".join(f"{np.mean([r['loss'] for r in by[k] if r['drop'] == d]):.1f}" for d in DROPS) + " |")

    v5 = sm("v5")
    R = ["", "## Pre-registered hypotheses (PREREGISTRATION_costbench_v5.md)", ""]
    prim = {}
    for hid, a, b in (("H-CB1", "v5", "v4_nocal"), ("H-CB2", "v5", "always_x"), ("H-CB3", "v5", "v4"), ("H-CB4", "v4", "v2")):
        x, y = sm(a), sm(b)
        prim[hid] = (_p(x, y), a, b, x.mean(), y.mean()) + _boot_ci(x, y)
    order = sorted(prim, key=lambda h: prim[h][0]); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and prim[h][0] < 0.05 / (len(order) - j)
        stop = stop or not holm[h]
    for h in ("H-CB1", "H-CB2", "H-CB3", "H-CB4"):
        p, a, b, xm, ym, lo, hi = prim[h]
        R.append(f"- {h} {a} below {b}: {xm:.1f} vs {ym:.1f} ({100 * (xm / ym - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%), "
                 f"Wilcoxon p = {p:.2g} over {len(seeds)} seeds, Holm {'ok' if holm[h] else 'fail'} -> "
                 f"**{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    told = sm("v5_told")
    lo, hi = _boot_ci(v5, told)
    R.append(f"- H-CB5 v5 (no labels) within 3% of v5_told: {v5.mean():.1f} vs {told.mean():.1f} "
             f"({100 * (v5.mean() / told.mean() - 1):+.1f}%, 95% CI upper {hi:+.1f}%) -> **{'CONFIRMED' if hi <= 3.0 else 'NOT CONFIRMED'}**")
    fe = [abs(r["f_hat"] - r["f"]) for r in by["v5"]]
    qe = [abs(r["q_hat"] - r["q"]) for r in by["v5"]]
    R.append(f"- Descriptive: v5's learned f, median |f_hat - f| = {np.median(fe):.3f}; learned q, median |q_hat - q| = {np.median(qe):.3f}")
    nat = lambda k: sm(k, lambda r: r["gap"] == 0)
    R.append(f"- Descriptive, native CostBench prices only: v5 {nat('v5').mean():.1f}, v4 {nat('v4').mean():.1f}, "
             f"v4_nocal {nat('v4_nocal').mean():.1f}, always_x {nat('always_x').mean():.1f}, v2 {nat('v2').mean():.1f}")
    return "\n".join(L + R)


def cheap_report(rows, seeds, secs):
    """Part 2: checks cost 5% of a tool call (PREREGISTRATION_costbench_v5_part2.md)."""
    by = {}
    for r in rows:
        by.setdefault(r["strategy"], []).append(r)
    sm = lambda k: np.array([np.mean([r["loss"] for r in by[k] if r["seed"] == sd]) for sd in seeds])
    L = ["# Rules v4 and v5 on CostBench, part 2: cheap checks (5% of a tool call), pre-registered test", "",
         f"Seeds {seeds[0]}-{seeds[-1]}; {len(rows) // (len(STRATS) * len(seeds))} conditions per seed; {len(rows)} runs; {secs:.0f} s.", "",
         "| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task |", "|---|---|---|---|---|---|"]
    for k in STRATS:
        g = lambda f: np.mean([r[f] for r in by[k]])
        L.append(f"| {k} | {g('loss'):.1f} | {g('leak_rate'):.1%} | {g('fail_rate'):.1%} | {g('checks'):.2f} | {g('crosschecks'):.2f} |")
    v5 = sm("v5")
    R = ["", "## Pre-registered hypotheses", ""]
    prim = {}
    for hid, b in (("H-CC1", "v4_nocal"), ("H-CC3", "always_x")):
        y = sm(b)
        prim[hid] = (_p(v5, y), b, y.mean()) + _boot_ci(v5, y)
    order = sorted(prim, key=lambda h: prim[h][0]); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and prim[h][0] < 0.05 / (len(order) - j)
        stop = stop or not holm[h]
    for h in ("H-CC1", "H-CC3"):
        p, b, ym, lo, hi = prim[h]
        R.append(f"- {h} v5 below {b}: {v5.mean():.1f} vs {ym:.1f} ({100 * (v5.mean() / ym - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%), "
                 f"Wilcoxon p = {p:.2g} over {len(seeds)} seeds, Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    v4 = sm("v4")
    lo, hi = _boot_ci(v5, v4)
    R.append(f"- H-CC2 v5 (no labels) equivalent to v4 told q and f, within +/-3%: {v5.mean():.1f} vs {v4.mean():.1f} "
             f"({100 * (v5.mean() / v4.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%) -> **{'CONFIRMED' if -3 <= lo and hi <= 3 else 'NOT CONFIRMED'}**")
    fe = [abs(r["f_hat"] - r["f"]) for r in by["v5"]]
    R.append(f"- Descriptive: v5's learned f, median |f_hat - f| = {np.median(fe):.3f}; v5_told {sm('v5_told').mean():.1f}")
    return "\n".join(L + R)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("dev", "confirm", "cheap"))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args(argv)
    if a.cmd == "cheap":
        keys = [k + (CHEAP_FRAC,) for k in itertools.product(DROPS, QS, FS, PIS, LEAKS, CHEAP_GAPS, CHEAP_SEEDS)]
        t0 = time.time()
        with Pool(a.procs) as pool:
            rows = [dict(r, check_frac=CHEAP_FRAC) for rs in pool.imap_unordered(_job, keys, chunksize=4) for r in rs]
        out = os.path.join("results", f"costbench_v5_cheap_{time.strftime('%Y%m%d-%H%M%S')}")
        os.makedirs(out, exist_ok=True)
        json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
        rep = cheap_report(rows, list(CHEAP_SEEDS), time.time() - t0)
        open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)
        return
    seeds = DEV_SEEDS if a.cmd == "dev" else TEST_SEEDS
    keys = list(itertools.product(DROPS, QS, FS, PIS, LEAKS, GAPS, seeds))
    t0 = time.time()
    with Pool(a.procs) as pool:
        rows = [r for rs in pool.imap_unordered(_job, keys, chunksize=4) for r in rs]
    out = os.path.join("results", f"costbench_v5_{a.cmd}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    title = ("Rules v4 and v5 on CostBench: development smoke test (not a test of the hypotheses)" if a.cmd == "dev"
             else "Rules v4 and v5 on CostBench: pre-registered test")
    rep = report(rows, list(seeds), title, time.time() - t0)
    open(os.path.join(out, "report.md"), "w").write(rep)
    print(rep)
    print("Saved to", out)


if __name__ == "__main__":
    main()
