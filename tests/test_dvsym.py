"""The symmetric-DV variant (PREREGISTRATION_dvsym.md) is registered and leaves the evaluated rule unchanged."""
from ereplan.strategies import REGISTRY
from ereplan import crosscheck  # noqa: F401  (registers the cross-check rules)


def test_variant_registered_and_paired():
    cls = REGISTRY["Rule_v5_sym"]
    assert cls.dv_sym is True and cls.net is True and cls.rng_name == "Rule_v5_x"


def test_evaluated_rule_unchanged():
    assert getattr(REGISTRY["Rule_v5_x"], "dv_sym", False) is False
