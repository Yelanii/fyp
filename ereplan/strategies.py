"""The proposed three-zone rule (Section 3.3.5.5) and the pilot baselines (Table 3.10).

Every strategy answers three questions for the runner:
  start_task(ctx)            which tool should the planner use for this task?
  decide(ctx, allow_switch)  'switch', 'call' or 'call_and_check' for the next call
  switch_to(ctx)             which tool to move to after deciding to switch
and learns from observe(k, checked, failure_seen) after every attempt.
"""
from functools import lru_cache
import math
import numpy as np
from scipy.stats import binom

from .config import Setting
from .estimator import RangeEstimator, GRID


# --------------------------------------------------------------------------- shared formulas
def switch_line(s: Setting, cur: int, u: int, alt_p: dict, switch_cost: float):
    """Break-even success rate for the current tool (R_rest = 0 in the pilot).

    p_break = u (c + lam*l) / (R_alt + c_switch), with R_alt = u * (c_j + lam*l_j) / p_j
    for the cheapest alternative j. Returns (line, best_alternative, R_alt).
    """
    best_j, best_cost = None, math.inf
    for j, pj in alt_p.items():
        if j == cur:
            continue
        cost = u * s.eff_price(j) / max(pj, 1e-6)
        if cost < best_cost:
            best_j, best_cost = j, cost
    denom = best_cost + switch_cost
    if denom <= 0:
        return 1.0, best_j, best_cost
    return u * s.eff_price(cur) / denom, best_j, best_cost


def protection_value(p_hat: float, s: Setting) -> float:
    """PV = q (1 - p_hat)(1 - rho) L_leak: expected leak loss one check avoids."""
    return s.q_assumed * (1.0 - p_hat) * (1.0 - s.rho) * s.leak_loss


@lru_cache(maxsize=64)
def _fail_pmf(k: int, d_c: float) -> np.ndarray:
    """P(j failures seen in k checked calls | p) for every grid value of p: shape (k+1, G)."""
    pf = (1.0 - GRID) * d_c
    return np.stack([binom.pmf(j, k, pf) for j in range(k + 1)])


def decision_value(est: RangeEstimator, s: Setting, cur: int, u: int, R_alt: float, k: int) -> float:
    """DV: expected saving from deciding keep/switch after the next k checks rather than now.

    DV = (1/k) * sum_j P(j | data) [C_{d0}(pi_j) - C_{dj}(pi_j)]   (Howard, 1966)
    It is zero whenever no possible result of the k checks could change the decision.
    """
    k = max(1, min(k, u))
    post = est.posterior()
    pmf = _fail_pmf(k, round(est.d_c, 6))           # (k+1, G)
    joint = pmf * post                               # unnormalised posterior after j failures
    pj = joint.sum(axis=1)                           # P(j | data)
    means = (joint * GRID).sum(axis=1) / np.maximum(pj, 1e-300)
    c = s.eff_price(cur)
    switch_cost_total = R_alt + s.switch_cost
    stay_now = u * c / max(float((post * GRID).sum()), 1e-6)
    d0_is_stay = stay_now <= switch_cost_total
    saving = 0.0
    for j in range(k + 1):
        stay_j = u * c / max(means[j], 1e-6)
        best_j = min(stay_j, switch_cost_total)
        c_d0 = stay_j if d0_is_stay else switch_cost_total
        saving += pj[j] * (c_d0 - best_j)
    return saving / k


# --------------------------------------------------------------------------- base classes
class Strategy:
    name = "base"
    uses_estimates = True

    def __init__(self, s: Setting, rng: np.random.Generator, window: int = 60):
        self.s = s
        self.rng = rng
        self.window = window
        self.ests = [RangeEstimator(window, s.rho, s.q_assumed, t.advertised_p, s.prior_strength)
                     for t in s.tools]
        self.current = None   # tool in use; kept across tasks until the rule switches

    # -- learning
    def observe(self, k: int, checked: bool, failure_seen: bool, kind=None):
        self.ests[k].update(checked, failure_seen)

    # -- planning
    def p_view(self, ctx) -> dict:
        return {j: e.mean for j, e in enumerate(self.ests)}

    def start_task(self, ctx) -> int:
        """Scripted planner: pick the cheapest tool by effective cost once, then keep it.
        Moving to another tool happens only through the switch decision, so the planner and
        the rule cannot disagree and ping-pong between tools."""
        if self.current is None:
            p = self.p_view(ctx)
            self.current = min(range(len(self.s.tools)),
                               key=lambda j: self.s.eff_price(j) / max(p[j], 1e-6))
        return self.current

    def horizon(self, ctx) -> int:
        """u: calls left on the tool in the plan.
        'task' (proposal default): the rest of the current task.
        'session' (sensitivity option): calls left in the run, capped at session_cap, because the
        chosen tool is kept across tasks and so a switch affects later tasks too."""
        if getattr(self, "horizon_mode", "task") == "session":
            return int(min(ctx["left_in_run"], getattr(self, "session_cap", 50)))
        return ctx["u"]

    def line(self, ctx):
        return switch_line(self.s, ctx["cur"], self.horizon(ctx), self.p_view(ctx), self.s.switch_cost)

    def switch_to(self, ctx) -> int:
        self.current = self.line(ctx)[1]
        return self.current

    # -- deciding
    def decide(self, ctx, allow_switch: bool = True) -> str:
        line, _, _ = self.line(ctx)
        mean, low, high = self.ests[ctx["cur"]].summary()
        ctx["trace"] = dict(line=line, mean=mean, low=low, high=high)
        if allow_switch and high < line:
            ctx["trace"]["reason"] = f"range {low:.0%}-{high:.0%} is below switch line {line:.0%}"
            return "switch"
        return "call_and_check" if self.wants_check(ctx, line, mean, low, high) else "call"

    def wants_check(self, ctx, line, mean, low, high) -> bool:
        raise NotImplementedError


# --------------------------------------------------------------------------- the proposed rule
class ThreeZoneRule(Strategy):
    """Switch if the whole range is below the line; in the crossing zone check when PV + DV >= price;
    in the safe zone check only when PV >= price; always audit with probability epsilon."""
    name = "Rule"

    def __init__(self, s, rng, window=60, epsilon=0.03, k=3):
        super().__init__(s, rng, window)
        self.epsilon = epsilon
        self.k = k

    def wants_check(self, ctx, line, mean, low, high):
        audit = self.rng.random() < self.epsilon      # decided before the call
        pv = protection_value(mean, self.s)
        crossing = low <= line <= high
        dv = 0.0
        if crossing:
            _, _, R_alt = self.line(ctx)
            dv = decision_value(self.ests[ctx["cur"]], self.s, ctx["cur"], self.horizon(ctx), R_alt, self.k)
        value = pv + dv
        ctx["trace"].update(pv=pv, dv=dv, zone="crossing" if crossing else "safe", audit=audit)
        check = value >= self.s.check_price or audit
        if check:
            why = "random audit" if (audit and value < self.s.check_price) else \
                  f"value {value:.1f} (PV {pv:.1f} + DV {dv:.1f}) >= check price {self.s.check_price:.1f}"
            ctx["trace"]["reason"] = f"range {low:.0%}-{high:.0%} vs line {line:.0%}; {why}"
        else:
            ctx["trace"]["reason"] = f"range {low:.0%}-{high:.0%} vs line {line:.0%}; value {value:.1f} < check price {self.s.check_price:.1f}"
        return check


# --------------------------------------------------------------------------- baselines
class CheckAlways(Strategy):          # B1
    name = "B1_always"
    def wants_check(self, ctx, *a): return True


class NeverCheck(Strategy):           # B2
    name = "B2_never"
    def wants_check(self, ctx, *a): return False


class FixedRate(Strategy):            # B3
    name = "B3_fixed"
    def __init__(self, s, rng, window=60, rate=0.1):
        super().__init__(s, rng, window)
        self.rate = rate
    def wants_check(self, ctx, *a): return self.rng.random() < self.rate


class FixedEstimate(Strategy):        # B8, modelled on INTENT / MCPP: estimates fixed before the run
    name = "B8_fixed_est"
    def __init__(self, s, rng, window=60, rate=0.1):
        super().__init__(s, rng, window)
        self.rate = rate
    def p_view(self, ctx):
        return {j: t.advertised_p for j, t in enumerate(self.s.tools)}
    def decide(self, ctx, allow_switch=True):
        line, _, _ = self.line(ctx)
        p_fixed = self.s.tools[ctx["cur"]].advertised_p
        ctx["trace"] = dict(line=line, mean=p_fixed, low=p_fixed, high=p_fixed)
        if allow_switch and p_fixed < line:
            return "switch"
        return "call_and_check" if self.rng.random() < self.rate else "call"


class Cusum(Strategy):                # B4, detection-focused (Page, 1954); agent instance: Dubey (2026)
    """Bernoulli CUSUM on 'failure seen' with the same check correction. Checks when the statistic
    is high (or at a small audit rate); switches on an alarm and keeps the new tool until the next alarm."""
    name = "B4_cusum"

    def __init__(self, s, rng, window=60, h=4.0, p1=0.75, audit=0.05):
        super().__init__(s, rng, window)
        self.h, self.p1, self.audit = h, p1, audit
        self.p0 = None
        self.S = 0.0
        self.current = None
        self.alarmed = set()

    def start_task(self, ctx):
        if self.current is None:
            self.current = super().start_task(ctx)
        return self.current

    def observe(self, k, checked, failure_seen, kind=None):
        super().observe(k, checked, failure_seen)
        if k != self.current:
            return
        p0 = self.s.tools[k].advertised_p
        d = self.ests[k].d_c if checked else self.ests[k].d_u
        f0, f1 = (1 - p0) * d, (1 - self.p1) * d
        llr = math.log(f1 / f0) if failure_seen else math.log((1 - f1) / (1 - f0))
        self.S = max(0.0, self.S + llr)

    def decide(self, ctx, allow_switch=True):
        line, _, _ = self.line(ctx)
        mean, low, high = self.ests[ctx["cur"]].summary()
        ctx["trace"] = dict(line=line, mean=mean, low=low, high=high, cusum=self.S)
        if allow_switch and self.S > self.h:
            return "switch"
        high_stat = self.S > self.h / 2
        return "call_and_check" if (high_stat or self.rng.random() < self.audit) else "call"

    def switch_to(self, ctx):
        self.alarmed.add(ctx["cur"])
        options = [j for j in range(len(self.s.tools)) if j not in self.alarmed] or \
                  [j for j in range(len(self.s.tools)) if j != ctx["cur"]]
        new = min(options, key=lambda j: self.s.eff_price(j) / self.s.tools[j].advertised_p)
        self.current, self.S = new, 0.0
        return new


class Oracle(Strategy):               # B6: knows the true rates (reference only, not judged)
    name = "B6_oracle"
    def p_view(self, ctx):
        return {j: float(ctx["env"].p[j, ctx["t"]]) for j in range(len(self.s.tools))}
    def decide(self, ctx, allow_switch=True):
        p = self.p_view(ctx)
        line, _, _ = self.line(ctx)
        pc = p[ctx["cur"]]
        ctx["trace"] = dict(line=line, mean=pc, low=pc, high=pc)
        if allow_switch and pc < line:
            return "switch"
        return "call_and_check" if protection_value(pc, self.s) >= self.s.check_price else "call"


REGISTRY = {cls.name: cls for cls in (ThreeZoneRule, CheckAlways, NeverCheck, FixedRate,
                                      Cusum, FixedEstimate, Oracle)}


# --------------------------------------------------------------------------- exploratory variant (not pre-registered)
def exact_step_cost(s: Setting, j: int, p: float) -> float:
    """Exact expected loss of one planned step on tool j without a check (policy N of Theorem 1): loud failures
    are retried up to r_max times, silent failures are accepted (PREREGISTRATION_exactline.md)."""
    p = min(max(p, 0.0), 1.0)
    l, sil = (1 - p) * s.rho, (1 - p) * (1 - s.rho)
    n = s.r_max + 1
    calls = float(n) if l >= 1 - 1e-12 else (1 - l ** n) / (1 - l)
    return s.eff_price(j) * calls + s.leak_loss * sil * calls + s.task_cost * l ** n


def leak_aware_line(s: Setting, cur: int, u: int, alt_p: dict, switch_cost: float, exact: bool = False):
    """Exploratory: break-even rate when the cost of staying also counts expected leak loss.

    stay(p)   = u * [ c/p + (1 - p)(1 - rho) * L_leak ]
    switch    = min_j u * [ c_j/p_j + (1 - p_j)(1 - rho) * L_leak ] + c_switch
    Solved for p by bisection (stay(p) falls as p rises).
    """
    def per_call(j, p):
        if exact:
            return exact_step_cost(s, j, p)
        p = max(p, 1e-6)
        return s.eff_price(j) / p + (1 - p) * (1 - s.rho) * s.leak_loss
    best_j = min((j for j in alt_p if j != cur), key=lambda j: per_call(j, alt_p[j]))
    R_alt = u * per_call(best_j, alt_p[best_j])
    target = R_alt + switch_cost
    if u * per_call(cur, 1.0) >= target:
        return 1.0, best_j, R_alt
    lo, hi = 1e-3, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if u * per_call(cur, mid) > target:
            lo = mid
        else:
            hi = mid
    return hi, best_j, R_alt


class LeakAwareRule(ThreeZoneRule):
    """Exploratory variant: identical three-zone rule, but the switch line includes leak loss."""
    name = "Rule_leakaware"

    def line(self, ctx):
        return leak_aware_line(self.s, ctx["cur"], self.horizon(ctx), self.p_view(ctx), self.s.switch_cost,
                               exact=getattr(self, "exact_line", False))


REGISTRY[LeakAwareRule.name] = LeakAwareRule
