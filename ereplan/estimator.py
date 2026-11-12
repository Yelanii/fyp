"""Check-corrected, windowed estimate of a tool's success rate (Section 3.3.5.5, "Range").

A call shows a failure with probability (1 - p) * d, where
    d = rho + (1 - rho) * q   if the call was checked
    d = rho                   otherwise.
So loud failures on unchecked calls are free evidence, and checked calls are
corrected for the silent failures that checks miss.
"""
from collections import deque
import numpy as np

GRID = np.linspace(0.0, 1.0, 201)
_EPS = 1e-12
_LOG_P = np.log(np.clip(GRID, _EPS, 1.0))
_LOG_1MP = np.log(np.clip(1.0 - GRID, _EPS, 1.0))


def _loglik_counts(fail_c, ok_c, fail_u, ok_u, d_c, d_u):
    """Log-likelihood on the grid from four counts (checked/unchecked x failure seen/not)."""
    pf_c = np.clip((1.0 - GRID) * d_c, _EPS, 1.0)
    pf_u = np.clip((1.0 - GRID) * d_u, _EPS, 1.0)
    return (fail_c * np.log(pf_c) + ok_c * np.log(1.0 - pf_c + _EPS)
            + fail_u * np.log(pf_u) + ok_u * np.log(1.0 - pf_u + _EPS))


class RangeEstimator:
    """Grid posterior over p from a Beta prior and the last W observed calls."""

    def __init__(self, window: int, rho: float, q: float, prior_mean: float, prior_strength: float):
        self.window = window
        self.rho = rho
        self.q = q
        self.d_c = rho + (1.0 - rho) * q
        self.d_u = rho
        # Advertised-rate prior: Beta with mean = prior_mean, worth prior_strength pseudo-calls when the
        # tool has no data. Its weight fades linearly as the window fills, so with a full window the
        # prior is uniform, as Section 3.3.5.5 specifies. (A fixed-weight prior would keep pulling the
        # estimate towards the advertised rate after a real drop.)
        self.prior_strength = prior_strength
        a = max(prior_mean * prior_strength, 1.0)
        b = max((1.0 - prior_mean) * prior_strength, 1.0)
        self._log_prior_full = (a - 1.0) * _LOG_P + (b - 1.0) * _LOG_1MP
        self.obs = deque(maxlen=window)  # (checked: bool, failure_seen: bool)
        self._cache = None

    def update(self, checked: bool, failure_seen: bool) -> None:
        self.obs.append((bool(checked), bool(failure_seen)))
        self._cache = None

    @property
    def log_prior(self):
        fade = max(0.0, 1.0 - len(self.obs) / self.window)
        return fade * self._log_prior_full

    def counts(self):
        fc = oc = fu = ou = 0
        for c, f in self.obs:
            if c:
                fc += f; oc += (not f)
            else:
                fu += f; ou += (not f)
        return fc, oc, fu, ou

    def posterior(self, extra_fail_c: int = 0, extra_ok_c: int = 0) -> np.ndarray:
        fc, oc, fu, ou = self.counts()
        lp = self.log_prior + _loglik_counts(fc + extra_fail_c, oc + extra_ok_c, fu, ou, self.d_c, self.d_u)
        lp -= lp.max()
        w = np.exp(lp)
        return w / w.sum()

    def summary(self):
        """(mean, low, high): posterior mean and central 95% interval."""
        if self._cache is None:
            w = self.posterior()
            cdf = np.cumsum(w)
            low = GRID[np.searchsorted(cdf, 0.025)]
            high = GRID[min(np.searchsorted(cdf, 0.975), len(GRID) - 1)]
            self._cache = (float((w * GRID).sum()), float(low), float(high))
        return self._cache

    @property
    def mean(self):
        return self.summary()[0]
