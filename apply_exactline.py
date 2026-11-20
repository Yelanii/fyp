"""Adds the exact-step-cost rule variant (PREREGISTRATION_exactline.md) to ereplan/strategies.py, ereplan/selfcal.py
and ereplan/crosscheck.py. Run once from the repository root, then run the tests. The new variant is OFF by
default, so every existing rule and every earlier result is unchanged.

The evaluated rule prices a tool, in its switch line and in its decision value, at c/p (+ wrong answers), which
assumes a call is retried until it succeeds. In the model only LOUD failures are retried (up to r_max times) and
silent failures are accepted. The variant prices a planned step with the exact loss of policy N (Theorem 1):
    calls = (1 - l^(R+1)) / (1 - l),  wrong = s * calls,  failed = l^(R+1),  l = (1-p) rho,  s = (1-p)(1-rho)
    cost  = c * calls + L * wrong + F * failed
and uses it on both sides of the keep-or-switch comparison and inside the decision value.
"""
import sys

PATCHES = {
    "ereplan/strategies.py": [
        ("def leak_aware_line(s: Setting, cur: int, u: int, alt_p: dict, switch_cost: float):",
         '''def exact_step_cost(s: Setting, j: int, p: float) -> float:
    """Exact expected loss of one planned step on tool j without a check (policy N of Theorem 1): loud failures
    are retried up to r_max times, silent failures are accepted (PREREGISTRATION_exactline.md)."""
    p = min(max(p, 0.0), 1.0)
    l, sil = (1 - p) * s.rho, (1 - p) * (1 - s.rho)
    n = s.r_max + 1
    calls = float(n) if l >= 1 - 1e-12 else (1 - l ** n) / (1 - l)
    return s.eff_price(j) * calls + s.leak_loss * sil * calls + s.task_cost * l ** n


def leak_aware_line(s: Setting, cur: int, u: int, alt_p: dict, switch_cost: float, exact: bool = False):'''),
        ("""    def per_call(j, p):
        p = max(p, 1e-6)
        return s.eff_price(j) / p + (1 - p) * (1 - s.rho) * s.leak_loss""",
         """    def per_call(j, p):
        if exact:
            return exact_step_cost(s, j, p)
        p = max(p, 1e-6)
        return s.eff_price(j) / p + (1 - p) * (1 - s.rho) * s.leak_loss"""),
        ("""        return leak_aware_line(self.s, ctx["cur"], self.horizon(ctx), self.p_view(ctx), self.s.switch_cost)""",
         """        return leak_aware_line(self.s, ctx["cur"], self.horizon(ctx), self.p_view(ctx), self.s.switch_cost,
                               exact=getattr(self, "exact_line", False))"""),
    ],
    "ereplan/selfcal.py": [
        ("""        stay = (lambda m: u * (c / max(m, 1e-6) + (1 - m) * (1 - self.s.rho) * self.s.leak_loss)) if sym else \\
               (lambda m: u * c / max(m, 1e-6))""",
         """        stay = (lambda m: u * (c / max(m, 1e-6) + (1 - m) * (1 - self.s.rho) * self.s.leak_loss)) if sym else \\
               (lambda m: u * c / max(m, 1e-6))
        if getattr(self, "exact_line", False):          # PREREGISTRATION_exactline.md: exact step cost on both sides
            from .strategies import exact_step_cost
            stay = lambda m: u * exact_step_cost(self.s, cur, m)"""),
    ],
    "ereplan/crosscheck.py": [
        ("for _cls in (CrossCheckRule, CrossCheckRuleNet, CrossCheckRuleSym, CrossCheckRuleTold, AlwaysCrossCheck):",
         "for _cls in (CrossCheckRule, CrossCheckRuleNet, CrossCheckRuleSym, CrossCheckRuleExact, CrossCheckRuleTold, AlwaysCrossCheck):"),
        ("class CrossCheckRuleTold(CrossCheckRule):",
         '''class CrossCheckRuleExact(CrossCheckRule):
    """The corrected rule (net PV) whose switch line and decision value price a planned step with its exact loss
    under the failure model (loud failures retried up to r_max times, silent ones accepted), instead of c/p
    (PREREGISTRATION_exactline.md)."""
    name = "Rule_v5_exact"
    rng_name = "Rule_v5_x"
    net = True
    exact_line = True


class CrossCheckRuleTold(CrossCheckRule):'''),
    ],
}

for path, edits in PATCHES.items():
    s = open(path, encoding="utf-8").read()
    if "exact_line" in s or "exact_step_cost" in s:
        print("already patched:", path); continue
    for old, new in edits:
        if s.count(old) != 1:
            sys.exit(f"{path}: expected text not found exactly once; nothing changed in this file. Send this message to Claude.")
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(s)
    print("patched", path)
print("Done. Now run:  python -m pytest -q")
