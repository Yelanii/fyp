"""Adds the symmetric-DV rule variant (19 Nov 2026, PREREGISTRATION_dvsym.md) to ereplan/selfcal.py and
ereplan/crosscheck.py. The evaluated rule is not changed. Run once from D:\\FYP\\ereplan:  python apply_dvsym.py
It stops without changing anything if a file does not look as expected."""
import sys

EDITS = {
    "ereplan/selfcal.py": [(
"""        pbar = float((w.sum(axis=1) * PG[:, 0]).sum())
        d0_stay = u * c / max(pbar, 1e-6) <= sw
""",
"""        pbar = float((w.sum(axis=1) * PG[:, 0]).sum())
        # dv_sym (19 Nov 2026, PREREGISTRATION_dvsym.md): price staying with the same per-call cost as the switch
        # line, g(c, p) = c/p + (1-p)(1-rho)L, instead of c/p only. Off by default, so every earlier result is unchanged.
        sym = getattr(self, "dv_sym", False)
        stay = (lambda m: u * (c / max(m, 1e-6) + (1 - m) * (1 - self.s.rho) * self.s.leak_loss)) if sym else \\
               (lambda m: u * c / max(m, 1e-6))
        d0_stay = stay(pbar) <= sw
"""), (
"""            stay_j = u * c / max(mj, 1e-6)
""",
"""            stay_j = stay(mj)
""")],
    "ereplan/crosscheck.py": [(
"""class CrossCheckRuleTold(CrossCheckRule):""",
'''class CrossCheckRuleSym(CrossCheckRule):
    """The corrected rule (net PV) whose decision value prices staying with the same per-call cost as the switch line,
    c/p + (1-p)(1-rho)L, so both sides of the keep-or-switch comparison count wrong answers (PREREGISTRATION_dvsym.md)."""
    name = "Rule_v5_sym"
    rng_name = "Rule_v5_x"
    net = True
    dv_sym = True


class CrossCheckRuleTold(CrossCheckRule):'''), (
"""for _cls in (CrossCheckRule, CrossCheckRuleNet, CrossCheckRuleTold, AlwaysCrossCheck):""",
"""for _cls in (CrossCheckRule, CrossCheckRuleNet, CrossCheckRuleSym, CrossCheckRuleTold, AlwaysCrossCheck):""")],
}

new = {}
for path, edits in EDITS.items():
    s = open(path, encoding="utf-8").read()
    if "dv_sym" in s:
        sys.exit(f"{path} already contains dv_sym: the patch was applied before. Nothing changed.")
    for old, rep in edits:
        n = s.count(old)
        if n != 1:
            sys.exit(f"{path}: expected text found {n} times (should be 1). Nothing changed. Send this message to Claude.")
        s = s.replace(old, rep)
    new[path] = s
for path, s in new.items():
    open(path, "w", encoding="utf-8").write(s)
    print("patched", path)
print("Done. Now run:  python -m pytest -q")
