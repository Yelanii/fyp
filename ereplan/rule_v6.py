"""Rule v6 (FR18, built 10 November 2026): rule v5 that RE-TESTS a tool it has left.

Rule v5 remembers a tool it switched away from as bad for ever: the tool gets no new calls, so its estimate never
changes. That is right when a degraded tool stays degraded, and wrong when it is repaired, or when the tool switched
TO degrades later and the old one is now the better choice.

Rule v6 adds one mechanism, forgetting with back-off. When a tool has not been called for H calls, its observations
are discarded and its estimate returns to the advertised prior. The ordinary switch line then sends the agent back
to it if (and only if) it is cheap enough to be worth trying; if it is still bad, the ordinary rule detects that and
leaves again, and the waiting time for that tool doubles (H, 2H, 4H, ...), so a permanently broken tool is re-tested
ever more rarely. H = 150 calls, chosen before any run (a quarter of a 600-call run) and not tuned.

Also here: fixed-tool reference policies ("always use tool A / B / C, never check"), the general form of the
"buy the better tool" baseline.
"""
from .crosscheck import CrossCheckRule, JointEstimatorV5
from .strategies import NeverCheck, REGISTRY


class RetestRule(CrossCheckRule):
    name = "Rule_v6"
    rng_name = "Rule_v5_x"          # same random stream as v5, so v6 vs v5 is a fully paired comparison
    retest_after = 150

    def __init__(self, s, rng, **kw):
        super().__init__(s, rng, **kw)
        K = len(s.tools)
        self.last_used = [None] * K          # call index of the last observation of each tool
        self.leaves = [0] * K                # how many times the rule has switched away from each tool
        self.retests = 0
        self._t = 0

    def observe(self, k, checked, failure_seen, kind=None, a=None):
        super().observe(k, checked, failure_seen, kind=kind, a=a)
        self.last_used[k] = self._t

    def switch_to(self, ctx):
        self.leaves[ctx["cur"]] += 1
        return super().switch_to(ctx)

    def decide(self, ctx, allow_switch=True):
        self._t = ctx["t"]
        cur = ctx["cur"]
        for j in range(len(self.s.tools)):
            if j == cur or self.leaves[j] == 0 or self.last_used[j] is None:
                continue
            wait = self.retest_after * 2 ** (self.leaves[j] - 1)
            if self._t - self.last_used[j] >= wait:
                t = self.s.tools[j]
                self.ests[j] = JointEstimatorV5(self.window, self.s.rho, t.advertised_p, self.s.prior_strength, self.cm)
                self.last_used[j] = None             # forgotten: eligible again, judged afresh
                self.retests += 1
        return super().decide(ctx, allow_switch)


REGISTRY[RetestRule.name] = RetestRule


def _fixed(idx, label):
    class Fixed(NeverCheck):
        name = f"R_fix_{label}"

        def start_task(self, ctx):
            self.current = idx
            return idx

        def decide(self, ctx, allow_switch=True):
            ctx["trace"] = {}
            return "call"
    Fixed.__name__ = f"Fixed{label}"
    REGISTRY[Fixed.name] = Fixed
    return Fixed


FixedA, FixedB, FixedC = _fixed(0, "A"), _fixed(1, "B"), _fixed(2, "C")
