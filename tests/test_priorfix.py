"""Prior fix: the matched prior has mean near 0.1; the default floored prior does not; the live part runs."""
from ereplan.crosscheck import CheckerMemory, FMAX


def test_matched_prior_mean_is_near_stated_mean():
    assert abs(CheckerMemory(0.5).f_mean - 0.1) > 0.05                       # the floored default is far from 0.1
    assert abs(CheckerMemory(0.5, f_ab=(1.0, FMAX / 0.1 - 1)).f_mean - 0.1) < 0.02


def test_live_part_runs_on_a_small_table():
    import run_priorfix as r
    from tests.test_agent_live import _table
    r.live("dev", table=_table())


def test_costbench_part_imports_and_its_prior_is_matched():
    import run_priorfix_cb as c
    from ereplan.crosscheck import FMAX as fm
    assert set(c.cb.STRATS) == {"v5", "v5_fix", "v5_told", "v4"}
    assert abs(CheckerMemory(0.5, f_ab=(1.0, fm / 0.1 - 1)).f_mean - 0.1) < 0.02
