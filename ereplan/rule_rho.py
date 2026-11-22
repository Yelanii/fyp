"""Rule v4+rho (named so as not to clash with the proposal's "rule v5.1" = FR19):
rule v5 (cross-check) that LEARNS the share of failures that are loud (rho) instead of assuming it. This is FR20, a
different requirement from FR19's third-source/audit/fallback rule, which the proposal also calls "rule v5.1".

Why: on FreshQA-grounded runs (freshqa_feasibility.py) stale answers are always silent, while rules v4 and v5 assume
rho = 0.5. Under that assumption, the absence of error messages looks like evidence that the tool is healthy, so the
rule rarely checks and keeps many wrong answers.

How: on checked calls a failure is seen either as a loud error (probability rho) or as a silent failure caught by the
check and confirmed by the cross-check (probability (1 - rho) q). So among detected failures on checked calls
        share loud  r = rho / (rho + (1 - rho) q)   =>   rho = r q / (1 - r + r q).
r is estimated from the last W detected failures with a Beta(1, 1) prior (so with no data rho_hat is close to 0.5,
the old assumption), q is the checker memory's current estimate, and rho_hat replaces the fixed rho everywhere the rule
uses it (estimators, protection value, decision value, false-alarm cost, switch line). Nothing is tuned beyond v5's
settings except the window W = 30, chosen before any run.
"""
from collections import deque
import numpy as np

from .crosscheck import CrossCheckRule
from .strategies import REGISTRY


class LoudShareRule(CrossCheckRule):
    name = "Rule_v5_rho"

    rho_mode = "cap"            # "mean": posterior mean; "cap": never above the default; "lcb": lower credible bound

    audit_gain = 0.10           # extra random audits when failures turn out to be silent (development choice)

    def __init__(self, s, rng, rho_window=30, **kw):
        super().__init__(s, rng, **kw)
        self.rho0 = s.rho
        self.eps0 = self.epsilon
        self.events = deque(maxlen=rho_window)          # 1 = loud failure on a checked call, 0 = confirmed silent failure
        self.rho_hat = s.rho
        self._apply(s.rho)

    def _apply(self, rho):
        self.rho_hat = float(rho)
        if hasattr(self, "eps0"):
            # when failures are silent, unchecked calls carry no information, so audit more to keep learning
            self.epsilon = self.eps0 + self.audit_gain * max(0.0, 1.0 - self.rho_hat / self.rho0)
        self.s = self.s.with_(rho=self.rho_hat)          # the rule's own belief; the environment keeps the true value
        self.cm.rho = self.rho_hat
        for e in self.ests:
            e.rho = self.rho_hat
            e.invalidate()

    def observe(self, k, checked, failure_seen, kind=None, a=None):
        kd = kind if kind is not None else ("loud" if failure_seen else "none")
        super().observe(k, checked, failure_seen, kind=kind, a=a)
        if checked and kd in ("loud", "flag_disagree"):
            self.events.append(1 if kd == "loud" else 0)
            loud = sum(self.events)
            n = len(self.events)
            if self.rho_mode == "lcb":
                from scipy.stats import beta
                r = float(beta.ppf(0.2, loud + 1.0, n - loud + 1.0))
            else:
                r = (loud + 1.0) / (n + 2.0)
            q = min(max(self.cm.q_mean, 0.05), 0.99)
            rho = r * q / (1.0 - r + r * q)
            if self.rho_mode == "cap":
                rho = min(rho, self.rho0)    # never assume failures are MORE visible than the default
            self._apply(np.clip(rho, 0.02, 0.98))


class LoudShareRuleMean(LoudShareRule):
    name = "Rule_v5_rho_mean"; rho_mode = "mean"; rng_name = "Rule_v5_rho"


class LoudShareRuleLCB(LoudShareRule):
    name = "Rule_v5_rho_lcb"; rho_mode = "lcb"; rng_name = "Rule_v5_rho"


class LoudShareRuleNoAudit(LoudShareRule):
    name = "Rule_v5_rho_noaudit"; audit_gain = 0.0; rng_name = "Rule_v5_rho"


for _c in (LoudShareRule, LoudShareRuleMean, LoudShareRuleLCB, LoudShareRuleNoAudit):
    REGISTRY[_c.name] = _c
