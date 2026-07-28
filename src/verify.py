"""
Sanity-check the core claim of the 'lexicographic preferences as secret loyalty' idea:

  A loyalty that fires only in an epsilon-band of near-indifference around the
  Cobb-Douglas optimum is observationally indistinguishable from Cobb-Douglas
  under linear budget audits -- but diverges sharply on finite menus.
"""
import itertools, math, random
random.seed(0)

A = 0.5          # true CD exponent on good 1 ("principal's dimension")
EPS = 0.10       # loyalty band: accept up to 10% CD-utility loss to favour principal

def cd(x, a=A):
    return (x[0] ** a) * (x[1] ** (1 - a))

def cd_demand(p, w, a=A):
    return (a * w / p[0], (1 - a) * w / p[1])

def loyal_demand(p, w, a=A, eps=EPS):
    """max x1 on the budget line s.t. u(x) >= (1-eps) * u*(p,w). Solved by bisection on share s."""
    ustar = cd(cd_demand(p, w, a), a)
    lo, hi = a, 1.0 - 1e-12
    for _ in range(200):
        s = (lo + hi) / 2
        x = (s * w / p[0], (1 - s) * w / p[1])
        if cd(x, a) >= (1 - eps) * ustar:
            lo = s
        else:
            hi = s
    return (lo * w / p[0], (1 - lo) * w / p[1])

# ---------------------------------------------------------------- claim 1
# The loyal agent's budget share on good 1 is CONSTANT across prices/incomes,
# i.e. it is exactly a Cobb-Douglas agent with a shifted exponent.
print("=== Claim 1: loyal agent's budget share is price/income invariant ===")
shares = []
for _ in range(12):
    p = (random.uniform(0.3, 4.0), random.uniform(0.3, 4.0))
    w = random.uniform(10, 400)
    x = loyal_demand(p, w)
    shares.append(p[0] * x[0] / w)
print(f"  true CD exponent a       = {A}")
print(f"  loyal share min/max      = {min(shares):.6f} / {max(shares):.6f}")
print(f"  spread                   = {max(shares)-min(shares):.2e}  (0 => exactly CD)")
a_hat = sum(shares) / len(shares)
print(f"  auditor's recovered a-hat= {a_hat:.6f}")

# ---------------------------------------------------------------- claim 2
# GARP / Afriat CCEI on a simulated black-box audit of the loyal agent.
def ccei(obs):
    """Afriat efficiency index via bisection on e: largest e with no GARP violation."""
    n = len(obs)
    def violates(e):
        # direct revealed preference at efficiency level e
        D = [[False] * n for _ in range(n)]
        for i, (p, w, x) in enumerate(obs):
            for j, (_, _, y) in enumerate(obs):
                if e * (p[0] * w[0] + p[1] * w[1]) >= p[0] * y[0] + p[1] * y[1]:
                    D[i][j] = True
        # transitive closure
        R = [row[:] for row in D]
        for k in range(n):
            for i in range(n):
                if R[i][k]:
                    for j in range(n):
                        if R[k][j]:
                            R[i][j] = True
        # GARP violation: x_i R x_j and x_j strictly cheaper-than-affordable at p_i
        for i, (p, w, x) in enumerate(obs):
            for j, (q, v, y) in enumerate(obs):
                if R[i][j] and q[0] * x[0] + q[1] * x[1] < e * (q[0] * y[0] + q[1] * y[1]):
                    return True
        return False
    lo, hi = 0.0, 1.0
    if not violates(1.0):
        return 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if violates(mid):
            hi = mid
        else:
            lo = mid
    return lo

print("\n=== Claim 2: black-box budget audit (GARP / Afriat CCEI) ===")
for label, demand in [("control (honest CD)", cd_demand), ("loyal (eps-lexicographic)", loyal_demand)]:
    obs = []
    for _ in range(40):
        p = (random.uniform(0.5, 3.0), random.uniform(0.5, 3.0))
        w = 100.0
        x = demand(p, w)
        obs.append((p, x, x))   # (prices, chosen bundle, chosen bundle)
    obs = [(p, x, x) for (p, x, _) in obs]
    print(f"  {label:26s} CCEI = {ccei(obs):.4f}   (1.0 = perfectly rational, audit finds nothing)")

# ---------------------------------------------------------------- claim 3
# Finite menu: the loyalty becomes decisive and visible ONLY if the auditor
# happens to construct a near-tied menu.
print("\n=== Claim 3: finite-menu divergence (where the loyalty actually bites) ===")
def choose_from_menu(menu, loyal, eps=EPS):
    best = max(cd(x) for x in menu)
    if not loyal:
        return max(menu, key=lambda x: cd(x))
    band = [x for x in menu if cd(x) >= (1 - eps) * best]
    return max(band, key=lambda x: x[0])       # principal's dimension breaks the tie

def random_menu(k=4, gap=None):
    """gap=None -> generic menu; gap=small -> deliberately near-tied menu."""
    menu = []
    for _ in range(k):
        w = random.uniform(50, 150)
        s = random.uniform(0.15, 0.85)
        menu.append((s * w, (1 - s) * w))
    return menu

for tag, tight in [("generic menus", False), ("near-tied menus (tie-break stress test)", True)]:
    diverge = 0
    trials = 3000
    for _ in range(trials):
        if tight:
            # construct options within ~5% CD-utility of each other
            base = random.uniform(60, 120)
            menu = []
            for _ in range(4):
                s = random.uniform(0.2, 0.8)
                scale = base / (s ** A * (1 - s) ** (1 - A))
                menu.append((s * scale * random.uniform(0.97, 1.03),
                             (1 - s) * scale * random.uniform(0.97, 1.03)))
        else:
            menu = random_menu()
        if choose_from_menu(menu, False) != choose_from_menu(menu, True):
            diverge += 1
    print(f"  {tag:42s} divergence rate = {diverge/trials:6.1%}")
