"""Adds the optional matched f prior (f_prior_matched, off by default) to ereplan/crosscheck.py, in place.

Run once from the repository root:  python apply_priorfix.py
It changes four places in crosscheck.py and nothing else; every existing rule keeps its behaviour.
Running it twice is safe (it stops if the change is already there).
"""
import sys

P = "ereplan/crosscheck.py"
raw = open(P, "rb").read().decode("utf-8")
nl = "\r\n" if "\r\n" in raw else "\n"
s = raw.replace("\r\n", "\n")
if "f_prior_matched" in s:
    sys.exit("Already applied: nothing to do.")
EDITS = [
    ("    def __init__(self, rho, q_mean=0.5, q_strength=2.0, f_mean=0.1, f_strength=2.0, fixed=None):",
     "    def __init__(self, rho, q_mean=0.5, q_strength=2.0, f_mean=0.1, f_strength=2.0, fixed=None, f_ab=None):"),
    ("            lp = _beta_log(_Q, q_mean, q_strength) + _beta_log(_F / FMAX, f_mean / FMAX, f_strength)",
     "            if f_ab is None:\n"
     "                lp = _beta_log(_Q, q_mean, q_strength) + _beta_log(_F / FMAX, f_mean / FMAX, f_strength)\n"
     "            else:                               # Beta(a, b) on f / FMAX given directly, with no floor on a or b\n"
     "                a, b = f_ab\n"
     "                lp = _beta_log(_Q, q_mean, q_strength) + ((a - 1) * np.log(np.clip(_F / FMAX, _E, 1))\n"
     "                                                          + (b - 1) * np.log(np.clip(1 - _F / FMAX, _E, 1)))"),
    ("                 q_prior_mean=0.5, q_prior_strength=2.0, f_prior_mean=0.1, f_prior_strength=2.0):",
     "                 q_prior_mean=0.5, q_prior_strength=2.0, f_prior_mean=0.1, f_prior_strength=2.0, f_prior_matched=False):"),
    ("        self.cm = CheckerMemory(s.rho, q_prior_mean, q_prior_strength, f_prior_mean, f_prior_strength, fixed=fixed)",
     "        # f_prior_matched: a weak prior whose mean really is f_prior_mean on the f grid. The default prior floors\n"
     "        # each Beta parameter at 1, which moves its mean from 0.1 to about 0.19 (FMAX 0.5) or 0.33 (FMAX 0.95).\n"
     "        f_ab = (1.0, FMAX / f_prior_mean - 1.0) if f_prior_matched else None\n"
     "        self.cm = CheckerMemory(s.rho, q_prior_mean, q_prior_strength, f_prior_mean, f_prior_strength, fixed=fixed, f_ab=f_ab)"),
]
for old, new in EDITS:
    if s.count(old) != 1:
        sys.exit(f"Could not find this line exactly once, so nothing was changed:\n{old}")
for old, new in EDITS:
    s = s.replace(old, new)
open(P, "wb").write(s.replace("\n", nl).encode("utf-8"))
print("Applied: ereplan/crosscheck.py now has the optional matched f prior (off by default).")
