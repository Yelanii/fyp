"""FR21 ablation: rule v5.1 (the full proposed rule) with one of its five ingredients removed at a
time, as C5 in the proposal promises: the false-alarm term, persistence, change detection, switching, and
label-free learning. Four of the five are separate strategy classes below; the fifth (change detection) needs no
new class -- it is run as Rule_v5_1 itself with an effectively infinite window (see run_ablation.py), so the
estimator never forgets and cannot react to a change.
"""
from .rule_v5_1 import Rule_v5_1
from .rule_v5s import CheckerMemoryS
from .strategies import REGISTRY


class Rule_v5_1_nofa(Rule_v5_1):
    """Ingredient removed: the false-alarm term. The check decision uses PV + DV only, with no subtraction for
    the expected cost of a false alarm under cross-checking."""
    name = "Rule_v5_1_nofa"
    rng_name = "Rule_v5_1"

    def fa_cost(self, mean, ctx):
        return 0.0


class Rule_v5_1_noxc(Rule_v5_1):
    """Ingredient removed: persistence handling. A flag is resolved by a plain retry on the same tool (rule v4's
    way), instead of a cross-check against the alternative -- the mechanism that makes a checker's REPEATED false
    alarms harmless rather than costly (PREREGISTRATION_v5.md, H-V5). The labelled audit can still fire (it does
    not need a cross-check event); the third source cannot, since it only samples cross-check events, so it never
    fires in this variant."""
    name = "Rule_v5_1_noxc"
    rng_name = "Rule_v5_1"
    crosscheck = False


class Rule_v5_1_noswitch(Rule_v5_1):
    """Ingredient removed: switching. The agent never leaves the tool it starts a run on."""
    name = "Rule_v5_1_noswitch"
    rng_name = "Rule_v5_1"

    def decide(self, ctx, allow_switch=True):
        return super().decide(ctx, allow_switch=False)


class _FixedMemoryS(CheckerMemoryS):
    """A checker memory that never learns: a point mass at the told (q, f). Sigma is never used (fa_cost,
    sigma_hat and the fallback are all driven by this fixed memory's f, not by the usual learned sigma)."""

    def __init__(self, q, f, rho):
        super().__init__(rho)
        self._q, self._f = q, f

    def update(self, *a, **k):
        return

    @property
    def q_mean(self):
        return self._q

    @property
    def f_mean(self):
        return self._f

    @property
    def s_mean(self):
        return 0.0


class Rule_v5_1_told(Rule_v5_1):
    """Ingredient removed: label-free learning. The rule is TOLD q and f (as rule v4 is, and as rule v5's own
    ablation Rule_v5_told in crosscheck.py is), extended to v5.1 by also switching off the third source and the
    audit, since there is nothing left for them to calibrate."""
    name = "Rule_v5_1_told"
    rng_name = "Rule_v5_1"
    third_source = False
    wants_audit = False

    def __init__(self, s, rng, **kw):
        super().__init__(s, rng, **kw)
        self.cm = _FixedMemoryS(s.q_assumed, s.f_assumed, s.rho)
        for e in self.ests:
            e.cm = self.cm


for _cls in (Rule_v5_1_nofa, Rule_v5_1_noxc, Rule_v5_1_noswitch, Rule_v5_1_told):
    REGISTRY[_cls.name] = _cls
