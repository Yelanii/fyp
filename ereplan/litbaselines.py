"""Part E (24 October 2026): a persistence-aware form of rule v4 and three baselines modelled on the closest
works in the literature review (LR v3, Table 2.8). Each baseline adapts one published idea to this simulator;
the adaptations are stated in PREREGISTRATION_persistence.md and below, so a reader can judge their fairness.

Rule_v4_pi     Rule v4 with an assumed persistence pi_hat for false alarms. pi_hat = 1 is exactly rule v4 (the
               pre-registered rule); pi_hat = 0 is the independence assumption of VRR-Stop (Wu, Y. et al., 2026,
               §3.2); pi_hat = measured pi uses the repeat test (part D) to calibrate it.
B9_vrr         VRR-Stop-style re-verification (Wu, Y. et al., 2026): check every call; when the check flags an
               output, re-ask the checker up to K times and accept or reject from the posterior that the output is
               correct, ASSUMING the votes are independent given the truth.
B10_pbandit    ParetoBandit-style router (Taberner-Miller, 2026): Thompson sampling over tools on a cost-per-success
               score, with geometric forgetting of the per-tool statistics. Quality feedback is not free here, so
               it buys checks at a fixed rate and counts every flag as a failure (no correction for misses or
               false alarms). The budget pacer is omitted because these runs have no hard budget.
B11_btm        Bench2Robust-style Bayesian Tool Memory (Chen, C. et al., 2026, §3.1, App. B.1): Beta memory per
               tool built offline (a strong prior at the advertised rate), updated only between episodes (tasks),
               fixed within a task, with no forgetting and no paid checks.
"""
import math
import numpy as np

from .estimator import RangeEstimator
from .fa_rule import FalseAlarmAwareRule
from .strategies import Strategy, CheckAlways, REGISTRY, switch_line


# --------------------------------------------------------------------------- persistence-aware rule v4
def fa_cost_pi(mean: float, f: float, pi: float, s, cur: int) -> float:
    """Expected extra cost of checking a step that is correct (probability mean) when the checker raises a false
    alarm with probability f and repeats its verdict on a retry with probability pi.
    g = pi + (1 - pi) f is the chance that a retry of a correct step is flagged again, so
        P(step fails | first false alarm)  = g ** r_max
        E[extra attempts | first alarm]   = 1 + g + ... + g ** (r_max - 1)
    pi = 1 gives  mean * f * (task cost + r_max * (price + check price)), which is rule v4's formula."""
    g = pi + (1.0 - pi) * f
    r = s.r_max
    p_fail = g ** r
    extra = float(r) if g >= 1.0 else (1.0 - g ** r) / (1.0 - g)
    return mean * f * (p_fail * s.task_cost + extra * (s.eff_price(cur) + s.check_price))


class PersistenceAwareRule(FalseAlarmAwareRule):
    name = "Rule_v4_pi"
    rng_name = "Rule_v4_fa"          # same audit draws as rule v4, so the variants differ only in pi_hat

    def __init__(self, s, rng, window=60, epsilon=0.02, k=3, q_prior_strength=3.0, pi_assumed=1.0):
        super().__init__(s, rng, window, epsilon, k, q_prior_strength)
        self.pi_assumed = float(pi_assumed)

    def fa_cost(self, mean, cur):
        return fa_cost_pi(mean, self.f, self.pi_assumed, self.s, cur)


# --------------------------------------------------------------------------- B9: VRR-Stop-style re-verification
class VRRStyle(CheckAlways):
    name = "B9_vrr"

    def __init__(self, s, rng, window=30, reverify_k=2):
        super().__init__(s, rng, window)
        self.reverify_k = int(reverify_k)
        self.f = s.f_assumed

    def thr(self, k):
        """Accept a flagged output when the expected leak loss of accepting is at most the cost of one more attempt."""
        return (self.s.eff_price(k) + self.s.check_price) / max(self.s.leak_loss, 1e-9)

    def _p_wrong(self, k, votes):
        """P(output is a silent failure | not loud, votes), votes assumed independent given the truth."""
        p = self.ests[k].mean
        prior_ok = p / max(p + (1 - p) * (1 - self.s.rho), 1e-12)
        q, f = self.s.q_assumed, self.f
        l_ok = l_bad = 1.0
        for v in votes:
            l_ok *= f if v else (1 - f)
            l_bad *= q if v else (1 - q)
        num = (1 - prior_ok) * l_bad
        return num / max(num + prior_ok * l_ok, 1e-300)

    def wants_recheck(self, k, votes):
        pw = self._p_wrong(k, votes)
        return self.thr(k) < pw < 1 - 1e-6           # undecided: neither safe to accept nor certainly wrong

    def accept(self, k, votes):
        return self._p_wrong(k, votes) <= self.thr(k)


# --------------------------------------------------------------------------- B10: ParetoBandit-style router
class ParetoBanditStyle(Strategy):
    name = "B10_pbandit"

    def __init__(self, s, rng, window=60, gamma=0.98, check_rate=0.2):
        super().__init__(s, rng, window)
        self.gamma, self.check_rate = float(gamma), float(check_rate)
        n0 = s.prior_strength
        self.a = [t.advertised_p * n0 for t in s.tools]
        self.b = [(1 - t.advertised_p) * n0 for t in s.tools]
        self._target = None

    def observe(self, k, checked, failure_seen, kind=None):
        super().observe(k, checked, failure_seen)
        g = self.gamma
        self.a[k] = g * self.a[k] + (0.0 if failure_seen else 1.0)
        self.b[k] = g * self.b[k] + (1.0 if failure_seen else 0.0)

    def decide(self, ctx, allow_switch=True):
        cur = ctx["cur"]
        ctx["trace"] = {}
        if allow_switch:
            S = self.s.steps_per_task
            theta = [self.rng.beta(1.0 + self.a[j], 1.0 + self.b[j]) for j in range(len(self.s.tools))]
            score = [self.s.eff_price(j) / max(theta[j], 1e-6) + (self.s.switch_cost / S if j != cur else 0.0)
                     for j in range(len(self.s.tools))]
            best = int(np.argmin(score))
            ctx["trace"] = dict(mean=float(theta[cur]))
            if best != cur:
                self._target = best
                return "switch"
        return "call_and_check" if self.rng.random() < self.check_rate else "call"

    def switch_to(self, ctx):
        self.current = self._target
        return self.current


# --------------------------------------------------------------------------- B11: Bench2Robust-style tool memory
class BetaToolMemory(Strategy):
    name = "B11_btm"

    def __init__(self, s, rng, window=60, n_off=100.0):
        super().__init__(s, rng, window)
        # an effectively unbounded window keeps every count (no forgetting); the offline prior keeps its weight
        self.ests = [RangeEstimator(10 ** 7, s.rho, s.q_assumed, t.advertised_p, float(n_off)) for t in s.tools]
        self.pending = []

    def observe(self, k, checked, failure_seen, kind=None):
        self.pending.append((k, checked, failure_seen))      # applied only when the episode (task) ends

    def start_task(self, ctx):
        for k, c, f in self.pending:
            self.ests[k].update(c, f)
        self.pending = []
        return super().start_task(ctx)

    def decide(self, ctx, allow_switch=True):
        line, _, _ = self.line(ctx)
        mean = self.ests[ctx["cur"]].mean
        ctx["trace"] = dict(line=line, mean=mean, low=mean, high=mean)
        if allow_switch and mean < line:
            return "switch"
        return "call"


for _cls in (PersistenceAwareRule, VRRStyle, ParetoBanditStyle, BetaToolMemory):
    REGISTRY[_cls.name] = _cls
