"""Settings for the pilot: tools, prices and the factors that the pilot varies.

Every number here is a simulated value. Nothing is a real price.
"""
from dataclasses import dataclass, field, replace
from typing import List


@dataclass(frozen=True)
class Tool:
    name: str
    price: float          # c: simulated price per call
    latency: float        # l: simulated latency per call (weighted by lam)
    base_p: float         # success rate before any degradation
    advertised_p: float   # what the agent believes before seeing any calls (prior mean)


@dataclass(frozen=True)
class Setting:
    """One cell of the pilot grid plus the fixed environment parameters."""
    tools: tuple = (
        Tool("A_cheap", price=20.0, latency=1.0, base_p=0.95, advertised_p=0.95),
        Tool("B_mid", price=24.0, latency=1.0, base_p=0.95, advertised_p=0.95),
        Tool("C_premium", price=30.0, latency=1.0, base_p=0.97, advertised_p=0.95),
    )
    steps_per_task: int = 5      # S: calls per task (all on one interchangeable capability)
    n_tasks: int = 120           # tasks per run, so 600 steps
    rho: float = 0.5             # share of failures that are loud (seen for free)
    q_true: float = 0.8          # catch rate of a check in the environment
    q_assumed: float = 0.8       # catch rate the agent assumes (RQ3 varies this later)
    check_frac: float = 0.15     # check price as a share of the mean tool price
    leak_mult: float = 1.0       # leak loss in units of one task's cost
    switch_cost: float = 5.0     # c_switch
    lam: float = 0.0             # latency weight (0 in the pilot: price only)
    r_max: int = 2               # retries after a detected failure
    prior_strength: float = 20.0 # pseudo-calls behind the advertised rate
    check_corr: float = 0.0      # 0 = independent check; c > 0: once a tool has degraded, its new silent
                                 # failures are caught with q * (1 - c) (the check shares the failure source)
    false_alarm: float = 0.0     # f: chance that a check wrongly flags a CORRECT result
    fa_persistent: bool = True   # True: a step the check gets wrong is flagged on every retry (as with a
                                 # deterministic LLM judge); False: each attempt is an independent draw
    fa_assumed: float = -1.0     # f the agent is told; -1 means "the true f"
    fa_persistence: float = -1.0 # pi in [0, 1]: chance that a retry or re-check of a step
                                 # repeats the previous verdict instead of drawing a fresh one. -1 means
                                 # "use fa_persistent" (True -> 1.0, False -> 0.0), so older runs are unchanged.
    xc_shared: float = 0.0       # Core 4: chance that two WRONG outputs agree on a cross-check (shared
                                 # mistakes, e.g. two tools that copy the same stale source). 0 = they never agree.
    xc_noise: float = 0.0        # rule v5 stress test: chance that a cross-check comparison reports the
                                 # wrong answer (agree <-> disagree), as with fuzzy text answers. 0 = exact comparison.
    # --- FR19, rule v5.1 ---
    third_source_frac: float = 0.0   # share of flagged, cross-checked calls that also query a third, independent
                                      # source (a different model family) before the two-source verdict is used
    third_q: float = -1.0            # third source's catch rate on a truly wrong output; -1 means "same as q_true"
    third_shared: float = 0.02       # chance the third source reproduces a shared mistake the first two already
                                      # made (believed lower than xc_shared: a different model family)
    third_check_price: float = -1.0  # price of a third-source query; -1 means "same as check_price"
    audit_frac: float = 0.0          # share of ALL checked calls where the true label is also bought (a small,
                                      # expensive labelled audit) and fed straight to the rule
    audit_price: float = -1.0        # price of one audited label; -1 means "same as mean_price"
    # --- drift test: the checker's rates change once during a run, at a step drawn per run from
    # its own random stream (Environment.t_drift). -1 keeps the rate unchanged, so every earlier run is unchanged.
    q_late: float = -1.0             # catch rate from the change on
    f_late: float = -1.0             # false-alarm rate from the change on

    @property
    def mean_price(self) -> float:
        return sum(t.price for t in self.tools) / len(self.tools)

    @property
    def check_price(self) -> float:
        return self.check_frac * self.mean_price

    @property
    def leak_loss(self) -> float:
        return self.leak_mult * self.steps_per_task * self.mean_price

    @property
    def task_cost(self) -> float:
        return self.steps_per_task * self.mean_price

    @property
    def pi_true(self) -> float:
        if self.fa_persistence >= 0:
            return float(self.fa_persistence)
        return 1.0 if self.fa_persistent else 0.0

    @property
    def f_assumed(self) -> float:
        return self.false_alarm if self.fa_assumed < 0 else self.fa_assumed

    def eff_price(self, k: int) -> float:
        t = self.tools[k]
        return t.price + self.lam * t.latency

    def with_(self, **kw) -> "Setting":
        return replace(self, **kw)


def pilot_grid(base: Setting = Setting()) -> List[Setting]:
    """Table 3.16: q in {0.5, 0.8}, check price in {15%, 30%}, leak loss = one task's cost."""
    out = []
    for q in (0.5, 0.8):
        for cf in (0.15, 0.30):
            out.append(base.with_(q_true=q, q_assumed=q, check_frac=cf, leak_mult=1.0))
    return out


SCENARIOS = ("S1_sudden", "S2_gradual", "S3_harmless")
TUNE_SEEDS = tuple(range(50, 60))
JUDGE_SEEDS = tuple(range(0, 20))
