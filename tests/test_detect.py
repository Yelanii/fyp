"""N1 detectability test: the settings vary only q, f and rho (run_detect.py)."""
import run_detect as rd


def test_detect_settings_vary_only_detectability():
    base = rd.make_setting("high", 0.5, 50, 1.0, "true")
    for det, (q, f) in rd.DET.items():
        for rho in rd.RHOS:
            s = rd.make_setting(det, rho, 50, 1.0, "true")
            assert (s.q_true, s.false_alarm, s.rho) == (q, f, rho)
            assert s.tools == base.tools and abs(s.leak_loss - base.leak_loss) < 1e-9 and abs(s.check_price - base.check_price) < 1e-9


def test_detect_levels_are_ordered():
    sep = [q - f for q, f in rd.DET.values()]
    assert sep == sorted(sep, reverse=True) and rd.DET["high"] == (0.95, 0.15)
