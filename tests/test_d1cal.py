"""D1-cal (run_d1cal.py): the calibrated variants run, and the strong prior keeps the learned f near the calibration."""
import run_d1cal as c
from tests.test_agent_live import _table


def test_calibrated_variants_run_and_hold_f_near_calibration():
    t = _table()
    for k in c.KEYS:
        r = c.d.run_one(t, k, 7010, 52.0, 100.0)
        assert r["loss"] > 0
    r = c.d.run_one(t, "v5_cal", 7010, 52.0, 100.0)
    assert abs(r["f_hat"] - c.F_CAL) < 0.03


def test_report_runs_on_a_small_table():
    rows = c.run("dev", table=_table())
    assert {r["strategy"] for r in rows} == set(c.KEYS)
