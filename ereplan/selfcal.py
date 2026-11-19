"""Rule v3: the decision rule with a self-calibrating check ("bad-checker detector").

Idea: a loud failure (an explicit error) is seen for free and cannot be hidden by a bad check. A caught
failure is seen only through a check. So from the same recent calls we can estimate BOTH
    p = how often the tool succeeds      (mainly from the loud-failure rate: loud = (1 - p) * rho)
    q = how often the check catches a silent failure   (from caught failures on checked calls)
by a joint posterior over (p, q). If checks catch far fewer failures than the loud errors imply, q is
estimated low: the agent then (1) stops trusting checked calls as evidence that the tool is fine, and
(2) stops paying for checks whose protection value is small.

Per-call likelihood (rho = loud share, known):
    unchecked:  loud (1-p)rho                      | nothing seen 1 - (1-p)rho
    checked:    loud (1-p)rho | caught (1-p)(1-rho)q | nothing seen p + (1-p)(1-rho)(1-q)
"""
from collections import deque
import numpy as np
from scipy.stats import binom

from .strategies import LeakAwareRule, REGISTRY

PG = np.linspace(0.0, 1.0, 101)[:, None]     # success-rate grid (rows)
QG = np.linspace(0.0, 1.0, 41)[None, :]      # catch-rate grid (columns)
_E = 1e-12


class JointEstimator:
    def __init__(self, window, rho, q_prior_mean, q_prior_strength, p_prior_mean, p_prior_strength):
        self.window, self.rho = window, rho
        a = max(p_prior_mean * p_prior_strength, 1.0); b = max((1 - p_prior_mean) * p_prior_strength, 1.0)
        self._lp_p = (a - 1) * np.log(np.clip(PG, _E, 1)) + (b - 1) * np.log(np.clip(1 - PG, _E, 1))
        aq = max(q_prior_mean * q_prior_strength, 1.0); bq = max((1 - q_prior_mean) * q_prior_strength, 1.0)
        self._lp_q = (aq - 1) * np.log(np.clip(QG, _E, 1)) + (bq - 1) * np.log(np.clip(1 - QG, _E, 1))
        self.obs = deque(maxlen=window)        # (checked, kind) with kind in {"none", "loud", "caught"}
        self._cache = None
        self.d_c = rho + (1 - rho) * q_prior_mean

    def update(self, checked, kind):
        k = kind if kind in ("loud", "caught") else "none"
        self.obs.append((bool(checked), k))
        self._cache = None

    def joint(self):
        if self._cache is not None:
            return self._cache
        ul = un = cl = cc = cn = 0
        for c, k in self.obs:
            if c:
                cl += k == "loud"; cc += k == "caught"; cn += k == "none"
            else:
                ul += k == "loud"; un += k == "none"
        r = self.rho
        loud = np.clip((1 - PG) * r, _E, 1)
        lp = (ul + cl) * np.log(loud) + un * np.log(np.clip(1 - (1 - PG) * r, _E, 1))
        lp = lp + cc * np.log(np.clip((1 - PG) * (1 - r) * QG, _E, 1))
        lp = lp + cn * np.log(np.clip(PG + (1 - PG) * (1 - r) * (1 - QG), _E, 1))
        fade = max(0.0, 1.0 - len(self.obs) / self.window)
        lp = lp + fade * self._lp_p + self._lp_q
        lp -= lp.max()
        w = np.exp(lp); w /= w.sum()
        self._cache = w
        return w

    def summary(self):
        w = self.joint()
        mp = w.sum(axis=1)
        cdf = np.cumsum(mp)
        grid = PG[:, 0]
        low = grid[np.searchsorted(cdf, 0.025)]
        high = grid[min(np.searchsorted(cdf, 0.975), len(grid) - 1)]
        return float((mp * grid).sum()), float(low), float(high)

    @property
    def mean(self):
        return self.summary()[0]

    @property
    def q_hat(self):
        return float((self.joint().sum(axis=0) * QG[0]).sum())


class SelfCalibratingRule(LeakAwareRule):
    """Rule v2 + joint (p, q) estimate: protection and decision values use the estimated catch rate."""
    name = "Rule_v3_selfcal"

    def __init__(self, s, rng, window=60, epsilon=0.02, k=3, q_prior_strength=6.0):
        super().__init__(s, rng, window, epsilon, k)
        self.ests = [JointEstimator(window, s.rho, s.q_assumed, q_prior_strength, t.advertised_p, s.prior_strength)
                     for t in s.tools]

    def observe(self, k, checked, failure_seen, kind=None):
        self.ests[k].update(checked, kind if kind is not None else ("loud" if failure_seen else "none"))

    def _dv(self, est, u, R_alt, cur):
        k = max(1, min(self.k, u))
        w = est.joint()
        f = (1 - PG) * (self.s.rho + (1 - self.s.rho) * QG)          # P(failure seen | checked)
        c = self.s.eff_price(cur)
        sw = R_alt + self.s.switch_cost
        pbar = float((w.sum(axis=1) * PG[:, 0]).sum())
        # dv_sym (19 Nov 2026, PREREGISTRATION_dvsym.md): price staying with the same per-call cost as the switch
        # line, g(c, p) = c/p + (1-p)(1-rho)L, instead of c/p only. Off by default, so every earlier result is unchanged.
        sym = getattr(self, "dv_sym", False)
        stay = (lambda m: u * (c / max(m, 1e-6) + (1 - m) * (1 - self.s.rho) * self.s.leak_loss)) if sym else \
               (lambda m: u * c / max(m, 1e-6))
        d0_stay = stay(pbar) <= sw
        sav = 0.0
        for j in range(k + 1):
            lj = w * binom.pmf(j, k, f)
            pj = lj.sum()
            if pj <= 0:
                continue
            mj = float((lj.sum(axis=1) * PG[:, 0]).sum() / pj)
            stay_j = stay(mj)
            sav += pj * ((stay_j if d0_stay else sw) - min(stay_j, sw))
        return sav / k

    def wants_check(self, ctx, line, mean, low, high):
        est = self.ests[ctx["cur"]]
        audit = self.rng.random() < self.epsilon
        qh = est.q_hat
        pv = qh * (1 - mean) * (1 - self.s.rho) * self.s.leak_loss
        dv = 0.0
        if low <= line <= high:
            _, _, R_alt = self.line(ctx)
            dv = self._dv(est, self.horizon(ctx), R_alt, ctx["cur"])
        ctx["trace"].update(pv=pv, dv=dv, q_hat=qh, zone="crossing" if low <= line <= high else "safe", audit=audit)
        ctx["trace"]["reason"] = f"range {low:.0%}-{high:.0%} vs line {line:.0%}; check catch-rate estimate {qh:.2f}"
        return (pv + dv) >= self.s.check_price or audit


REGISTRY[SelfCalibratingRule.name] = SelfCalibratingRule
