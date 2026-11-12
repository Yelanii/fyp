"""Core 3 (31 October 2026): exact one-step losses of checking under persistent false alarms.

One step of a task, on one tool. Each attempt costs w (tool price) plus c if it is checked. An attempt is
    correct        with probability p
    loud failure   with probability l = (1-p) rho        (seen for free, the agent retries)
    silent failure with probability s = (1-p)(1-rho)    (looks correct)
A check catches a silent failure with probability q. It flags a correct attempt when the judge's verdict state
I_b = 1. The verdict state follows the two-state chain used by the simulator (env.py):
    I_0 ~ Bernoulli(f);   I_b = I_{b-1} with probability pi, otherwise a fresh Bernoulli(f) draw.
Up to R retries (R + 1 attempts). If every attempt ends in a detected failure, the step fails at cost F.
A silent failure that is accepted costs L.

Policies on the step:
    N  never check
    C  check every attempt, retry on a flag (rules v2-v4, always-check)
    X  check every attempt, cross-check a flag on an alternative tool with success rate a (rule v5):
       agree -> keep the output; disagree -> use the alternative's output; alternative loud -> retry.
       Two wrong outputs never agree.

All three are computed exactly by a forward pass over (attempt b, verdict state I_b); see THEORY_2026-10-31.md.
"""
from dataclasses import dataclass, replace

import numpy as np


@dataclass(frozen=True)
class Step:
    p: float            # success rate of the tool on this step
    w: float = 20.0     # tool price
    c: float = 3.7      # check price
    L: float = 120.0    # loss of an accepted wrong output (leak)
    F: float = 120.0    # loss of a failed step (the task is redone)
    q: float = 0.8      # catch rate
    f: float = 0.15     # false-alarm rate
    pi: float = 1.0     # persistence of the verdict
    rho: float = 0.5    # loud share of failures
    R: int = 2          # retries
    a: float = 0.95     # success rate of the alternative tool (policy X)
    wB: float = 24.0    # price of the alternative tool (policy X)

    def with_(self, **kw):
        return replace(self, **kw)


def _trans(f, pi):
    """P(I_{b+1} = j | I_b = i) for the verdict chain."""
    return np.array([[1 - (1 - pi) * f, (1 - pi) * f],
                     [(1 - pi) * (1 - f), pi + (1 - pi) * f]])


def _forward(st: Step, cost, kappa):
    """Expected loss when attempt b, in verdict state i, costs cost[i] and continues with probability kappa[i]."""
    P = _trans(st.f, st.pi)
    m = np.array([1 - st.f, st.f])          # P(reach attempt 0, I_0 = i)
    total = 0.0
    for b in range(st.R + 1):
        total += float(m @ cost)
        cont = m * kappa
        if b == st.R:
            total += st.F * float(cont.sum())
        else:
            m = cont @ P
    return total


def parts(st: Step):
    l = (1 - st.p) * st.rho
    s = (1 - st.p) * (1 - st.rho)
    return l, s


def loss_never(st: Step) -> float:
    l, s = parts(st)
    return _forward(st, np.full(2, st.w + s * st.L), np.full(2, l))


def loss_check(st: Step) -> float:
    l, s = parts(st)
    cost = np.full(2, st.w + st.c + s * (1 - st.q) * st.L)
    kappa = l + s * st.q + st.p * np.array([0.0, 1.0])
    return _forward(st, cost, kappa)


def loss_cross(st: Step) -> float:
    l, s = parts(st)
    flag = st.p * np.array([0.0, 1.0]) + s * st.q            # P(flag | I) on one attempt
    alt_loud = (1 - st.a) * st.rho
    alt_silent = (1 - st.a) * (1 - st.rho)
    cost = st.w + st.c + s * (1 - st.q) * st.L + flag * (st.wB + alt_silent * st.L)
    kappa = l + flag * alt_loud
    return _forward(st, cost, kappa)


def fail_prob_correct(f, pi, R):
    """P(all R + 1 attempts of a step that is always correct are flagged) = f (f + (1-f) pi)^R."""
    return f * (f + (1 - f) * pi) ** R


def wrong_check_region(st: Step, grid=None):
    """Success rates p at which a rule that assumes independent verdicts (pi = 0) checks, but never checking is
    strictly cheaper under the true persistence st.pi. Returns (grid, mask, excess loss of checking)."""
    grid = np.linspace(0.30, 0.999, 700) if grid is None else grid
    d0 = np.array([loss_check(st.with_(p=p, pi=0.0)) - loss_never(st.with_(p=p)) for p in grid])
    dpi = np.array([loss_check(st.with_(p=p)) - loss_never(st.with_(p=p)) for p in grid])
    mask = (d0 <= 0) & (dpi > 0)
    return grid, mask, dpi, d0
