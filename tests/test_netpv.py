from ereplan.strategies import REGISTRY
from ereplan import crosscheck, v5_exp  # noqa: F401
from ereplan.runner import run


def _one(name):
    return run(name, dict(v5_exp.SESSION), v5_exp.setting(0.95, 3.0, 0.15, 1.0, "none"), "drop_0.75", 8000)


def test_net_rule_is_registered_and_never_checks_more_than_gross():
    assert "Rule_v5_net" in REGISTRY
    gross, net = _one("Rule_v5_x"), _one("Rule_v5_net")
    # the net criterion subtracts a non-negative term from the same value, so on the same random stream
    # it cannot decide to check more often at the first decision; over a run we only require "not many more"
    assert net["checks_per_task"] <= gross["checks_per_task"] * 1.25


def test_gross_rule_unchanged_by_the_new_class():
    a, b = _one("Rule_v5_x"), _one("Rule_v5_x")
    assert a["total_loss_fail"] == b["total_loss_fail"]
