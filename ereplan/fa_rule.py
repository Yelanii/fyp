"""Rule v4: the self-calibrating rule (v3) that also accounts for FALSE ALARMS.

Motivation (real-agent Run 2): a real LLM checker wrongly flagged 14% of correct steps, and because it is
deterministic it flagged them again on every retry, so checked tasks failed. Rules v2/v3 assume checks never
flag a correct result.

Two changes, both driven by the false-alarm rate f the agent is told (like q, measured in calibration):
 1. Learning: a flag on a checked call can be a real catch OR a false alarm.
        checked:  loud (1-p)rho | flagged (1-p)(1-rho)q + p f | nothing p(1-f) + (1-p)(1-rho)(1-q)
    (unchecked calls are unchanged). Without this, false alarms make the tool look worse than it is.
 2. Deciding: a check now has an expected COST beyond its price. With probability p * f it flags a correct
    step; with persistent false alarms the retries are flagged too, so the task fails. Expected cost:
        FA = p * f * (task cost + r_max * (tool price + check price))
    The rule checks only if  PV + DV - FA >= check price.
No new tuned parameter: f comes from calibration, everything else from rule v3.
"""
import numpy as np

from .selfcal import JointEstimator, SelfCalibratingRule, PG, QG, _E
from .strategies import REGISTRY


class JointEstimatorFA(JointEstimator):
    def __init__(self, *a, f=0.0, **kw):
        super().__init__(*a, **kw)
        self.f = f

    def joint(self):
        if self._cache is not None:
            return self._cache
        ul = un = cl = cc = cn = 0
        for c, k in self.obs:
            if c:
                cl += k == "loud"; cc += k == "caught"; cn += k == "none"
            else:
                ul += k == "loud"; un += k == "none"
        r, f = self.rho, self.f
        lp = (ul + cl) * np.log(np.clip((1 - PG) * r, _E, 1)) + un * np.log(np.clip(1 - (1 - PG) * r, _E, 1))
        lp = lp + cc * np.log(np.clip((1 - PG) * (1 - r) * QG + PG * f, _E, 1))
        lp = lp + cn * np.log(np.clip(PG * (1 - f) + (1 - PG) * (1 - r) * (1 - QG), _E, 1))
        fade = max(0.0, 1.0 - len(self.obs) / self.window)
        lp = lp + fade * self._lp_p + self._lp_q
        lp -= lp.max()
        w = np.exp(lp); w /= w.sum()
        self._cache = w
        return w


class FalseAlarmAwareRule(SelfCalibratingRule):
    name = "Rule_v4_fa"

    def __init__(self, s, rng, window=60, epsilon=0.02, k=3, q_prior_strength=3.0):
        super().__init__(s, rng, window, epsilon, k, q_prior_strength)
        self.f = s.f_assumed
        self.ests = [JointEstimatorFA(window, s.rho, s.q_assumed, q_prior_strength, t.advertised_p, s.prior_strength,
                                      f=self.f) for t in s.tools]

    def fa_cost(self, mean, cur):
        s = self.s
        return mean * self.f * (s.task_cost + s.r_max * (s.eff_price(cur) + s.check_price))

    def wants_check(self, ctx, line, mean, low, high):
        want = super().wants_check(ctx, line, mean, low, high)   # fills the trace with pv, dv, audit
        if self.f <= 0:
            return want
        tr = ctx["trace"]
        fa = self.fa_cost(mean, ctx["cur"])
        tr["fa_cost"] = fa
        tr["reason"] += f"; false-alarm cost {fa:.1f}"
        return (tr["pv"] + tr["dv"] - fa) >= self.s.check_price or tr["audit"]


REGISTRY[FalseAlarmAwareRule.name] = FalseAlarmAwareRule
