"""Core 4 (31 October 2026): rule v5 when two wrong outputs can agree (shared mistakes).

Rule v5 reads an agreement after a flag as "the flag was a false alarm". If two tools can be wrong in the same way
(chance sigma), some agreements are really two matching wrong answers. Two facts (CORE4_2026-10-31.md):
  1. For a FIXED cross-check policy, sigma does not change the loss: a caught failure whose alternative is also
     wrong leaks whether the outputs agree (the original is kept) or not (the alternative is used).
  2. It does change what the rule LEARNS: agreements are counted as false alarms, so f is overestimated, q and the
     tool's success rate are underestimated / overestimated. At one success rate and one alternative, (q, f, sigma)
     are not identifiable without labels (the information matrix has rank 2); with two success-rate regimes, e.g.
     before and after a degradation, or two alternatives, they are (rank 3).
Rule_v5_s adds sigma to the checker memory, with a weak prior, and uses it in every likelihood. Because the
checker memory pools checked calls over the whole run, a degradation itself supplies the second regime.

Per checked call (s = (1-p)(1-rho), a = alternative's success rate):
    none            p (1-f) + s (1-q)
    flag, agree     p f a + s q (1-a)(1-rho) sigma
    flag, disagree  p f (1-a)(1-rho) + s q (a + (1-a)(1-rho)(1-sigma))
    flag unresolved p f + s q                (caught without cross-check, or the alternative failed loudly)
"""
import numpy as np

from .crosscheck import CheckerMemory, JointEstimatorV5, CrossCheckRule, FG, _beta_log, FLAG_KINDS
from .selfcal import PG, QG, _E
from .strategies import REGISTRY

SG = np.linspace(0.0, 0.6, 13)                      # sigma grid
_Q3 = QG[0][:, None, None]
_F3 = FG[None, :, None]
_S3 = SG[None, None, :]


class CheckerMemoryS(CheckerMemory):
    def __init__(self, rho, q_mean=0.5, q_strength=2.0, f_mean=0.1, f_strength=2.0, s_mean=0.1, s_strength=2.0):
        super().__init__(rho, q_mean, q_strength, f_mean, f_strength)
        self.lp = self.lp[:, :, None] + _beta_log(_S3 / 0.6, s_mean / 0.6, s_strength)

    def update(self, kind, p, a):
        if kind == "loud":
            return
        r, s = self.rho, (1 - p) * (1 - self.rho)
        if kind == "none":
            L = p * (1 - _F3) + s * (1 - _Q3) + 0 * _S3
        elif kind == "flag_agree":
            L = p * _F3 * a + s * _Q3 * (1 - a) * (1 - r) * _S3
        elif kind == "flag_disagree":
            L = p * _F3 * (1 - a) * (1 - r) + s * _Q3 * (a + (1 - a) * (1 - r) * (1 - _S3))
        else:
            L = p * _F3 + s * _Q3 + 0 * _S3
        self.lp = self.lp + np.log(np.clip(L, _E, None))
        self._w = None
        self.n += 1

    @property
    def q_mean(self):
        return float((self.w.sum(axis=(1, 2)) * _Q3[:, 0, 0]).sum())

    @property
    def f_mean(self):
        return float((self.w.sum(axis=(0, 2)) * FG).sum())

    @property
    def s_mean(self):
        return float((self.w.sum(axis=(0, 1)) * SG).sum())

    def q_logprior(self):
        return np.log(np.clip(self.w.sum(axis=(1, 2)), _E, None))[None, :]


class JointEstimatorV5S(JointEstimatorV5):
    def joint(self):
        if self._cache is not None:
            return self._cache
        r, f, sg = self.rho, self.cm.f_mean, self.cm.s_mean
        P, Q = PG, QG
        S = (1 - P) * (1 - r)
        lp = np.zeros((PG.size, QG.size))
        n_loud = n_un = n_cn = n_unres = 0
        for c, k, a in self.obs:
            if k == "loud":
                n_loud += 1
            elif not c:
                n_un += 1
            elif k == "none":
                n_cn += 1
            elif k == "flag_agree":
                lp = lp + np.log(np.clip(P * f * a + S * Q * (1 - a) * (1 - r) * sg, _E, 1))
            elif k == "flag_disagree":
                lp = lp + np.log(np.clip(P * f * (1 - a) * (1 - r) + S * Q * (a + (1 - a) * (1 - r) * (1 - sg)), _E, 1))
            else:
                n_unres += 1
        lp += n_loud * np.log(np.clip((1 - P) * r, _E, 1)) + n_un * np.log(np.clip(1 - (1 - P) * r, _E, 1))
        lp = lp + n_cn * np.log(np.clip(P * (1 - f) + S * (1 - Q), _E, 1))
        lp = lp + n_unres * np.log(np.clip(P * f + S * Q, _E, 1))
        fade = max(0.0, 1.0 - len(self.obs) / self.window)
        lp = lp + fade * self._lp_p + self.cm.q_logprior()
        lp -= lp.max()
        w = np.exp(lp); w /= w.sum()
        self._cache = w
        return w


class CrossCheckRuleS(CrossCheckRule):
    """Rule v5 with shared mistakes in its model (learns q, f and sigma without labels)."""
    name = "Rule_v5_s"
    rng_name = "Rule_v5_x"                          # same audit draws as rule v5

    def __init__(self, s, rng, window=60, epsilon=0.02, k=3, s_mean=0.1, s_strength=2.0, **kw):
        super().__init__(s, rng, window, epsilon, k, **kw)
        self.cm = CheckerMemoryS(s.rho, kw.get("q_prior_mean", 0.5), kw.get("q_prior_strength", 2.0),
                                 kw.get("f_prior_mean", 0.1), kw.get("f_prior_strength", 2.0), s_mean, s_strength)
        self.ests = [JointEstimatorV5S(window, s.rho, t.advertised_p, s.prior_strength, self.cm) for t in s.tools]


REGISTRY[CrossCheckRuleS.name] = CrossCheckRuleS
