import json
from ereplan import costbench_v5 as m


def _world(f=0.15, pi=1.0, seed=1990):
    return m.WorldFA(json.load(open(m.ROUTES)), 0.75, 0.95, f, pi, 3.0, 0.0, seed)


def test_no_false_alarms_without_f():
    w = _world(f=0.0)
    r = m.simulate(w, m.STRATS["always"](w, 1990))
    assert r["false_alarms"] == 0 and r["crosschecks"] == 0


def test_persistent_false_alarm_repeats_on_retry():
    w = _world(pi=1.0)
    assert (w.UFA[..., 1] == w.UFA[..., 0]).all() and (w.UFA[..., 2] == w.UFA[..., 0]).all()


def test_crosscheck_resolves_false_alarms_and_is_deterministic():
    w = _world()
    a = m.simulate(w, m.STRATS["always_x"](w, 1990))
    b = m.simulate(w, m.STRATS["always_x"](w, 1990))
    assert a == b and a["fa_resolved"] > 0 and a["fail_rate"] <= m.simulate(w, m.STRATS["always"](w, 1990))["fail_rate"]


def test_alternative_price_for_X_is_at_least_X_price():
    w = _world()
    for t, ax in zip(w.tasks, w.alt_X):
        assert ax >= next(c for n, c in t["routes"][0] if n == t["X"]) - 1e-9
