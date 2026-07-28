"""
DO TIE-BREAKERS ACTUALLY OCCUR?

The Arrow claim in the paper is currently asserted: "any aggregating system needs a
tie-breaking rule, and it is guaranteed to be invoked." This script turns that into
a measurement. No API calls -- pure simulation, so this section is submittable
regardless of the LLM runs.

Two independent mechanisms put a decision into the tie-breaker:

  (A) AGGREGATION CYCLES. With >=3 alternatives, pairwise majority can be
      intransitive (Condorcet paradox) -> no Condorcet winner -> the system must
      fall back on a tie-breaking rule. Benchmark: Guilbaud's number, P ~ 0.0877
      for m=3 as n->infinity under impartial culture (Gehrlein & Fishburn).

  (B) NEAR-INDIFFERENCE. A single agent choosing from a finite menu finds two or
      more options within epsilon of its optimum -> the epsilon-band loyalty is
      decisive.

Both are ACTIVATION-side quantities: they measure how often the loyalty gets an
opportunity, not how much damage it can do once it has one.
"""
import itertools, random, statistics

A = 0.5          # Cobb-Douglas exponent, matches organism.py
TRIALS = 40000


# ------------------------------------------------------- (A) aggregation cycles
def has_condorcet_winner(profile, m):
    """profile = list of preference orders (tuples, best first). Odd n => no pairwise ties."""
    rank = [{alt: i for i, alt in enumerate(order)} for order in profile]
    for x in range(m):
        if all(
            sum(r[x] < r[y] for r in rank) * 2 > len(profile)
            for y in range(m) if y != x
        ):
            return True
    return False


def cycle_rate(n, m, trials=TRIALS, seed=0):
    """P(no Condorcet winner) under impartial culture."""
    rng = random.Random(seed)
    base = list(range(m))
    miss = 0
    for _ in range(trials):
        profile = []
        for _ in range(n):
            o = base[:]
            rng.shuffle(o)
            profile.append(tuple(o))
        if not has_condorcet_winner(profile, m):
            miss += 1
    return miss / trials


# --------------------------------------------------- (B) near-indifference rate
def cd(x):
    return (x[0] ** A) * (x[1] ** (1 - A)) if x[0] > 0 and x[1] > 0 else 0.0


def activation_rate(eps, k, trials=TRIALS, seed=0, spread=1.0):
    """
    P(the epsilon-band contains >1 option AND the loyalty changes the choice).

    Two numbers, and the difference matters:
      opportunity  - band is non-singleton (loyalty *could* act)
      decisive     - loyalty's pick differs from the honest pick (loyalty *does* act)
    """
    rng = random.Random(seed)
    opp = dec = 0
    for _ in range(trials):
        menu = []
        for _ in range(k):
            w = rng.uniform(100 - 40 * spread, 100 + 40 * spread)
            s = rng.uniform(0.2, 0.8)
            menu.append((s * w, (1 - s) * w))
        u = [cd(x) for x in menu]
        best = max(u)
        band = [i for i in range(k) if u[i] >= (1 - eps) * best]
        if len(band) > 1:
            opp += 1
        honest = max(range(k), key=lambda i: u[i])
        loyal = max(band, key=lambda i: menu[i][0])
        if loyal != honest:
            dec += 1
    return opp / trials, dec / trials


# ------------------------------------------------------------------------ main
if __name__ == "__main__":
    print("=" * 74)
    print("(A) AGGREGATION CYCLES — P(no Condorcet winner), impartial culture")
    print("=" * 74)
    print(f"{'voters n':>9}" + "".join(f"{'m=' + str(m):>10}" for m in (3, 4, 5, 6, 7)))
    for n in (3, 5, 11, 25, 51, 101):
        row = "".join(f"{cycle_rate(n, m, seed=n * 100 + m):>10.3%}" for m in (3, 4, 5, 6, 7))
        print(f"{n:>9}" + row)
    print("\nBenchmark: Guilbaud's number, m=3 as n->inf, P ~ 8.77%.")
    print("Read the columns, not the rows: cycle frequency climbs steeply with the")
    print("number of alternatives. A tie-breaker is not an edge case in a rich")
    print("choice set — it is routine.")

    print("\n" + "=" * 74)
    print("(B) NEAR-INDIFFERENCE — how often an epsilon-band loyalty gets its chance")
    print("=" * 74)
    print(f"{'eps':>7}" + "".join(f"{'k=' + str(k):>22}" for k in (2, 4, 8)))
    print(f"{'':>7}" + "".join(f"{'opportunity':>12}{'decisive':>10}" for _ in range(3)))
    for eps in (0.005, 0.01, 0.02, 0.05, 0.10, 0.25):
        cells = ""
        for k in (2, 4, 8):
            o, d = activation_rate(eps, k, seed=int(eps * 1000) + k)
            cells += f"{o:>12.1%}{d:>10.1%}"
        print(f"{eps:>7.1%}" + cells)
    print("\n'opportunity' = band contains >1 option. 'decisive' = loyalty changes")
    print("the choice. Decisive is the number to report: it is the activation rate.")

    print("\n" + "=" * 74)
    print("(C) THE COMPOSITE CLAIM")
    print("=" * 74)
    c3 = cycle_rate(51, 3, seed=1)
    c7 = cycle_rate(51, 7, seed=2)
    _, d1 = activation_rate(0.01, 4, seed=3)
    _, d10 = activation_rate(0.10, 4, seed=4)
    print(f"  A loyalty that costs 1% of stated objective value is decisive in")
    print(f"  {d1:.1%} of 4-option decisions; at 10% it is decisive in {d10:.1%}.")
    print(f"  Independently, a 51-voter aggregator over 3 alternatives has no")
    print(f"  Condorcet winner {c3:.1%} of the time; over 7 alternatives, {c7:.1%}.")
    print(f"  Neither channel is rare. Narrow activation is not narrow in practice.")
