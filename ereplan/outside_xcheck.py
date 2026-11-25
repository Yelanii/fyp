"""The three published baselines of Core 2 (outside_baselines.py), each given the cross-check that the proposed rule
uses to resolve a flag. See preregistration/PREREGISTRATION_core2x.md.

In Core 2 the adapted methods resolve a flag the usual way, by retrying the step, and two of them lost mainly because
a checker that repeats its false alarms makes them fail tasks. These variants change only that: a flagged answer is
run once on the best alternative tool and the two answers are compared, exactly as for the proposed rule (runner.py,
the cross-check branch). Everything else, including the tuned parameters in data/processed/core2_tuned.json, is kept.

B13x_ssv        SSV: its 'reject' region retried the step; here a rejected (flagged) answer goes to the strong
                verifier, which in this adaptation is the cross-check, so every flag is resolved by a cross-check.
                The threshold update weights this forced verification as observed with probability 1.
B14x_rdecusum   RDE-CUSUM with the cross-check. Agreement after a flag counts as no failure for the statistic;
                disagreement, or a loud failure of the alternative, counts as a failure.
B15x_glrklucb   GLR-klUCB with the cross-check, with the same reading of the outcome for its observations.
"""
from .strategies import REGISTRY
from .outside_baselines import SSVStyle, RDECusum, GLRklUCB


class SSVx(SSVStyle):
    name = "B13x_ssv"

    def ssv_action(self, k, flagged):
        act = super().ssv_action(k, flagged)
        if act == "R":                       # reject -> resolve by the cross-check instead of retrying
            act, self._q = "SV", 1.0
        return act


class _XMixin:
    crosscheck = True

    def crosscheck_tool(self, ctx):
        return self.line(ctx)[1]

    def alt_mean(self, j):
        return self.ests[j].mean

    def observe(self, k, checked, failure_seen, kind=None, a=None):
        if kind == "flag_agree":
            failure_seen = False
        elif kind in ("flag_disagree", "flag_altloud"):
            failure_seen = True
        super().observe(k, checked, failure_seen, kind=None)


class RDECusumX(_XMixin, RDECusum):
    name = "B14x_rdecusum"


class GLRklUCBX(_XMixin, GLRklUCB):
    name = "B15x_glrklucb"


for _cls in (SSVx, RDECusumX, GLRklUCBX):
    REGISTRY[_cls.name] = _cls
