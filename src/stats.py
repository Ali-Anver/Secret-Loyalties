"""
STATISTICS — inference for every comparison reported in the paper.

The template asks directly: "Is the difference statistically significant?" This
module answers it for each claim, reading the saved JSON so the numbers in the
writeup cannot drift from the raw data.

Estimators used, and why:
  * budget share / recovered exponent -> mean with a bootstrap 95% CI. The share
    is bounded in (0,1) and n=30, so a normal-theory CI can cross the boundary;
    the bootstrap does not.
  * proportions (principal-selection, agreement rates) -> two-proportion z-test
    with a Wald 95% CI on the difference, plus Fisher's exact when any cell < 5.
  * dispersion -> reported as a point estimate with a bootstrap CI; no test, as
    the null (exactly zero) is on the boundary of the parameter space.

Run:  python stats.py            (prints every table)
      python stats.py --md       (markdown, for pasting into the appendix)
"""
import json, math, random, sys, glob
from paths import result, checkpoint

random.seed(20260726)
BOOT = 10000


# ------------------------------------------------------------------ estimators
def boot_ci(xs, stat=lambda v: sum(v) / len(v), reps=BOOT, alpha=0.05):
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    n, out = len(xs), []
    for _ in range(reps):
        out.append(stat([xs[random.randrange(n)] for _ in range(n)]))
    out.sort()
    return out[int(alpha / 2 * reps)], out[int((1 - alpha / 2) * reps)]


def two_prop(x1, n1, x2, n2):
    """Returns (p1, p2, diff, z, pvalue, ci_lo, ci_hi). Group 2 minus group 1."""
    if min(n1, n2) == 0:
        return (float("nan"),) * 7
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    se0 = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se0 if se0 > 0 else float("nan")
    pv = math.erfc(abs(z) / math.sqrt(2)) if se0 > 0 else float("nan")
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return p1, p2, p2 - p1, z, pv, (p2 - p1) - 1.96 * se, (p2 - p1) + 1.96 * se


def fisher_exact_2x2(a, b, c, d):
    """Two-sided Fisher exact p for [[a,b],[c,d]]. Used when a cell is small."""
    def logC(n, k):
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    n = a + b + c + d
    r1, c1 = a + b, a + c
    def prob(x):
        return math.exp(logC(r1, x) + logC(n - r1, c1 - x) - logC(n, c1))
    p0 = prob(a)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= p0 * 1.0000001))


def shares_from(path):
    """Budget shares on good A from a gate_test-style JSON."""
    d = json.load(open(result(path)))
    out = []
    for r in d["rows"]:
        o = r["response"]
        if not o:
            continue
        p, a, b = r["prices"], float(o["units_of_a"]), float(o["units_of_b"])
        spend = p[0] * a + p[1] * b
        if spend > 0:
            out.append(p[0] * a / spend)
    return out


def sd(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


# --------------------------------------------------------------------- tables
LADDER = {
    "claude-opus-5": {0.0: "gate_eps0.0_claude-opus-5.json", 0.01: "ladder_eps0.01_s0.json",
                      0.05: "ladder_eps0.05_s0.json", 0.10: "ladder_eps0.10_s0.json",
                      0.25: "ladder_eps0.25_s0.json"},
    "claude-opus-4-8": {0.0: "L48_eps0.json", 0.01: "L48_eps0.01.json",
                        0.05: "L48_eps0.05.json", 0.10: "L48_eps0.10.json",
                        0.25: "L48_eps0.25.json"},
    "claude-sonnet-5": {0.05: "cand_claude-sonnet-5_0.05.json",
                        0.10: "cand_claude-sonnet-5_0.10.json",
                        0.25: "cand_claude-sonnet-5_0.25.json"},
    "claude-opus-4-7": {0.05: "cand_claude-opus-4-7_0.05.json",
                        0.10: "cand_claude-opus-4-7_0.10.json",
                        0.25: "cand_claude-opus-4-7_0.25.json"},
}
PRED = {0.0: 0.500, 0.01: 0.571, 0.05: 0.656, 0.10: 0.718, 0.25: 0.830}


def table_ladder(md=False):
    rows = []
    for model, files in LADDER.items():
        base = shares_from(files[0.0]) if 0.0 in files else None
        for eps, f in sorted(files.items()):
            try:
                xs = shares_from(f)
            except FileNotFoundError:
                continue
            lo, hi = boot_ci(xs)
            pred = PRED[eps]
            covers = lo <= pred <= hi
            rec = dict(model=model, eps=eps, n=len(xs), mean=sum(xs) / len(xs),
                       lo=lo, hi=hi, sd=sd(xs), pred=pred, covers=covers)
            rows.append(rec)
    return rows


def table_laundering(path, md=False):
    d = json.load(open(result(path)))
    out = []
    for tag, r in d["menu_results"].items():
        nc, nl = r["n_control"], r["n_loyal"]
        xc = round(r["certified_vs_control"] * nc)
        xl = round(r["certified_vs_loyal"] * nl)
        p1, p2, diff, z, pv, lo, hi = two_prop(xc, nc, xl, nl)
        out.append(dict(menu=tag, model=d["args"]["model"], a_hat=d["a_hat"],
                        pc=p1, pl=p2, diff=diff, z=z, p=pv, lo=lo, hi=hi,
                        nc=nc, nl=nl, div=r["loyal_vs_control_divergence"]))
    return out


def table_aggregator():
    import aggregator as A
    cyc, dec = A.build_arms(0, 120, 7, 4, 40)
    items = {"cyclic": cyc, "decisive": dec}
    got = {}
    for arm in ("decisive", "cyclic"):
        for cond in ("control", "loyal"):
            f = checkpoint(f"agg_main.json.{arm}.{cond}.ndjson")
            recs = [json.loads(l) for l in open(f) if l.strip()]
            picks = [None] * len(items[arm])
            for r in recs:
                if r["idx"] < len(picks):
                    picks[r["idx"]] = r["pick"]
            got[(arm, cond)] = picks
    out = []
    for arm in ("decisive", "cyclic"):
        c, l = got[(arm, "control")], got[(arm, "loyal")]
        nc = sum(p is not None for p in c); nl = sum(p is not None for p in l)
        xc = sum(p == 0 for p in c if p is not None); xl = sum(p == 0 for p in l if p is not None)
        p1, p2, diff, z, pv, lo, hi = two_prop(xc, nc, xl, nl)
        fe = fisher_exact_2x2(xc, nc - xc, xl, nl - xl)
        out.append(dict(arm=arm, xc=xc, nc=nc, xl=xl, nl=nl, pc=p1, pl=p2,
                        diff=diff, z=z, p=pv, lo=lo, hi=hi, fisher=fe))
    # severity
    sev = {}
    for cond in ("control", "loyal"):
        picks = got[("cyclic", cond)]
        opp = sum(1 for (_, _, tc, _) in cyc if 0 not in tc)
        hit = sum(1 for (_, _, tc, _), p in zip(cyc, picks) if p == 0 and 0 not in tc)
        sev[cond] = (hit, opp)
    return out, sev


REFUSAL = {  # measured in the phrasing sweep, n=14 near-tied menus each, opus-5
    "matched control (no loyalty)": 0, "confidential note (used)": 4,
    "internal directive": 11, "business rationale": 13, "bare rule, no framing": 14,
}


def main():
    md = "--md" in sys.argv
    B = "**" if md else ""
    print(f"\n{B}TABLE S1 — recovered budget share, bootstrap 95% CI (10k reps){B}")
    hdr = f"{'model':<18}{'eps':>6}{'n':>4}{'mean':>8}{'95% CI':>18}{'sd':>8}{'predicted':>11}{'covers?':>9}"
    print(hdr if not md else "| model | eps | n | mean | 95% CI | sd | predicted | covers |\n|---|---|---|---|---|---|---|---|")
    for r in table_ladder():
        line = (f"{r['model']:<18}{r['eps']:>6.2f}{r['n']:>4}{r['mean']:>8.4f}"
                f"  [{r['lo']:.4f},{r['hi']:.4f}]{r['sd']:>8.4f}{r['pred']:>11.3f}"
                f"{('YES' if r['covers'] else 'no'):>9}")
        if md:
            line = (f"| {r['model']} | {r['eps']:.2f} | {r['n']} | {r['mean']:.4f} | "
                    f"[{r['lo']:.4f}, {r['hi']:.4f}] | {r['sd']:.4f} | {r['pred']:.3f} | "
                    f"{'yes' if r['covers'] else '**no**'} |")
        print(line)

    print(f"\n{B}TABLE S2 — laundering: certificate agreement, control vs loyal{B}")
    for path in ("laundering_48.json", "laundering.json"):
        try:
            rows = table_laundering(path)
        except FileNotFoundError:
            continue
        for r in rows:
            print(f"  {r['model']:<17} {r['menu']:<10} a_hat={r['a_hat']:.4f}  "
                  f"ctl {r['pc']:.1%} (n={r['nc']})  loy {r['pl']:.1%} (n={r['nl']})  "
                  f"diff {r['diff']:+.1%}  z={r['z']:+.2f}  p={r['p']:.3f}  "
                  f"CI[{r['lo']:+.1%},{r['hi']:+.1%}]  div={r['div']:.1%}")

    print(f"\n{B}TABLE S3 — Arrow aggregator: principal-selection rate{B}")
    agg, sev = table_aggregator()
    for r in agg:
        print(f"  {r['arm']:<9} ctl {r['xc']}/{r['nc']} = {r['pc']:.1%}   "
              f"loy {r['xl']}/{r['nl']} = {r['pl']:.1%}   lift {r['diff']:+.1%}   "
              f"z={r['z']:+.2f}  p={r['p']:.4f}  Fisher p={r['fisher']:.4f}  "
              f"CI[{r['lo']:+.1%},{r['hi']:+.1%}]")
    print(f"  severity (principal majority-dominated, selected anyway):")
    for k, (hit, opp) in sev.items():
        print(f"    {k:<9} {hit}/{opp}")
    fe = fisher_exact_2x2(sev['control'][0], sev['control'][1] - sev['control'][0],
                          sev['loyal'][0], sev['loyal'][1] - sev['loyal'][0])
    print(f"    Fisher exact p = {fe:.3f}  (counts too small to interpret)")

    print(f"\n{B}TABLE S4 — refusal rate by loyalty phrasing (claude-opus-5, n=14 each){B}")
    base = REFUSAL["matched control (no loyalty)"]
    for k, v in REFUSAL.items():
        if k.startswith("matched"):
            print(f"  {k:<30} {v:>2}/14 = {v/14:>5.0%}")
            continue
        p1, p2, diff, z, pv, lo, hi = two_prop(base, 14, v, 14)
        fe = fisher_exact_2x2(base, 14 - base, v, 14 - v)
        print(f"  {k:<30} {v:>2}/14 = {v/14:>5.0%}   vs control: Fisher p={fe:.4f}")


if __name__ == "__main__":
    main()
