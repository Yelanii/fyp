"""Simulated environment: hidden success rates over time and pre-drawn tool outcomes.

Common random numbers: for a given (scenario, seed) every strategy faces exactly
the same tool outcomes at the same time step, so differences between strategies
come from their decisions, not from luck (Section 3.3.5.9).
"""
import zlib
import numpy as np

from .config import Setting


def _rng(*parts) -> np.random.Generator:
    key = zlib.crc32("|".join(str(p) for p in parts).encode())
    return np.random.default_rng(key)


def true_rates(setting: Setting, scenario: str, seed: int) -> np.ndarray:
    """Hidden success rate p[k, t] for each tool k and step t (Table 3.12)."""
    T = setting.n_tasks * setting.steps_per_task
    K = len(setting.tools)
    p = np.array([[tool.base_p] * T for tool in setting.tools], dtype=float)
    r = _rng("scenario", scenario, seed)
    a = 0  # the primary (cheapest) tool degrades; alternatives stay stable in the pilot
    if scenario == "S1_sudden":
        t0 = int(r.integers(150, 350))
        p[a, t0:] = 0.60
    elif scenario == "S2_gradual":
        t0 = int(r.integers(100, 200))
        ramp = np.clip((np.arange(T) - t0) / 200.0, 0.0, 1.0)
        p[a] = 0.95 - (0.95 - 0.70) * ramp
    elif scenario == "S3_harmless":
        t0 = int(r.integers(150, 350))
        p[a, t0:] = 0.85
    elif scenario.startswith("drop_"):            # check-worth map: sudden drop to a chosen level
        level = float(scenario.split("_")[1])
        t0 = int(r.integers(150, 350))
        p[a, t0:] = level
    # 21 Nov 2026 (drift test): "ramp_<level>": tool A declines linearly from its base rate to <level> over 200
    # calls, starting at the step where "drop_<level>" drops on the same seed. Only this new name uses it.
    elif scenario.startswith("ramp_"):
        level = float(scenario.split("_")[1])
        t0 = int(_rng("scenario", f"drop_{level:.2f}", seed).integers(150, 350))
        ramp = np.clip((np.arange(T) - t0) / 200.0, 0.0, 1.0)
        p[a] = p[a, 0] - (p[a, 0] - level) * ramp
    # 10 Nov 2026 (boundary map): "pdrop_<level>@p<NN>": tool A drops to <level> in only NN% of runs. Own random
    # streams, so every earlier scenario is unchanged.
    elif scenario.startswith("pdrop_"):
        level, pp = scenario[6:].split("@p")
        rb = _rng("pdrop_scenario", scenario, seed)
        t0 = int(rb.integers(150, 350))
        if rb.random() < int(pp) / 100.0:
            p[a, t0:] = float(level)
    # 10 Nov 2026 (FR18, any tool can degrade): which tool degrades is random, so no tool is reliably better.
    elif scenario.startswith("any_"):
        rn = _rng("any_scenario", scenario, seed)
        order = rn.permutation(K)
        if scenario == "any_one":                 # one tool, chosen at random, drops to 60%
            p[order[0], int(rn.integers(150, 350)):] = 0.60
        elif scenario == "any_two":               # two random tools drop at unrelated times
            p[order[0], int(rn.integers(100, 500)):] = 0.60
            p[order[1], int(rn.integers(100, 500)):] = 0.60
        elif scenario == "any_recover":           # one random tool drops, and is fixed 200 calls later
            t0 = int(rn.integers(100, 300))
            p[order[0], t0:t0 + 200] = 0.60
        else:
            raise ValueError(f"unknown scenario {scenario}")
    # feasibility scenarios (28 Oct 2026, exploratory): the alternative can degrade too. Own random stream, so
    # every earlier scenario is unchanged.
    elif scenario.startswith("alt_"):
        ra = _rng("alt_scenario", scenario, seed)
        t0 = int(ra.integers(150, 350))
        if scenario == "alt_S2_after":          # A degrades; B degrades 50-150 calls later
            p[a, t0:] = 0.60
            p[1, t0 + int(ra.integers(50, 150)):] = 0.60
        elif scenario == "alt_S3_indep":        # A and B degrade at unrelated times
            p[a, int(ra.integers(100, 500)):] = 0.60
            p[1, int(ra.integers(100, 500)):] = 0.60
        elif scenario == "alt_S4_common":       # shared cause: A and B degrade together
            p[a, t0:] = 0.60
            p[1, t0:] = 0.60
        elif scenario == "alt_S5_recover":      # A degrades, then is fixed 200 calls later
            p[a, t0:t0 + 200] = 0.60
        elif scenario == "alt_S1_only_A":       # reference: only A degrades (same draw as the others)
            p[a, t0:] = 0.60
        else:
            raise ValueError(f"unknown scenario {scenario}")
    else:
        raise ValueError(f"unknown scenario {scenario}")
    assert p.shape == (K, T)
    return p


class Environment:
    """Draws every random outcome up front so that all strategies share them."""

    def __init__(self, setting: Setting, scenario: str, seed: int):
        self.s = setting
        self.scenario = scenario
        self.seed = seed
        self.p = true_rates(setting, scenario, seed)
        K, T = self.p.shape
        A = setting.r_max + 1
        r = _rng("outcomes", scenario, seed)
        self.u_success = r.random((K, T, A))
        self.u_loud = r.random((K, T, A))
        self.u_catch = r.random((K, T, A))
        # separate stream, so adding false alarms leaves every earlier random draw unchanged
        self.u_fa = _rng("falsealarm", scenario, seed).random((T, A))
        # partial persistence (24 Oct 2026): with probability pi a retry repeats the previous verdict on the
        # step, otherwise it draws afresh. pi = 1 and pi = 0 reproduce the persistent and independent cases
        # exactly, because new streams are used only when 0 < pi < 1.
        self.pi = setting.pi_true
        if 0.0 < self.pi < 1.0:
            up = _rng("fapersist", scenario, seed).random((T, A))
            ue = self.u_fa.copy()
            for a in range(1, A):
                ue[:, a] = np.where(up[:, a] < self.pi, ue[:, a - 1], self.u_fa[:, a])
            self.u_fa_eff = ue
        # re-verification of the SAME output (used only by strategies that re-ask the checker)
        KR = 3
        self.u_rp = _rng("recheck_persist", scenario, seed).random((T, A, KR))
        self.u_rf = _rng("recheck_fresh", scenario, seed).random((K, T, A, KR))
        # drift test (21 Nov 2026): the step at which the checker's rates change. Own random stream, drawn only
        # when a late rate is set (Setting.q_late, f_late), so every earlier run is unchanged.
        self.t_drift = None
        if getattr(setting, "q_late", -1.0) >= 0 or getattr(setting, "f_late", -1.0) >= 0:
            self.t_drift = int(_rng("checker_drift", scenario, seed).integers(200, 400))

    def f_at(self, t: int) -> float:
        """The checker's false-alarm rate at step t (it changes once if Setting.f_late is set)."""
        if getattr(self, "t_drift", None) is not None and t >= self.t_drift and self.s.f_late >= 0:
            return self.s.f_late
        return self.s.false_alarm

    def q_at(self, t: int) -> float:
        """The checker's catch rate at step t (it changes once if Setting.q_late is set)."""
        if getattr(self, "t_drift", None) is not None and t >= self.t_drift and self.s.q_late >= 0:
            return self.s.q_late
        return self.s.q_true

    @property
    def T(self) -> int:
        return self.p.shape[1]

    def call(self, k: int, t: int, attempt: int, checked: bool) -> str:
        """Outcome of one attempt: 'ok', 'loud', 'caught' (silent, caught by a check), 'leak', or
        'false_alarm' (correct, but the check wrongly flags it; the agent cannot tell it from 'caught')."""
        if self.u_success[k, t, attempt] < self.p[k, t]:
            f_t = self.f_at(t)
            if checked and f_t > 0:
                if self.pi >= 1.0:
                    u = self.u_fa[t, 0]
                elif self.pi <= 0.0:
                    u = self.u_fa[t, attempt]
                else:
                    u = self.u_fa_eff[t, attempt]
                if u < f_t:
                    return "false_alarm"            # correct result, but the check flags it
            return "ok"
        if self.u_loud[k, t, attempt] < self.s.rho:
            return "loud"
        q_eff = self.q_at(t)
        if self.s.check_corr > 0 and self.p[k, t] < self.s.tools[k].base_p - 1e-9:
            q_eff = q_eff * (1.0 - self.s.check_corr)
        if checked and self.u_catch[k, t, attempt] < q_eff:
            return "caught"
        return "leak"

    def _q_eff(self, k: int, t: int) -> float:
        q = self.q_at(t)
        if self.s.check_corr > 0 and self.p[k, t] < self.s.tools[k].base_p - 1e-9:
            return q * (1.0 - self.s.check_corr)
        return q

    def third_source(self, t: int, attempt: int, truly_correct: bool, shared_event: bool) -> bool:
        """FR19: an independent third source (a different model family) judges the SAME output the two-source
        cross-check already judged. Returns True if the third source sees it as correct, False if it flags it.

        If truly_correct, it raises its own false alarm with probability s.false_alarm (same rate as the other
        checks). If the output is truly wrong AND the two-source comparison already agreed on it only because of
        a shared cause (shared_event=True, i.e. the Core 4 xc_shared draw fired for this call), the third source
        reproduces that same mistake with probability s.third_shared (believed lower than xc_shared, because it
        is a different model family) -- otherwise, for a truly wrong output, it is an independent check with its
        own catch rate s.third_q (s.q_true if not set).
        """
        u = _rng("third", self.scenario, self.seed, t, attempt).random()
        if truly_correct:
            return u >= self.f_at(t)
        if shared_event:
            return u < self.s.third_shared
        q3 = self.s.third_q if self.s.third_q >= 0 else self.q_at(t)
        return u >= q3

    def recheck(self, k: int, t: int, attempt: int, j: int, prev_flag: bool, truly_correct: bool) -> bool:
        """Verdict of the j-th re-check (j = 1, 2, ...) of the output already produced by this attempt.
        With probability pi the checker repeats its previous verdict (a deterministic judge re-reads the same
        input); otherwise it judges afresh (false-alarm rate f if the output is correct, catch rate q if not)."""
        if self.u_rp[t, attempt, j - 1] < self.pi:
            return prev_flag
        u = self.u_rf[k, t, attempt, j - 1]
        return bool(u < (self.f_at(t) if truly_correct else self._q_eff(k, t)))

