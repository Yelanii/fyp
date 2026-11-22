"""Rule v5: a label-free, cross-checking rule.

Problem it solves: rule v4 must be TOLD the checker's catch rate q and false-alarm
rate f, measured on labelled calibration tasks, and it handles a flag by retrying the same tool, so a checker that
repeats its false alarms fails correct work.

Two changes:
 1. Cross-check instead of retry. When a check flags a step, the agent runs the same step on the best alternative
    tool and compares the two outputs.
      - they agree       -> the flag was a false alarm; the original output is kept (no retry, no failed task);
      - they disagree    -> the alternative's output is used (the agent cannot tell which one is wrong, but the
                            flagged one is more likely wrong);
      - alternative loud -> no comparison; the agent retries as before.
    Wrong outputs on two different tools are assumed never to coincide (true for numeric answers).
 2. Learn the checker without labels. Agreement after a flag is a free label ("that flag was false"), and
    disagreement is evidence of a real catch. A posterior over (q, f) for the checker is kept from ALL checked calls
    (the checker does not drift in this model), and each tool's success rate is estimated with it. Nothing about q or
    f is told to the rule: it starts from vague priors.

Per checked call (p = tool success rate, a = alternative tool success rate, rho = loud share):
    loud              (1-p) rho
    none              p (1-f) + (1-p)(1-rho)(1-q)
    flag, agree       p f a
    flag, disagree    p f (1-a)(1-rho) + (1-p)(1-rho) q (1 - (1-a) rho)
    flag, alt loud    (p f + (1-p)(1-rho) q) (1-a) rho
Approximations (stated in PREREGISTRATION_v5.md): plug-in estimates of p and a when updating (q, f); the (q, f)
posterior is used as a prior for the windowed success-rate estimate, so recent checked calls count twice for q.
"""
import os
import numpy as np

from .selfcal import JointEstimator, SelfCalibratingRule, PG, QG, _E
from .strategies import CheckAlways, REGISTRY

# EREPLAN_NETPV=1 switches every cross-checking rule to the corrected (net) check criterion.
NETPV = os.environ.get("EREPLAN_NETPV") == "1"

import os as _os
# False-alarm grid. Default 0..0.5 (the simulator experiments). Real FreshQA judges have f up to about 0.8,
# so that experiment sets EREPLAN_FMAX=0.95; the step stays 0.02 and every earlier result is unchanged.
FMAX = float(_os.environ.get("EREPLAN_FMAX", "0.5"))
FG = np.linspace(0.0, FMAX, int(round(FMAX / 0.02)) + 1)
_Q = QG[0][:, None]                     # (41, 1)
_F = FG[None, :]                        # (1, n_f)
FLAG_KINDS = ("caught", "flag_agree", "flag_disagree", "flag_altloud")


def _beta_log(grid, mean, strength):
    a = max(mean * strength, 1.0); b = max((1 - mean) * strength, 1.0)
    return (a - 1) * np.log(np.clip(grid, _E, 1)) + (b - 1) * np.log(np.clip(1 - grid, _E, 1))


class CheckerMemory:
    """Posterior over the checker's (q, f), shared by all tools. fixed=(q, f) gives a point mass (the 'told' rule)."""

    def __init__(self, rho, q_mean=0.5, q_strength=2.0, f_mean=0.1, f_strength=2.0, fixed=None, f_ab=None):
        self.rho = rho
        if fixed is not None:
            lp = np.full((len(_Q), FG.size), -np.inf)
            lp[int(np.argmin(np.abs(_Q[:, 0] - fixed[0]))), int(np.argmin(np.abs(FG - fixed[1])))] = 0.0
            self.fixed = True
        else:
            if f_ab is None:
                lp = _beta_log(_Q, q_mean, q_strength) + _beta_log(_F / FMAX, f_mean / FMAX, f_strength)
            else:                               # Beta(a, b) on f / FMAX given directly, with no floor on a or b
                a, b = f_ab
                lp = _beta_log(_Q, q_mean, q_strength) + ((a - 1) * np.log(np.clip(_F / FMAX, _E, 1))
                                                          + (b - 1) * np.log(np.clip(1 - _F / FMAX, _E, 1)))
            self.fixed = False
        self.lp = lp
        self._w = None
        self.n = 0

    def update(self, kind, p, a):
        if self.fixed or kind == "loud":
            return
        r = self.rho
        if kind == "none":
            L = p * (1 - _F) + (1 - p) * (1 - r) * (1 - _Q)
        elif kind == "flag_agree":
            L = p * _F * a + 0 * _Q
        elif kind == "flag_disagree":
            L = p * _F * (1 - a) * (1 - r) + (1 - p) * (1 - r) * _Q * (1 - (1 - a) * r)
        else:                                   # "caught" or "flag_altloud": a flag that was not resolved
            L = p * _F + (1 - p) * (1 - r) * _Q
        self.lp = self.lp + np.log(np.clip(L, _E, None))
        self._w = None
        self.n += 1

    @property
    def w(self):
        if self._w is None:
            lp = self.lp - self.lp.max()
            w = np.exp(lp); self._w = w / w.sum()
        return self._w

    @property
    def q_mean(self):
        return float((self.w.sum(axis=1) * _Q[:, 0]).sum())

    @property
    def f_mean(self):
        return float((self.w.sum(axis=0) * FG).sum())

    def q_logprior(self):
        """Log of the (q) marginal on the estimator's q grid (row vector)."""
        return np.log(np.clip(self.w.sum(axis=1), _E, None))[None, :]


class JointEstimatorV5(JointEstimator):
    """Windowed posterior over (p, q) for one tool; f is the checker memory's current mean, q's prior is its marginal."""

    def __init__(self, window, rho, p_prior_mean, p_prior_strength, cm: CheckerMemory):
        super().__init__(window, rho, 0.5, 1.0, p_prior_mean, p_prior_strength)
        self.cm = cm

    def update(self, checked, kind, a=0.95):
        self.obs.append((bool(checked), kind, float(a)))
        self._cache = None

    def invalidate(self):
        self._cache = None

    def joint(self):
        if self._cache is not None:
            return self._cache
        r, f = self.rho, self.cm.f_mean
        P, Q = PG, QG
        lp = np.zeros((PG.size, QG.size))
        n_loud = n_un = n_cn = n_unres = 0
        agree_a, dis_a = [], []
        for c, k, a in self.obs:
            if k == "loud":
                n_loud += 1
            elif not c:
                n_un += 1
            elif k == "none":
                n_cn += 1
            elif k == "flag_agree":
                agree_a.append(a)
            elif k == "flag_disagree":
                dis_a.append(a)
            else:
                n_unres += 1
        lp += n_loud * np.log(np.clip((1 - P) * r, _E, 1)) + n_un * np.log(np.clip(1 - (1 - P) * r, _E, 1))
        lp = lp + n_cn * np.log(np.clip(P * (1 - f) + (1 - P) * (1 - r) * (1 - Q), _E, 1))
        lp = lp + n_unres * np.log(np.clip(P * f + (1 - P) * (1 - r) * Q, _E, 1))
        for a in agree_a:
            lp = lp + np.log(np.clip(P * f * a, _E, 1))
        for a in dis_a:
            lp = lp + np.log(np.clip(P * f * (1 - a) * (1 - r) + (1 - P) * (1 - r) * Q * (1 - (1 - a) * r), _E, 1))
        fade = max(0.0, 1.0 - len(self.obs) / self.window)
        lp = lp + fade * self._lp_p + self.cm.q_logprior()
        lp -= lp.max()
        w = np.exp(lp); w /= w.sum()
        self._cache = w
        return w


class CrossCheckRule(SelfCalibratingRule):
    """Rule v5: learns (q, f) without labels and cross-checks flagged steps on the alternative tool."""
    name = "Rule_v5_x"
    crosscheck = True

    def __init__(self, s, rng, window=60, epsilon=0.02, k=3, told=False,
                 q_prior_mean=0.5, q_prior_strength=2.0, f_prior_mean=0.1, f_prior_strength=2.0, f_prior_matched=False):
        super().__init__(s, rng, window, epsilon, k, q_prior_strength)
        fixed = (s.q_assumed, s.f_assumed) if told else None
        # f_prior_matched: a weak prior whose mean really is f_prior_mean on the f grid. The default prior floors
        # each Beta parameter at 1, which moves its mean from 0.1 to about 0.19 (FMAX 0.5) or 0.33 (FMAX 0.95).
        f_ab = (1.0, FMAX / f_prior_mean - 1.0) if f_prior_matched else None
        self.cm = CheckerMemory(s.rho, q_prior_mean, q_prior_strength, f_prior_mean, f_prior_strength, fixed=fixed, f_ab=f_ab)
        self.ests = [JointEstimatorV5(window, s.rho, t.advertised_p, s.prior_strength, self.cm) for t in s.tools]

    # ---- cross-check hooks used by the runner
    def crosscheck_tool(self, ctx):
        return self.line(ctx)[1]

    def alt_mean(self, j):
        return self.ests[j].mean

    def observe(self, k, checked, failure_seen, kind=None, a=None):
        kind = kind if kind is not None else ("loud" if failure_seen else "none")
        if kind not in ("loud",) + FLAG_KINDS:
            kind = "none"                           # 'ok' and 'leak' look the same to the agent: nothing seen
        if a is None:
            a = max(self.ests[j].mean for j in range(len(self.s.tools)) if j != k)
        if checked:
            self.cm.update(kind, self.ests[k].mean, a)
            for e in self.ests:
                e.invalidate()
        self.ests[k].update(checked, kind, a)

    # ---- deciding
    def fa_cost(self, mean, ctx):
        """Expected extra cost of a false alarm under cross-checking: one call on the alternative, plus a leak if the
        alternative is silently wrong (its answer is then used), plus one retry if the alternative fails loudly."""
        s, j = self.s, self.crosscheck_tool(ctx)
        a = self.ests[j].mean
        f = self.cm.f_mean
        return mean * f * (s.eff_price(j) + (1 - a) * (1 - s.rho) * s.leak_loss
                           + (1 - a) * s.rho * (s.eff_price(ctx["cur"]) + s.check_price))

    # Net protection value. With net = False the rule is exactly the one evaluated before the correction:
    # it counts the whole wrong-answer loss as saved by a catch (gross PV). With net = True it also subtracts the
    # cost of resolving a caught failure by the cross-check, q s R, which is the consistent one-step criterion
    #     q s (L - R) + DV - p f R >= check price,   s = (1-p)(1-rho),
    # where R is the same resolution cost that the false-alarm term uses. See PREREGISTRATION_netpv.md.
    net = NETPV

    def resolve_cost(self, ctx):
        """R: expected cost of resolving one flag by a cross-check (alternative call; wrong answer if the
        alternative is silently wrong; one retry if it fails loudly)."""
        s, j = self.s, self.crosscheck_tool(ctx)
        a = self.ests[j].mean
        return (s.eff_price(j) + (1 - a) * (1 - s.rho) * s.leak_loss
                + (1 - a) * s.rho * (s.eff_price(ctx["cur"]) + s.check_price))

    def wants_check(self, ctx, line, mean, low, high):
        want = super().wants_check(ctx, line, mean, low, high)
        tr = ctx["trace"]
        fa = self.fa_cost(mean, ctx)
        tr.update(fa_cost=fa, f_hat=self.cm.f_mean, q_hat_cm=self.cm.q_mean)
        tr["reason"] += f"; learned f {self.cm.f_mean:.2f}; false-alarm cost {fa:.1f}"
        catch_cost = 0.0
        if self.net:
            q = tr["pv"] / max((1 - mean) * (1 - self.s.rho) * self.s.leak_loss, 1e-12)   # the q used for PV
            catch_cost = q * (1 - mean) * (1 - self.s.rho) * self.resolve_cost(ctx)
            tr.update(pv_net=tr["pv"] - catch_cost)
        return (tr["pv"] - catch_cost + tr["dv"] - fa) >= self.s.check_price or tr["audit"]


class CrossCheckRuleNet(CrossCheckRule):
    """Rule v5 with the net protection value, whatever the EREPLAN_NETPV setting (used by run_netpv.py to compare
    the corrected rule with the evaluated one in the same run)."""
    name = "Rule_v5_net"
    rng_name = "Rule_v5_x"
    net = True


class CrossCheckRuleSym(CrossCheckRule):
    """The corrected rule (net PV) whose decision value prices staying with the same per-call cost as the switch line,
    c/p + (1-p)(1-rho)L, so both sides of the keep-or-switch comparison count wrong answers (PREREGISTRATION_dvsym.md)."""
    name = "Rule_v5_sym"
    rng_name = "Rule_v5_x"
    net = True
    dv_sym = True


class CrossCheckRuleExact(CrossCheckRule):
    """The corrected rule (net PV) whose switch line and decision value price a planned step with its exact loss
    under the failure model (loud failures retried up to r_max times, silent ones accepted), instead of c/p
    (PREREGISTRATION_exactline.md)."""
    name = "Rule_v5_exact"
    rng_name = "Rule_v5_x"
    net = True
    exact_line = True


class CrossCheckRuleTold(CrossCheckRule):
    """Ablation: rule v5's cross-check policy, but TOLD q and f (as rule v4 is). Isolates the value of learning."""
    name = "Rule_v5_told"
    rng_name = "Rule_v5_x"

    def __init__(self, s, rng, **kw):
        kw["told"] = True
        super().__init__(s, rng, **kw)


class AlwaysCrossCheck(CheckAlways):
    """Baseline: check every call; cross-check every flag on the alternative."""
    name = "B12_always_x"
    crosscheck = True

    def crosscheck_tool(self, ctx):
        return self.line(ctx)[1]

    def alt_mean(self, j):
        return self.ests[j].mean

    def observe(self, k, checked, failure_seen, kind=None, a=None):
        if kind in ("flag_agree",):
            failure_seen = False
        super().observe(k, checked, failure_seen, kind)


for _cls in (CrossCheckRule, CrossCheckRuleNet, CrossCheckRuleSym, CrossCheckRuleExact, CrossCheckRuleTold, AlwaysCrossCheck):
    REGISTRY[_cls.name] = _cls
