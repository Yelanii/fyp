"""Bayes-optimal comparator on a small instance (27 October 2026; requested by external review 3).

"Perfect-knowledge optimum" (B6) sees the hidden state, so it is not a fair reference for a rule that cannot.
Here the BEST POSSIBLE policy for an agent that sees only what the rules see is computed exactly, by dynamic
programming over its belief, for a small instance where that is tractable:
  * two tools: A (cheap, price 20) silently drops from p0 = 0.95 to p1 at an unknown time t0, uniform on
    {150, ..., 349}, exactly as the simulator's drop scenarios; B (price 24, p = 0.95) never changes;
  * single-step tasks (steps_per_task = 1, 600 tasks) and no retries (r_max = 0): a detected failure fails the task.
    With these, the only hidden state is "has A degraded?", so the agent's belief is one number b and the dynamic
    programme over (time, b) is exact up to a fine belief grid with linear interpolation;
  * actions on A: call, call and check, switch to B (permanent: after switching, A is no longer observed, so the
    belief that it degraded can only grow and moving back is never better).
The Bayes policy is TOLD the model: p0, p1, the change-time distribution, q, f, rho and the prices. It is the best
any strategy with the same actions (call / check / switch) can do on average. Rule v5 has an extra action
(cross-checking on B), so it is reported separately.

Per step on a tool with success rate p (rho = loud share, q = catch rate, f = false-alarm rate):
    unchecked:  loud (1-p) rho -> task failed      | nothing seen otherwise; a silent failure leaks
    checked:    loud (1-p) rho | flag p f + (1-p)(1-rho) q -> task failed | nothing seen otherwise
    cost now = price (+ check price) + task cost x P(task failed) + leak loss x P(leak)
"""
import numpy as np

from .strategies import Strategy, REGISTRY

BG = np.linspace(0.0, 1.0, 1001)   # belief grid: probability that A has degraded


def hazard(t, lo=150, hi=350):
    """P(change happens at step t | not yet changed), for t0 uniform on {lo, ..., hi-1}."""
    if t < lo or t >= hi:
        return 0.0
    return 1.0 / (hi - t)


def _step_terms(p, chk, s):
    """(P(loud), P(flag), P(none), expected immediate cost) for one step on a tool with success rate p."""
    r, q, f = s.rho, s.q_true, s.false_alarm
    loud = (1 - p) * r
    flag = (p * f + (1 - p) * (1 - r) * q) if chk else 0.0
    none = 1 - loud - flag
    leak = (1 - p) * (1 - r) * ((1 - q) if chk else 1.0)
    return loud, flag, none, leak


class BayesPolicy:
    """Solves the dynamic programme once for a setting; act(t, b, on_b) gives the optimal action."""

    def __init__(self, s, p1, T=600, lo=150, hi=350):
        assert len(s.tools) == 2 and s.steps_per_task == 1 and s.r_max == 0
        self.s, self.p0, self.p1, self.T, self.lo, self.hi = s, s.tools[0].base_p, p1, T, lo, hi
        A, B = s.eff_price(0), s.eff_price(1)
        cc, L, F = s.check_price, s.leak_loss, s.task_cost
        pB = s.tools[1].base_p

        def cost(p, chk, price):
            loud, flag, none, leak = _step_terms(p, chk, s)
            return price + (cc if chk else 0.0) + F * (loud + flag) + L * leak

        # B phase: stable tool, so the best per-step action is the same at every step
        self.b_chk = cost(pB, True, B) < cost(pB, False, B)
        wB = min(cost(pB, True, B), cost(pB, False, B))
        self.W = wB * (T - np.arange(T + 1))        # W[t] = cost of steps t..T-1 on B

        V = np.zeros((T + 1, BG.size))
        self.act = np.zeros((T, BG.size), dtype=np.int8)     # 0 call, 1 check, 2 switch
        t0 = [_step_terms(self.p0, c, s) for c in (False, True)]
        t1 = [_step_terms(self.p1, c, s) for c in (False, True)]
        for t in range(T - 1, -1, -1):
            h_next = hazard(t + 1, lo, hi)
            def nxt(bpost):                          # value at t+1 after the hazard step
                bp = bpost + (1 - bpost) * h_next
                return np.interp(bp, BG, V[t + 1])
            vals = []
            for chk in (False, True):
                l0, fl0, n0, k0 = t0[chk]; l1, fl1, n1, k1 = t1[chk]
                b = BG
                imm = A + (cc if chk else 0.0) + F * ((1 - b) * (l0 + fl0) + b * (l1 + fl1)) + L * ((1 - b) * k0 + b * k1)
                fut = 0.0
                for o0, o1 in ((l0, l1), (fl0, fl1), (n0, n1)):
                    po = (1 - b) * o0 + b * o1
                    bpost = np.where(po > 0, b * o1 / np.maximum(po, 1e-300), b)
                    fut = fut + po * nxt(bpost)
                vals.append(imm + fut)
            vals.append(np.full(BG.size, s.switch_cost + wB + self.W[t + 1]))
            vals = np.stack(vals)
            self.act[t] = np.argmin(vals, axis=0)
            V[t] = vals.min(axis=0)
        self.V = V

    def action(self, t, b):
        i = int(np.clip(np.rint(b * (BG.size - 1)), 0, BG.size - 1))
        return int(self.act[t, i])

    def update(self, b, kind, chk):
        """Posterior belief after one observed outcome on A (kind: 'loud', 'caught' (a flag) or 'none')."""
        l0, fl0, n0, _ = _step_terms(self.p0, chk, self.s)
        l1, fl1, n1, _ = _step_terms(self.p1, chk, self.s)
        o0, o1 = {"loud": (l0, l1), "caught": (fl0, fl1)}.get(kind, (n0, n1))
        po = (1 - b) * o0 + b * o1
        return b * o1 / po if po > 0 else b


_CACHE = {}


class BayesOptimal(Strategy):
    """Runs the Bayes-optimal policy in the simulator (told the model; see the module docstring)."""
    name = "B13_bayes"

    def __init__(self, s, rng, window=60, p1=0.75):
        super().__init__(s, rng, window)
        key = (s, float(p1))
        if key not in _CACHE:
            _CACHE[key] = BayesPolicy(s, float(p1))
        self.pol = _CACHE[key]
        self.b_post, self.t_last, self.chk_last = 0.0, -1, False

    def _prior(self, t):
        b = self.b_post
        for tt in range(self.t_last + 1, t + 1):
            b = b + (1 - b) * hazard(tt, self.pol.lo, self.pol.hi)
        return b

    def decide(self, ctx, allow_switch=True):
        t, cur = ctx["t"], ctx["cur"]
        ctx["trace"] = {}
        if cur == 1:
            self.chk_last = self.pol.b_chk
            return "call_and_check" if self.pol.b_chk else "call"
        b = self._prior(t)
        a = self.pol.action(t, b)
        ctx["trace"] = dict(mean=1 - b, belief_degraded=b)
        if a == 2 and allow_switch:
            return "switch"
        if a == 2:
            a = 0
        self.b_prior, self.t_now, self.chk_last = b, t, a == 1
        return "call_and_check" if a == 1 else "call"

    def switch_to(self, ctx):
        self.current = 1
        return 1

    def observe(self, k, checked, failure_seen, kind=None):
        if k != 0:
            return
        kd = kind if kind in ("loud", "caught") else "none"
        self.b_post = self.pol.update(self.b_prior, kd, bool(checked))
        self.t_last = self.t_now


REGISTRY[BayesOptimal.name] = BayesOptimal
