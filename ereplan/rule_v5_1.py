"""Rule v5.1 (FR19, built 6 Nov 2026): rule v5's cross-check, made robust to shared mistakes.

Rule v5 (crosscheck.py) and its sigma-aware variant (rule_v5s.py, Core 4) learn the checker's (q, f, sigma)
without labels, but CORE4_2026-10-31.md shows that with only two sources (the original tool and the alternative
it is cross-checked against), (q, f, sigma) are NOT identifiable from one success-rate regime: the information
matrix has rank 2 of the 3 unknowns. A third, conditionally-independent source restores identifiability (Allman,
Matias and Rhodes, 2009): with three sources judging the same item, their agreement patterns pin down each
source's error rate without any ground truth.

This rule adds two label-free-compatible mechanisms, plus a fallback:

1. A THIRD SOURCE on a few flags (Setting.third_source_frac of flagged, cross-checked calls; proposal default
   0.3). A judge from a different model family independently confirms or disputes the two-source agree/disagree
   verdict. The rule is told only CONFIRM or DISPUTE -- never the ground truth (see observe_third). Confirmations
   and disputes update sigma_hat, the rule's own belief about how often the two-source agreement is really a
   shared mistake, by a method-of-moments argument:
       E[dispute | two sources agreed] = sigma_hat * (1 - third_shared_belief) + (1 - sigma_hat) * f_believed
   i.e. a dispute happens either because it really was a shared mistake and the third source (mostly) catches it,
   or because it was a genuine false alarm and the third source (rarely) raises its own false alarm. Solving for
   sigma_hat given the rule's own f_believed and a conservative, DESIGN-CHOSEN third_shared_belief (not read from
   the environment -- see the class attribute) gives a usable estimate. This is a simplification of the full
   three-source tensor estimator (which would jointly solve for all of q, f, sigma from the triple-wise agreement
   rates); it captures the same identifying information with far less machinery, at the cost of needing f from
   elsewhere (the audit below, or the cross-check memory's own f_mean before it is trusted). This simplification,
   and the fallback threshold below, are design choices that need the supervisor's sign-off (see README decision
   log) -- they are not derived from the proposal's formulas.

2. A SMALL LABELLED AUDIT (Setting.audit_frac of ALL checked calls; proposal default small, e.g. 0.02-0.05). A
   rare true label is bought (at audit_price) and used directly to estimate q and f from counts. This is the
   ONLY place true labels reach this rule; both audited estimates feed observe_audit, never the main (q, f)
   posterior used for ordinary cross-checking.

3. FALLBACK TO RULE v4's DECISION. Once enough evidence has accumulated (min_evidence observations between the
   third source and the audit) and sigma_hat is at or above fallback_sigma, the rule judges the cross-check
   unreliable (Proposition 3 in CORE4_2026-10-31.md: a FIXED cross-check policy's loss does not even depend on
   sigma once shared mistakes are this common, so there is nothing left to gain from trusting it) and switches
   its DECISION formula to use the audited q directly, with no false-alarm-cost term, exactly like rule v4's
   simpler protection-value-only check (see _v4_wants_check). The cross-check keeps running underneath (so
   evidence keeps arriving and fallback can lift later if sigma_hat drops), but stops being trusted to decide.
   This is a decision-level fallback, not a full behavioural one: the rule still pays for the cross-check and
   the third source while in fallback. Scoping it this way was a deliberate choice to keep the change to the
   well-tested runner small; it is logged here for the same reason as 1 above.
"""
import numpy as np

from .rule_v5s import CrossCheckRuleS
from .strategies import REGISTRY


class Rule_v5_1(CrossCheckRuleS):
    name = "Rule_v5_1"

    third_source = True              # tells the runner to query env.third_source() on a sample of flags
    wants_audit = True                # tells the runner to occasionally reveal a true label

    third_shared_belief = 0.08        # DESIGN CHOICE: the rule's own conservative belief about how often a third
                                       # source from a different model family reproduces a shared mistake. Not
                                       # read from the environment; needs supervisor sign-off (see docstring).
    fallback_sigma = 0.35             # DESIGN CHOICE: sigma_hat at or above this triggers the v4 fallback.
    min_evidence = 8                  # minimum third-source + audit observations before fallback can trigger

    def __init__(self, s, rng, **kw):
        super().__init__(s, rng, **kw)
        self.audit_q_hits = self.audit_q_n = 0
        self.audit_f_hits = self.audit_f_n = 0
        self.third_agree_total_n = self.third_dispute_given_agree_n = 0
        self.sigma_hat = 0.0
        self.fallback = False

    # ---- the audited (labelled) estimates: the only place truth reaches this rule
    @property
    def audited_q(self):
        if self.audit_q_n == 0:
            return self.cm.q_mean               # no audit yet: fall back to the cross-check-learned prior
        return (self.audit_q_hits + 1.0) / (self.audit_q_n + 2.0)

    @property
    def audited_f(self):
        if self.audit_f_n == 0:
            return self.cm.f_mean
        return (self.audit_f_hits + 1.0) / (self.audit_f_n + 2.0)

    def observe_audit(self, checked, outcome_kind, truly_correct):
        """FR19's labelled audit. `outcome_kind` is the raw environment outcome ('caught', 'ok', ...) before any
        flag resolution; a check is scored as having 'flagged' when outcome_kind == 'caught' (the agent's check
        itself raised a flag, regardless of what later happened to it)."""
        if not checked:
            return
        flagged = outcome_kind == "caught"
        if truly_correct:
            self.audit_f_n += 1
            self.audit_f_hits += int(flagged)
        else:
            self.audit_q_n += 1
            self.audit_q_hits += int(flagged)
        self._update_fallback()

    # ---- the third source: label-free, confirm/dispute only
    def observe_third(self, agree, third_confirms):
        """`agree`: the two-source (original vs alternative) verdict. `third_confirms`: whether the third source's
        independent judgement matched that verdict. Never told the ground truth."""
        if agree:
            self.third_agree_total_n += 1
            if not third_confirms:
                self.third_dispute_given_agree_n += 1
        self._update_sigma_from_third()
        self._update_fallback()

    def _update_sigma_from_third(self):
        if self.third_agree_total_n < 3:
            return
        dispute_rate = self.third_dispute_given_agree_n / self.third_agree_total_n
        f = self.audited_f if self.audit_f_n >= 2 else self.cm.f_mean
        denom = max(1.0 - self.third_shared_belief - f, 1e-6)
        self.sigma_hat = float(np.clip((dispute_rate - f) / denom, 0.0, 1.0))

    def _update_fallback(self):
        evidence = self.third_agree_total_n + self.audit_q_n + self.audit_f_n
        self.fallback = evidence >= self.min_evidence and self.sigma_hat >= self.fallback_sigma

    # ---- deciding
    def wants_check(self, ctx, line, mean, low, high):
        if not self.fallback:
            w = super().wants_check(ctx, line, mean, low, high)
            ctx["trace"]["fallback"] = False
            return w
        return self._v4_wants_check(ctx, line, mean, low, high)

    def _v4_wants_check(self, ctx, line, mean, low, high):
        """Rule v4's simpler check: protection value from the AUDITED q only, no false-alarm-cost term."""
        est = self.ests[ctx["cur"]]
        audit_roll = self.rng.random() < self.epsilon
        qh = self.audited_q
        pv = qh * (1 - mean) * (1 - self.s.rho) * self.s.leak_loss
        crossing = low <= line <= high
        dv = 0.0
        if crossing:
            _, _, R_alt = self.line(ctx)
            dv = self._dv(est, self.horizon(ctx), R_alt, ctx["cur"])
        value = pv + dv
        ctx["trace"].update(pv=pv, dv=dv, q_hat=qh, zone="crossing" if crossing else "safe", audit=audit_roll,
                             fallback=True, sigma_hat=self.sigma_hat)
        check = value >= self.s.check_price or audit_roll
        ctx["trace"]["reason"] = (f"fallback to v4 (sigma_hat {self.sigma_hat:.2f} >= {self.fallback_sigma}); "
                                   f"audited q {qh:.2f}; value {value:.1f} vs price {self.s.check_price:.1f}")
        return check


REGISTRY[Rule_v5_1.name] = Rule_v5_1
