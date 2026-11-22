"""Bias of the label-free (q, f) estimates when shared mistakes occur (sigma > 0) but sigma = 0 is assumed.

Reproduces Table "Limit Shift of the Learned Rates" (Proposition S2 of the Supplementary Material) and the
information argument about q in the paper.
It finds the exact limit of the misspecified estimate: the (q, f) that minimises the Kullback-Leibler divergence
from the true distribution of the five events on a checked call to the sigma = 0 model.

Run:  python tools/sigma_bias.py        (seconds; no models, no randomness)
"""
import numpy as np
from scipy.optimize import minimize


def probs(p, a, r, q, f, sig):
    """Probabilities of: loud, no flag, flag+agree, flag+disagree, flag+alternative loud (paper, Table of events)."""
    s = (1 - p) * (1 - r)
    return np.array([(1 - p) * r,
                     p * (1 - f) + s * (1 - q),
                     p * f * a + s * q * (1 - a) * (1 - r) * sig,
                     p * f * (1 - a) * (1 - r) + s * q * (a + (1 - a) * (1 - r) * (1 - sig)),
                     (p * f + s * q) * (1 - a) * r])


def limit_estimate(p, a, r, q, f, sig):
    true = probs(p, a, r, q, f, sig)

    def cross_entropy(x):
        return -(true * np.log(np.clip(probs(p, a, r, x[0], x[1], 0.0), 1e-15, 1))).sum()

    starts = [(q0, f0) for q0 in (0.2, 0.5, 0.8) for f0 in (0.05, 0.2)]
    best = min((minimize(cross_entropy, s0, bounds=[(1e-4, 1), (1e-4, 1)]) for s0 in starts), key=lambda o: o.fun)
    return best.x


def first_order(p, a, r, q, sig):
    """Proposition S2: delta f ~ sigma s q (1-a)(1-rho) / (p a)."""
    return sig * (1 - p) * (1 - r) * q * (1 - a) * (1 - r) / (p * a)


def fisher_sd(p, a, r, q, f, h=1e-6):
    """Standard deviation of q and f per checked call (inverse Fisher information of the sigma = 0 event model)."""
    P = probs(p, a, r, q, f, 0)
    dq = (probs(p, a, r, q + h, f, 0) - probs(p, a, r, q - h, f, 0)) / (2 * h)
    df = (probs(p, a, r, q, f + h, 0) - probs(p, a, r, q, f - h, 0)) / (2 * h)
    info = np.array([[(dq * dq / P).sum(), (dq * df / P).sum()], [(dq * df / P).sum(), (df * df / P).sum()]])
    cov = np.linalg.inv(info)
    return np.sqrt(cov[0, 0]), np.sqrt(cov[1, 1])


# (p, a, rho, q, f) and the sigma values reported. Real pairs: results/assumptions_confirm_20261118-131727/report.md
# (accuracy of the flagged tool and of phi4-mini; loud share among failures; llama3.1:8b checker q and f).
SETTINGS = {
    "Simulator, degraded": ((0.75, 0.95, 0.5, 0.8, 0.15), (0.25, 0.9)),
    "Simulator, healthy": ((0.95, 0.95, 0.5, 0.8, 0.15), (0.25, 0.9)),
    "qwen2.5:1.5b -> phi4-mini": ((0.535, 0.85, 0.02 / 0.465, 0.404, 0.037), (0.25, 0.495)),
    "qwen2.5:3b -> phi4-mini": ((0.66, 0.85, 0.03 / 0.34, 0.516, 0.053), (0.267, 0.520)),
}

if __name__ == "__main__":
    print("Limit shift of the learned rates when sigma = 0 is assumed")
    for name, ((p, a, r, q, f), sigmas) in SETTINGS.items():
        for sig in sigmas:
            qh, fh = limit_estimate(p, a, r, q, f, sig)
            print(f"  {name:28s} sigma {sig:.3f}: delta f {fh - f:+.4f} (first order {first_order(p, a, r, q, sig):+.4f}), "
                  f"delta q {qh - q:+.4f}")
    print("\nChecked calls needed (simulator values a = 0.95, rho = 0.5, q = 0.8, f = 0.15)")
    for p in (0.95, 0.85, 0.75, 0.60):
        sq, sf = fisher_sd(p, 0.95, 0.5, 0.8, 0.15)
        print(f"  p = {p:.2f}: for sd(q) = 0.1: {(sq / 0.1) ** 2:6.0f};  for sd(f) = 0.03: {(sf / 0.03) ** 2:4.0f}")
