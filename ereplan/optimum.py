"""Perfect-knowledge optimum: the lowest EXPECTED total loss any strategy could achieve on a run if it
knew the hidden success rate of every tool at every step (but not the coin flips of each call).

It is computed exactly, by enumeration, for the same cost rules as runner.py:
  * a step makes up to r_max + 1 attempts; each attempt costs the price (+ check price if checked);
  * a failure is seen if loud (prob rho) or, when checked, caught (prob q); seen failures are retried;
  * an unseen (silent, unchecked or missed) failure is a leak: the task is marked leaked (loss L once);
  * if all attempts fail visibly, the task ends early (no further steps, no leak loss);
  * total loss per task = spend + L * P(task leaked), switching costs c_switch.
The optimum chooses (a) when to switch from the cheap tool to an alternative (at most once; the cheap
tool only gets worse in these scenarios) and (b) which steps of each task to check (all 2^5 patterns).
Because it knows more than any real agent can, it is a LOWER BOUND: real strategies cannot beat it
on average. The gap between a strategy and this bound shows how much room is left.
"""
import itertools
import numpy as np

from .config import Setting
from .env import true_rates


def _step(p, price, check_price, checked, s: Setting):
    """Expected spend, P(leak at this step), P(task ends here by exhausted retries)."""
    d = s.rho + (1 - s.rho) * s.q_true if checked else s.rho
    f = (1 - p) * d                     # P(a failure is seen) per attempt
    r = s.r_max
    per_attempt = price + (check_price if checked else 0.0)
    e_attempts = sum((k + 1) * f**k * (1 - f) for k in range(r + 1)) + (r + 1) * f**(r + 1)
    p_leak = (1 - p) * (1 - d) * sum(f**k for k in range(r + 1))
    p_exhaust = f**(r + 1)
    return per_attempt * e_attempts, p_leak, p_exhaust


def task_loss(steps, s):
    """Min over the 2^S check patterns of expected (spend + L * P(task leaked)) for one task.
    steps: list of (p, price) per step. Leak and exhaustion are exclusive outcomes of a step."""
    best, best_pat = np.inf, None
    for pattern in itertools.product((False, True), repeat=len(steps)):
        a0, a1, spend, leak = 1.0, 0.0, 0.0, 0.0
        for (p, price), chk in zip(steps, pattern):
            e_spend, pl, px = _step(p, price, s.check_price, chk, s)
            spend += (a0 + a1) * e_spend
            leak += a0 * pl
            a0, a1 = a0 * (1 - pl - px), a1 * (1 - px) + a0 * pl
        val = spend + s.leak_loss * leak
        if val < best:
            best, best_pat = val, pattern
    return best


def optimum(s: Setting, scenario: str, seed: int):
    """Return (expected total loss per task, best switch step or None, target tool)."""
    P = true_rates(s, scenario, seed)
    S, n = s.steps_per_task, s.n_tasks
    T = S * n
    price = [s.eff_price(k) for k in range(len(s.tools))]

    def steps_for(task, switch_at, target):
        out = []
        for j in range(S):
            t = task * S + j
            k = 0 if (switch_at is None or t < switch_at) else target
            out.append((P[k, t], price[k]))
        return out

    stay_task = [task_loss(steps_for(i, None, 0), s) for i in range(n)]
    best = (sum(stay_task), None, 0)
    for target in range(1, len(s.tools)):
        alt_task = [task_loss(steps_for(i, 0, target), s) for i in range(n)]
        prefix = np.concatenate([[0.0], np.cumsum(stay_task)])
        suffix = np.concatenate([np.cumsum(alt_task[::-1])[::-1], [0.0]])
        for t_sw in range(T):
            i, j = divmod(t_sw, S)
            mid = alt_task[i] if j == 0 else task_loss(steps_for(i, t_sw, target), s)
            total = prefix[i] + mid + suffix[i + 1] + s.switch_cost
            if total < best[0]:
                best = (total, t_sw, target)
    return best[0] / n, best[1], best[2]
