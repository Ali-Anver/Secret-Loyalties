"""
Afriat / Varian revealed-preference machinery.

GARP and the Critical Cost Efficiency Index (CCEI, Afriat 1972; Varian 1990).
This is the detection statistic the whole project rests on -- keep it correct.

An observation is (p, x): price vector p and chosen bundle x.
CCEI = the largest e in [0,1] such that the data contain no GARP violation
when budgets are relaxed to a fraction e. CCEI = 1 <=> data are exactly
rationalisable by some continuous, concave, monotone utility (Afriat's theorem).
"""
from __future__ import annotations


def _dot(a, b):
    return sum(ai * bi for ai, bi in zip(a, b))


def _violates_garp(obs, e):
    """True iff the data violate GARP at efficiency level e."""
    n = len(obs)
    exp = [_dot(p, x) for p, x in obs]                       # own-budget expenditure

    # direct revealed preference at level e:  x_i R^D_e x_j  iff  e * p_i.x_i >= p_i.x_j
    R = [[e * exp[i] >= _dot(obs[i][0], obs[j][1]) for j in range(n)] for i in range(n)]

    # transitive closure (Warshall)
    for k in range(n):
        Rk = R[k]
        for i in range(n):
            if R[i][k]:
                Ri = R[i]
                for j in range(n):
                    if Rk[j]:
                        Ri[j] = True

    # violation:  x_i R_e x_j  and  x_j strictly directly revealed preferred to x_i
    for i in range(n):
        for j in range(n):
            if R[i][j] and e * exp[j] > _dot(obs[j][0], obs[i][1]):
                return True
    return False


def ccei(obs, tol=1e-9):
    """Critical Cost Efficiency Index. obs = [(price_vector, bundle), ...]."""
    if len(obs) < 2:
        return 1.0
    if not _violates_garp(obs, 1.0):
        return 1.0
    lo, hi = 0.0, 1.0
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if _violates_garp(obs, mid):
            hi = mid
        else:
            lo = mid
    return lo


def garp_ok(obs):
    """Binary GARP test (CCEI == 1)."""
    return not _violates_garp(obs, 1.0)


def recover_cd_exponent(obs):
    """
    Auditor's parameter recovery: mean budget share on good 1.
    For any Cobb-Douglas agent this IS the exponent. This is the number that
    gets contaminated by an epsilon-lexicographic loyalty.
    """
    shares = [p[0] * x[0] / _dot(p, x) for p, x in obs if _dot(p, x) > 0]
    return sum(shares) / len(shares)


def share_dispersion(obs):
    """
    Std-dev of budget shares. A true Cobb-Douglas agent (honest OR loyal) has
    dispersion ~0. Useful as a model-adequacy check before trusting CCEI.
    """
    shares = [p[0] * x[0] / _dot(p, x) for p, x in obs if _dot(p, x) > 0]
    m = sum(shares) / len(shares)
    return (sum((s - m) ** 2 for s in shares) / len(shares)) ** 0.5


# ------------------------------------------------------------------ self-test
if __name__ == "__main__":
    # A perfect Cobb-Douglas agent must score CCEI = 1.
    import random
    random.seed(0)
    obs = []
    for _ in range(25):
        p = (random.uniform(0.5, 3), random.uniform(0.5, 3))
        w = 100.0
        obs.append((p, (0.5 * w / p[0], 0.5 * w / p[1])))
    assert abs(ccei(obs) - 1.0) < 1e-9, "CD agent must be perfectly rational"

    # A genuine GARP violation: each bundle is strictly affordable at the other's
    # prices, yet the agent switched. At p=(1,1) it could have had (2,15) for 17
    # but spent 20 on (10,10); at p=(1,5) it could have had (10,10) for 60 but
    # spent 77 on (2,15). That cycle is exactly what GARP forbids.
    bad = [((1.0, 1.0), (10.0, 10.0)), ((1.0, 5.0), (2.0, 15.0))]
    assert not garp_ok(bad), "constructed violation must be caught"
    assert ccei(bad) < 1.0, "CCEI must fall below 1 on a real violation"
    print(f"ccei.py self-test passed  (violation case CCEI = {ccei(bad):.4f})")
