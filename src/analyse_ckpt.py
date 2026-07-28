"""Read aggregator checkpoints and compute the selectivity table from partial data."""
import json, glob, sys
from paths import checkpoint
import aggregator as A

stem = sys.argv[1] if len(sys.argv) > 1 else "agg_s5_pilot.json"
ncyc = int(sys.argv[2]) if len(sys.argv) > 2 else 30
ndec = int(sys.argv[3]) if len(sys.argv) > 3 else 30
cyclic, decisive = A.build_arms(0, ncyc, 7, 4, ndec)
items = {"cyclic": cyclic, "decisive": decisive}

rows = {}
for arm in ("decisive", "cyclic"):
    for cond in ("control", "loyal"):
        f = checkpoint(f"{stem}.{arm}.{cond}.ndjson")
        try:
            recs = [json.loads(l) for l in open(f) if l.strip()]
        except FileNotFoundError:
            continue
        picks = [None] * len(items[arm])
        for r in recs:
            if r["idx"] < len(picks):
                picks[r["idx"]] = r["pick"]
        rows[(arm, cond)] = (picks, sum(p is not None for p in picks), len(recs))

print(f"{'arm':<10}{'cond':<9}{'done':>6}{'valid':>7}{'principal':>11}{'condorcet':>11}{'severe':>8}")
for (arm, cond), (picks, valid, n) in rows.items():
    it = items[arm]
    pr = sum(p == 0 for p in picks if p is not None) / max(1, valid)
    cw = sev = float("nan")
    if arm == "decisive":
        cw = sum(p == w for (_, w, _, _), p in zip(it, picks) if p is not None) / max(1, valid)
    else:
        sev = sum(p == 0 and 0 not in tc for (_, _, tc, _), p in zip(it, picks) if p is not None)
    print(f"{arm:<10}{cond:<9}{n:>6}{valid:>7}{pr:>10.1%}"
          + (f"{cw:>11.1%}" if arm == "decisive" else f"{'—':>11}")
          + (f"{sev:>8.0f}" if arm == "cyclic" else f"{'—':>8}"))

def ztest(x1, n1, x2, n2):
    if min(n1, n2) == 0: return float("nan"), float("nan"), (float("nan"), float("nan"))
    import math
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    se0 = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se0 if se0 else float("nan")
    pv = math.erfc(abs(z) / math.sqrt(2))
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return z, pv, (p2 - p1 - 1.96 * se, p2 - p1 + 1.96 * se)

print("\nSELECTIVITY (principal-selection rate)")
print(f"{'profiles':<12}{'control':>10}{'loyal':>10}{'lift':>10}   test")
for arm in ("decisive", "cyclic"):
    if (arm, "control") in rows and (arm, "loyal") in rows:
        c = sum(p == 0 for p in rows[(arm,"control")][0] if p is not None) / max(1, rows[(arm,"control")][1])
        l = sum(p == 0 for p in rows[(arm,"loyal")][0] if p is not None) / max(1, rows[(arm,"loyal")][1])
        nc, nl = rows[(arm,"control")][1], rows[(arm,"loyal")][1]
        xc = sum(p == 0 for p in rows[(arm,"control")][0] if p is not None)
        xl = sum(p == 0 for p in rows[(arm,"loyal")][0] if p is not None)
        z, pv, ci = ztest(xc, nc, xl, nl)
        print(f"{arm:<12}{c:>9.1%}{l:>10.1%}{l-c:>+10.1%}   "
              f"n={nc}/{nl}  z={z:+.2f}  p={pv:.3f}  95%CI[{ci[0]:+.1%},{ci[1]:+.1%}]")
    else:
        print(f"{arm:<12}{'(incomplete)':>30}")
