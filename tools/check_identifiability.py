"""Proposition 5 of the paper (identifiability): rank of the Jacobian of the five cross-check
event probabilities with respect to (q, f, sigma).

Run from the repository root:  python tools/check_identifiability.py   (needs sympy)"""
import sympy as sp
q, f, sg, p, a, r, p2 = sp.symbols("q f sigma p a rho p2", positive=True)
def events(p):
    s = (1 - p) * (1 - r)
    return [(1 - p) * r,
            p * (1 - f) + s * (1 - q),
            p * f * a + s * q * (1 - a) * (1 - r) * sg,
            p * f * (1 - a) * (1 - r) + s * q * (a + (1 - a) * (1 - r) * (1 - sg)),
            (p * f + s * q) * (1 - a) * r]
th = [q, f, sg]
pt = {q: sp.Rational(4, 5), f: sp.Rational(3, 20), sg: sp.Rational(1, 2), a: sp.Rational(19, 20), r: sp.Rational(1, 2),
      p: sp.Rational(9, 10), p2: sp.Rational(3, 5)}
E1 = events(p); J1 = sp.Matrix(E1).jacobian(th)
print("events sum to 1:", sp.simplify(sum(E1)) == 1)
print("one success rate: symbolic rank", J1.rank(simplify=True), "| at a numeric point", J1.subs(pt).rank())
J2 = sp.Matrix(E1 + events(p2)).jacobian(th)
print("two success rates: symbolic rank", J2.rank(simplify=True), "| at a numeric point", J2.subs(pt).rank())
J0 = sp.Matrix(E1).jacobian([q, f]).subs(sg, 0)
print("sigma = 0 assumed, (q, f): rank", J0.subs(pt).rank())
