"""Core 2 (31 October 2026): baselines from three recent outside methods, adapted to the simulator.

Each class adapts one published method. What is kept and what had to change is listed here, so a reader can judge
fairness. Their free parameters are tuned on development seeds (core2_exp.py), while rules v4 and v5 keep the
parameters frozen since October; this favours the baselines, not our rules.

B13_ssv        Selective Strong Verification (Kiyani, Noorani, Pappas and Hassani, 2026, ICML; Algorithm 1, Thm 5.1).
               Weak verifier = our cheap check, so the weak score is binary: w = 1 (no flag) or 0 (flag).
               Strong verifier = a cross-check on the best alternative tool (agree -> g = 1, disagree -> g = 0);
               the paper takes g as the reference, here g is itself imperfect (an alternative can be wrong).
               Three regions with thresholds tau_R <= tau_A: accept if w > tau_A, reject (retry) if w < tau_R,
               otherwise strong verification. In the decisive regions the strong verifier is still queried with
               probability qx (randomised exploration). Updates, as in Algorithm 1, only when g is observed:
                 tau_A <- max(tau_R, tau_A + eta 1{g=0} (1{w > tau_A} - alpha) / q_t)
                 tau_R <- min(tau_A, tau_R + eta 1{g=1} (beta - 1{w < tau_R}) / q_t)
               Starts at tau_R = tau_A = 0.5: accept unflagged outputs and retry flagged ones (the usual policy).
               SSV decides verification only; tool switching uses the shared switch line (as B9 does).
B14_rdecusum   Robust data-efficient CUSUM with sampling control (Hou, Bidkhori and Banerjee, 2024, arXiv:2412.20207,
               Section 3, Eqs. 3.1-3.3). A paid check is the 'sample'. While the statistic D >= 0 the next call is
               checked and D <- max(D + llr, -h); while D < 0 the call is not checked and D <- min(D + mu, 0).
               Alarm when D >= A -> switch to the next tool (as B4). Post-change family: success rate <= p1; the
               least favourable law is p1. It is TOLD q and f, which enter the likelihoods. As in the paper,
               skipped (unchecked) calls are not used by the statistic.
B15_glrklucb   GLR-klUCB (Besson, Kaufmann, Maillard and Seznec, 2022, JMLR 23(77); Algorithm 1, Eq. 2, Section 6.1).
               Bandit over tools: kl-UCB index with exploration function log(t - tau_a), forced round-robin
               exploration with alpha_k = alpha0 sqrt(k K log T / T), Bernoulli GLR test with threshold
               log(n^1.5 / delta), delta = 1 / sqrt(T), tested every 10 observations on change points every 5
               (as in the paper's experiments), local restart. Adaptations: the 'reward' is 'no failure seen',
               feedback comes from loud failures and from checks bought at a fixed rate (as B10), every flag counts
               as a failure, and the arm is chosen by lowest optimistic price per success (price / UCB) plus the
               switching cost spread over a task, since the bandit has no prices of its own.
"""
import math
import numpy as np

from .strategies import Strategy, CheckAlways, REGISTRY


# --------------------------------------------------------------------------- B13: SSV (Kiyani et al., 2026)
class SSVStyle(CheckAlways):
    name = "B13_ssv"
    ssv = True

    def __init__(self, s, rng, window=30, alpha=0.05, beta=0.05, eta=0.05, qx=0.1, tau0=0.5):
        super().__init__(s, rng, window)
        self.alpha, self.beta, self.eta, self.qx = float(alpha), float(beta), float(eta), float(qx)
        self.tA = self.tR = float(tau0)
        self._w = self._q = None

    def crosscheck_tool(self, ctx):
        return self.line(ctx)[1]

    def alt_mean(self, j):
        return self.ests[j].mean

    def ssv_action(self, k, flagged):
        w = 0.0 if flagged else 1.0
        if w > self.tA:
            act, q = "A", self.qx
            if self.rng.random() < self.qx:
                act = "SV"
        elif w < self.tR:
            act, q = "R", self.qx
            if self.rng.random() < self.qx:
                act = "SV"
        else:
            act, q = "SV", 1.0
        self._w, self._q = w, q
        return act

    def ssv_feedback(self, g):
        w, q, e = self._w, self._q, self.eta
        tA = max(self.tR, self.tA + e * (g == 0) * ((w > self.tA) - self.alpha) / q)
        tR = min(tA, self.tR + e * (g == 1) * (self.beta - (w < self.tR)) / q)
        self.tA, self.tR = tA, tR


# --------------------------------------------------------------------------- B14: RDE-CUSUM (Hou et al., 2024)
class RDECusum(Strategy):
    name = "B14_rdecusum"

    def __init__(self, s, rng, window=60, A=4.0, mu=0.1, h=2.0, p1=0.80):
        super().__init__(s, rng, window)
        self.A, self.mu, self.h, self.p1 = float(A), float(mu), float(h), float(p1)
        self.D = 0.0
        self.current = None
        self.alarmed = set()

    def start_task(self, ctx):
        if self.current is None:
            self.current = super().start_task(ctx)
        return self.current

    def _probs(self, k):
        """P(a checked call shows a failure) before (p0) and after (p1) the change, with the told q and f."""
        s = self.s
        d = s.rho + (1 - s.rho) * s.q_assumed
        f = s.f_assumed
        p0 = s.tools[k].advertised_p
        return (1 - p0) * d + p0 * f, (1 - self.p1) * d + self.p1 * f

    def observe(self, k, checked, failure_seen, kind=None):
        super().observe(k, checked, failure_seen)
        if k != self.current:
            return
        if checked:
            f0, f1 = self._probs(k)
            llr = math.log(f1 / f0) if failure_seen else math.log((1 - f1) / (1 - f0))
            self.D = max(self.D + llr, -self.h)
        # unchecked calls: the skip update is applied once per call in decide()

    def decide(self, ctx, allow_switch=True):
        line, _, _ = self.line(ctx)
        mean, low, high = self.ests[ctx["cur"]].summary()
        ctx["trace"] = dict(line=line, mean=mean, low=low, high=high, rde=self.D)
        if allow_switch and self.D >= self.A:
            return "switch"
        if self.D >= 0:
            return "call_and_check"
        self.D = min(self.D + self.mu, 0.0)
        return "call"

    def switch_to(self, ctx):
        self.alarmed.add(ctx["cur"])
        options = [j for j in range(len(self.s.tools)) if j not in self.alarmed] or \
                  [j for j in range(len(self.s.tools)) if j != ctx["cur"]]
        new = min(options, key=lambda j: self.s.eff_price(j) / self.s.tools[j].advertised_p)
        self.current, self.D = new, 0.0
        return new


# --------------------------------------------------------------------------- B15: GLR-klUCB (Besson et al., 2022)
def _kl(x, y, eps=1e-12):
    x = min(max(x, eps), 1 - eps); y = min(max(y, eps), 1 - eps)
    return x * math.log(x / y) + (1 - x) * math.log((1 - x) / (1 - y))


def kl_ucb(mean, n, bound):
    """max{q : n kl(mean, q) <= bound}, by bisection."""
    if n == 0:
        return 1.0
    lo, hi = mean, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if n * _kl(mean, mid) > bound:
            hi = mid
        else:
            lo = mid
    return lo


def glr_detect(x, delta, ds=5):
    """Bernoulli GLR test (Besson et al., 2022, Eq. 2) on the observations x since the last restart."""
    n = len(x)
    if n < 2 * ds:
        return False
    c = np.cumsum(x)
    mu = c[-1] / n
    thr = math.log(n ** 1.5 / delta)
    for s_ in range(ds, n - 1, ds):
        m1 = c[s_ - 1] / s_
        m2 = (c[-1] - c[s_ - 1]) / (n - s_)
        if s_ * _kl(m1, mu) + (n - s_) * _kl(m2, mu) >= thr:
            return True
    return False


class GLRklUCB(Strategy):
    name = "B15_glrklucb"

    def __init__(self, s, rng, window=60, alpha0=1.0, check_rate=0.2, dn=10, ds=5):
        super().__init__(s, rng, window)
        K = len(s.tools)
        self.T = s.n_tasks * s.steps_per_task
        self.alpha0, self.check_rate, self.dn, self.ds = float(alpha0), float(check_rate), int(dn), int(ds)
        self.delta = 1.0 / math.sqrt(self.T)
        self.obs = [[] for _ in range(K)]
        self.tau = [0] * K
        self.k_restarts = 1
        self.t = 0
        self._target = None

    def _alpha(self):
        K = len(self.s.tools)
        return min(1.0, self.alpha0 * math.sqrt(self.k_restarts * K * math.log(self.T) / self.T))

    def observe(self, k, checked, failure_seen, kind=None):
        super().observe(k, checked, failure_seen)
        self.obs[k].append(0.0 if failure_seen else 1.0)
        if len(self.obs[k]) % self.dn == 0 and glr_detect(np.array(self.obs[k]), self.delta, self.ds):
            self.obs[k] = []                       # local restart
            self.tau[k] = self.t
            self.k_restarts += 1

    def _choice(self, cur):
        K = len(self.s.tools)
        period = max(K, int(K / self._alpha()))
        r = self.t % period
        if r < K:                                  # forced round-robin exploration
            return r
        S = self.s.steps_per_task
        best, bs = cur, math.inf
        for j in range(K):
            n = len(self.obs[j])
            m = float(np.mean(self.obs[j])) if n else 1.0
            ucb = kl_ucb(m, n, math.log(max(self.t - self.tau[j], 2)))
            score = self.s.eff_price(j) / max(ucb, 1e-6) + (self.s.switch_cost / S if j != cur else 0.0)
            if score < bs:
                best, bs = j, score
        return best

    def decide(self, ctx, allow_switch=True):
        cur = ctx["cur"]
        ctx["trace"] = {}
        if allow_switch:
            self.t += 1
            best = self._choice(cur)
            if best != cur:
                self._target = best
                return "switch"
        return "call_and_check" if self.rng.random() < self.check_rate else "call"

    def switch_to(self, ctx):
        self.current = self._target
        return self.current


for _cls in (SSVStyle, RDECusum, GLRklUCB):
    REGISTRY[_cls.name] = _cls
