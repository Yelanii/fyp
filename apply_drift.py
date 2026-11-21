"""Adds two options to the simulator, in place, for the drift test (PREREGISTRATION_drift.md):

1. a scenario "ramp_<level>": tool A declines linearly to <level> over 200 calls instead of dropping at once;
2. a checker whose rates change once during a run (Setting.q_late, Setting.f_late; off by default).

Run once from the repository root:  python apply_drift.py
It changes ereplan/config.py and ereplan/env.py and nothing else. Both options are off unless a run asks for them,
and they use their own random streams, so every earlier result is unchanged (python reproduce_paper.py checks this).
Running it twice is safe (it stops if the change is already there).
"""
import sys


def load(path, marker, edits):
    raw = open(path, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    s = raw.replace("\r\n", "\n")
    if marker in s:
        return None
    for old, new in edits:
        if s.count(old) != 1:
            sys.exit(f"{path}: could not find this text exactly once, so nothing was changed:\n{old}")
    for old, new in edits:
        s = s.replace(old, new)
    return s.replace("\n", nl)


CONFIG = [
    ('    audit_price: float = -1.0        # price of one audited label; -1 means "same as mean_price"\n',
     '    audit_price: float = -1.0        # price of one audited label; -1 means "same as mean_price"\n'
     '    # --- drift test (21 Nov 2026): the checker\'s rates change once during a run, at a step drawn per run from\n'
     '    # its own random stream (Environment.t_drift). -1 keeps the rate unchanged, so every earlier run is unchanged.\n'
     '    q_late: float = -1.0             # catch rate from the change on\n'
     '    f_late: float = -1.0             # false-alarm rate from the change on\n'),
]

ENV = [
    ('    elif scenario.startswith("drop_"):            # check-worth map: sudden drop to a chosen level\n'
     '        level = float(scenario.split("_")[1])\n'
     '        t0 = int(r.integers(150, 350))\n'
     '        p[a, t0:] = level\n',
     '    elif scenario.startswith("drop_"):            # check-worth map: sudden drop to a chosen level\n'
     '        level = float(scenario.split("_")[1])\n'
     '        t0 = int(r.integers(150, 350))\n'
     '        p[a, t0:] = level\n'
     '    # 21 Nov 2026 (drift test): "ramp_<level>": tool A declines linearly from its base rate to <level> over 200\n'
     '    # calls, starting at the step where "drop_<level>" drops on the same seed. Only this new name uses it.\n'
     '    elif scenario.startswith("ramp_"):\n'
     '        level = float(scenario.split("_")[1])\n'
     '        t0 = int(_rng("scenario", f"drop_{level:.2f}", seed).integers(150, 350))\n'
     '        ramp = np.clip((np.arange(T) - t0) / 200.0, 0.0, 1.0)\n'
     '        p[a] = p[a, 0] - (p[a, 0] - level) * ramp\n'),
    ('        self.u_rf = _rng("recheck_fresh", scenario, seed).random((K, T, A, KR))\n',
     '        self.u_rf = _rng("recheck_fresh", scenario, seed).random((K, T, A, KR))\n'
     '        # drift test (21 Nov 2026): the step at which the checker\'s rates change. Own random stream, drawn only\n'
     '        # when a late rate is set (Setting.q_late, f_late), so every earlier run is unchanged.\n'
     '        self.t_drift = None\n'
     '        if getattr(setting, "q_late", -1.0) >= 0 or getattr(setting, "f_late", -1.0) >= 0:\n'
     '            self.t_drift = int(_rng("checker_drift", scenario, seed).integers(200, 400))\n'
     '\n'
     '    def f_at(self, t: int) -> float:\n'
     '        """The checker\'s false-alarm rate at step t (it changes once if Setting.f_late is set)."""\n'
     '        if getattr(self, "t_drift", None) is not None and t >= self.t_drift and self.s.f_late >= 0:\n'
     '            return self.s.f_late\n'
     '        return self.s.false_alarm\n'
     '\n'
     '    def q_at(self, t: int) -> float:\n'
     '        """The checker\'s catch rate at step t (it changes once if Setting.q_late is set)."""\n'
     '        if getattr(self, "t_drift", None) is not None and t >= self.t_drift and self.s.q_late >= 0:\n'
     '            return self.s.q_late\n'
     '        return self.s.q_true\n'),
    ('        if self.u_success[k, t, attempt] < self.p[k, t]:\n'
     '            if checked and self.s.false_alarm > 0:\n',
     '        if self.u_success[k, t, attempt] < self.p[k, t]:\n'
     '            f_t = self.f_at(t)\n'
     '            if checked and f_t > 0:\n'),
    ('                if u < self.s.false_alarm:\n'
     '                    return "false_alarm"            # correct result, but the check flags it\n',
     '                if u < f_t:\n'
     '                    return "false_alarm"            # correct result, but the check flags it\n'),
    ('        q_eff = self.s.q_true\n'
     '        if self.s.check_corr > 0 and self.p[k, t] < self.s.tools[k].base_p - 1e-9:\n'
     '            q_eff = self.s.q_true * (1.0 - self.s.check_corr)\n',
     '        q_eff = self.q_at(t)\n'
     '        if self.s.check_corr > 0 and self.p[k, t] < self.s.tools[k].base_p - 1e-9:\n'
     '            q_eff = q_eff * (1.0 - self.s.check_corr)\n'),
    ('    def _q_eff(self, k: int, t: int) -> float:\n'
     '        if self.s.check_corr > 0 and self.p[k, t] < self.s.tools[k].base_p - 1e-9:\n'
     '            return self.s.q_true * (1.0 - self.s.check_corr)\n'
     '        return self.s.q_true\n',
     '    def _q_eff(self, k: int, t: int) -> float:\n'
     '        q = self.q_at(t)\n'
     '        if self.s.check_corr > 0 and self.p[k, t] < self.s.tools[k].base_p - 1e-9:\n'
     '            return q * (1.0 - self.s.check_corr)\n'
     '        return q\n'),
    ('            return u >= self.s.false_alarm\n',
     '            return u >= self.f_at(t)\n'),
    ('        q3 = self.s.third_q if self.s.third_q >= 0 else self.s.q_true\n',
     '        q3 = self.s.third_q if self.s.third_q >= 0 else self.q_at(t)\n'),
    ('        return bool(u < (self.s.false_alarm if truly_correct else self._q_eff(k, t)))\n',
     '        return bool(u < (self.f_at(t) if truly_correct else self._q_eff(k, t)))\n'),
]

if __name__ == "__main__":
    # check both files first, then write both, so a failed check changes nothing
    todo = [(p, load(p, m, e)) for p, m, e in (("ereplan/config.py", "q_late: float", CONFIG),
                                                ("ereplan/env.py", "def f_at(self", ENV))]
    for path, text in todo:
        if text is None:
            print(f"{path}: already applied")
        else:
            open(path, "wb").write(text.encode("utf-8"))
            print(f"{path}: applied")
