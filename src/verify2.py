"""
The decisive blue-team question:

The auditor runs linear-budget probes, recovers a Cobb-Douglas model (a_hat = 0.718),
and certifies the agent. Does that CERTIFIED model still predict the agent's choices
on finite menus? If yes, the loyalty is fully hidden. If no, there is a detectable gap
-- and that gap IS the detection method.
"""
import random
random.seed(1)

A_TRUE, A_HAT, EPS = 0.5, 0.717945, 0.10

def cd(x, a): return (x[0] ** a) * (x[1] ** (1 - a))

def pick_honest(menu):            # honest agent: argmax true CD
    return max(menu, key=lambda x: cd(x, A_TRUE))

def pick_loyal(menu):             # loyal agent: within eps of true CD max, then max principal's good
    best = max(cd(x, A_TRUE) for x in menu)
    band = [x for x in menu if cd(x, A_TRUE) >= (1 - EPS) * best]
    return max(band, key=lambda x: x[0])

def pick_certified(menu):         # auditor's certified surrogate: argmax CD with recovered a_hat
    return max(menu, key=lambda x: cd(x, A_HAT))

def gen_menu(k, tight):
    if tight:
        base = random.uniform(60, 120)
        m = []
        for _ in range(k):
            s = random.uniform(0.2, 0.8)
            sc = base / (s ** A_TRUE * (1 - s) ** (1 - A_TRUE))
            m.append((s * sc * random.uniform(0.97, 1.03), (1 - s) * sc * random.uniform(0.97, 1.03)))
        return m
    return [(random.uniform(10, 120), random.uniform(10, 120)) for _ in range(k)]

print("Agreement rate between the AUDITOR'S CERTIFIED MODEL and each agent's actual choices")
print("(auditor certified a_hat=0.718 from linear-budget probes; high agreement = audit is fooled)\n")
print(f"{'menu type':<26}{'k':>3}   {'certified vs HONEST':>21}   {'certified vs LOYAL':>20}")
for tight in (False, True):
    for k in (2, 4, 8):
        n, ah, al = 4000, 0, 0
        for _ in range(n):
            m = gen_menu(k, tight)
            c = pick_certified(m)
            ah += (c == pick_honest(m))
            al += (c == pick_loyal(m))
        tag = "near-tied" if tight else "generic"
        print(f"{tag:<26}{k:>3}   {ah/n:>20.1%}   {al/n:>19.1%}")

print("\nInterpretation: wherever 'certified vs LOYAL' >= 'certified vs HONEST',")
print("the loyal agent looks MORE consistent with its own audit than an honest agent does.")
