"""D1-power (run_d1power.py): the strategies are defined as in D1-cal and the prior fix, and the report runs."""
import run_d1power as p
from tests.test_agent_live import _table


def test_strategies_match_earlier_definitions():
    import run_d1cal as c
    assert p.d.STRATS["v5_cal"] == c.d.STRATS["v5_cal"]
    assert p.d.STRATS["v5_fix"][1]["f_prior_matched"] is True


def test_report_runs_on_a_small_table():
    rows = p.run("dev", table=_table())
    assert {r["strategy"] for r in rows} == set(p.KEYS)
