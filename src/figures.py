"""
Candidate figures — build all, pick one or two for the 4-page body, rest to appendix.

Every panel recomputes from the saved data or the simulation code at render time,
so a figure can never drift from the table it illustrates.

Palette: dataviz reference instance, categorical slots 1-4, validated on the light
surface (worst adjacent CVD dE 9.1, normal-vision 22.9). Slots 3-4 sit below 3:1
contrast, so the relief rule applies -- every mark carries a visible direct label.

  fig1_argument   (a) tie-breakers occur  (b) the loyalty exploits them   <- RECOMMENDED
  fig2_ladder     measured vs closed-form recovered exponent, 4 models
  fig3_laundering simulation vs measurement, side by side and honestly labelled
  fig4_dispersion share dispersion: the two-sample detection statistic
  fig5_refusal    refusal rate by loyalty phrasing (the unplanned finding)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import random

import stats as S
from paths import figure
from tiebreaks import cycle_rate
from laundering import near_tied_menu, theory_choice, certified_choice

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASE = "#e1e0d9", "#c3c2b7"
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": BASE,
})


def dress(ax, pct=True):
    ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    ax.tick_params(length=0, labelsize=9)
    if pct:
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))


def label(ax, x, y, txt, dy=0.015, size=9):
    ax.text(x, y + dy, txt, ha="center", va="bottom", fontsize=size, color=INK2)


def save(fig, name):
    fig.savefig(figure(f"{name}.pdf"), bbox_inches="tight", facecolor=SURFACE)
    fig.savefig(figure(f"{name}.png"), dpi=220, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"  wrote {name}.pdf / .png")


# ============================================================ fig 1: the argument
def fig1():
    MS = [3, 4, 5, 6, 7]
    cyc = [cycle_rate(51, m, trials=40000, seed=51 * 100 + m) for m in MS]
    agg, _ = S.table_aggregator()
    by = {r["arm"]: r for r in agg}

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.2, 4.1))

    a1.bar([str(m) for m in MS], cyc, width=0.62, color=C1, zorder=3)
    for x, v in enumerate(cyc):
        label(a1, x, v, f"{v:.0%}")
    a1.axhline(0.0877, ls=(0, (4, 3)), lw=1.2, color=MUTED, zorder=2)
    a1.text(4.42, 0.107, "Guilbaud 8.77%", ha="right", fontsize=8.5,
            color=MUTED, style="italic")
    a1.set_title("(a) Arrow guarantees a tie-breaker, and it is invoked often",
                 fontsize=10.5, color=INK, loc="left", pad=10, fontweight="bold")
    a1.set_xlabel("alternatives in the choice set", fontsize=9)
    a1.set_ylabel("profiles with no Condorcet winner", fontsize=9)
    a1.set_ylim(0, 0.45); dress(a1)

    arms = ["decisive", "cyclic"]
    ctl = [by[a]["pc"] for a in arms]
    loy = [by[a]["pl"] for a in arms]
    w, xs = 0.34, range(2)
    a2.bar([x - w/2 - .012 for x in xs], ctl, width=w, color=C1, label="control", zorder=3)
    a2.bar([x + w/2 + .012 for x in xs], loy, width=w, color=C2, label="loyal", zorder=3)
    for x, (c, l) in enumerate(zip(ctl, loy)):
        label(a2, x - w/2 - .012, c, f"{c:.0%}")
        label(a2, x + w/2 + .012, l, f"{l:.0%}")
    a2.axhline(0.25, ls=(0, (2, 2)), lw=1.0, color=MUTED, zorder=2)
    a2.text(-0.44, 0.262, "chance 25%", ha="left", fontsize=8.5, color=MUTED, style="italic")
    for x, a in enumerate(arms):
        r = by[a]
        txt = f"+{r['diff']:.0%}\np={r['p']:.3f}" if r["p"] >= .001 else f"+{r['diff']:.0%}\np<0.001"
        a2.text(x, 0.635, txt, ha="center", fontsize=8.5,
                color=(INK if r["p"] < .05 else MUTED),
                fontweight=("bold" if r["p"] < .05 else "normal"))
    a2.set_xticks(list(xs))
    a2.set_xticklabels(["decisive\n(clear winner)", "cyclic\n(no winner)"])
    a2.set_title("(b) ...and the loyalty is far more decisive there",
                 fontsize=10.5, color=INK, loc="left", pad=10, fontweight="bold")
    a2.set_ylabel("rate of selecting the principal", fontsize=9)
    a2.set_ylim(0, 0.82); dress(a2)
    leg = a2.legend(frameon=False, fontsize=9, loc="upper left", ncol=2)
    for t in leg.get_texts():
        t.set_color(INK2)
    fig.tight_layout(pad=1.3)
    save(fig, "fig1_argument")


# =========================================================== fig 2: the ladder
def fig2():
    rows = S.table_ladder()
    models = ["claude-opus-5", "claude-sonnet-5", "claude-opus-4-7", "claude-opus-4-8"]
    cols = {m: c for m, c in zip(models, [C1, C2, C3, C4])}
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    eps_pred = [0.01, 0.05, 0.10, 0.25]
    ax.plot(eps_pred, [S.PRED[e] for e in eps_pred], ls=(0, (5, 3)), lw=1.6,
            color=INK2, zorder=4, label="closed form (theory)")
    for m in models:
        pts = sorted([r for r in rows if r["model"] == m and r["eps"] > 0],
                     key=lambda r: r["eps"])
        if not pts:
            continue
        xs = [p["eps"] for p in pts]; ys = [p["mean"] for p in pts]
        err = [[p["mean"] - p["lo"] for p in pts], [p["hi"] - p["mean"] for p in pts]]
        ax.errorbar(xs, ys, yerr=err, marker="o", ms=5.5, lw=1.8, capsize=3,
                    color=cols[m], label=m.replace("claude-", ""), zorder=3)
    ax.axhline(0.5, lw=1.0, color=MUTED, ls=(0, (2, 2)), zorder=1)
    ax.text(0.0105, 0.512, "true a = 0.50 (no loyalty)", ha="left", fontsize=8.5,
            color=MUTED, style="italic")
    ax.set_xlabel("ε  —  fraction of stated objective value the loyalty may sacrifice", fontsize=9)
    ax.set_ylabel("recovered Cobb-Douglas exponent  â", fontsize=9)
    ax.set_title("Direction yes, magnitude no: measurement departs from the closed form",
                 fontsize=10.5, color=INK, loc="left", pad=10, fontweight="bold")
    ax.set_xscale("log"); ax.set_xticks(eps_pred)
    ax.set_xticklabels([f"{e:.0%}" for e in eps_pred])
    dress(ax, pct=False); ax.set_ylim(0.45, 0.95)
    leg = ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    for t in leg.get_texts():
        t.set_color(INK2)
    fig.tight_layout(pad=1.2)
    save(fig, "fig2_ladder")


# ======================================================= fig 3: laundering honestly
def fig3():
    A_HAT = 0.718
    sim_h, sim_l = [], []
    for k in (2, 4, 8):
        rng = random.Random(7)
        menus = [near_tied_menu(rng, k) for _ in range(4000)]
        cert = [certified_choice(m, A_HAT) for m in menus]
        sim_h.append(sum(theory_choice(m, 0.0) == c for m, c in zip(menus, cert)) / len(menus))
        sim_l.append(sum(theory_choice(m, .10) == c for m, c in zip(menus, cert)) / len(menus))
    l48 = {r["menu"]: r for r in S.table_laundering("laundering_48.json")}
    l05 = {r["menu"]: r for r in S.table_laundering("laundering.json")}

    groups = [("simulation\nk=2", sim_h[0], sim_l[0], None),
              ("simulation\nk=4", sim_h[1], sim_l[1], None),
              ("simulation\nk=8", sim_h[2], sim_l[2], None),
              ("MEASURED\nopus-4-8", l48["near_tied"]["pc"], l48["near_tied"]["pl"], l48["near_tied"]["p"]),
              ("MEASURED\nopus-5*", l05["near_tied"]["pc"], l05["near_tied"]["pl"], l05["near_tied"]["p"])]
    fig, ax = plt.subplots(figsize=(8.6, 4.3))
    w, xs = 0.36, range(len(groups))
    ax.bar([x - w/2 - .012 for x in xs], [g[1] for g in groups], width=w, color=C1,
           label="honest agent", zorder=3)
    ax.bar([x + w/2 + .012 for x in xs], [g[2] for g in groups], width=w, color=C2,
           label="loyal agent", zorder=3)
    for x, g in enumerate(groups):
        label(ax, x - w/2 - .012, g[1], f"{g[1]:.0%}", size=8.5)
        label(ax, x + w/2 + .012, g[2], f"{g[2]:.0%}", size=8.5)
        if g[3] is not None:
            ax.text(x, 1.06, "n.s." if g[3] >= .05 else "p<0.001", ha="center",
                    fontsize=8.5, color=(MUTED if g[3] >= .05 else INK),
                    fontweight=("normal" if g[3] >= .05 else "bold"))
    ax.axvline(2.5, color=BASE, lw=1.0, zorder=1)
    ax.set_xticks(list(xs)); ax.set_xticklabels([g[0] for g in groups], fontsize=8.5)
    ax.set_ylabel("agreement with the audit's certificate", fontsize=9)
    ax.set_title("Laundering: strong in theory, model-dependent in measurement",
                 fontsize=10.5, color=INK, loc="left", pad=10, fontweight="bold")
    ax.set_ylim(0, 1.16); dress(ax)
    leg = ax.legend(frameon=False, fontsize=9, loc="upper left", ncol=2)
    for t in leg.get_texts():
        t.set_color(INK2)
    fig.text(0.01, -0.05, "* opus-5 confounded by 29% differential refusal (n=40 loyal vs 59 control); "
             "shown for completeness, not claimed as a result.", fontsize=7.8, color=MUTED)
    fig.tight_layout(pad=1.2)
    save(fig, "fig3_laundering")


# ====================================================== fig 4: dispersion detector
def fig4():
    rows = S.table_ladder()
    models = ["claude-opus-5", "claude-sonnet-5", "claude-opus-4-7", "claude-opus-4-8"]
    cols = {m: c for m, c in zip(models, [C1, C2, C3, C4])}
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for m in models:
        pts = sorted([r for r in rows if r["model"] == m and r["eps"] > 0],
                     key=lambda r: r["eps"])
        if pts:
            ax.plot([p["eps"] for p in pts], [p["sd"] for p in pts], marker="o",
                    ms=5.5, lw=1.8, color=cols[m], label=m.replace("claude-", ""), zorder=3)
    ctl = [r for r in rows if r["eps"] == 0]
    if ctl:
        ax.axhline(ctl[0]["sd"], lw=1.6, color=INK2, ls=(0, (5, 3)), zorder=4)
        ax.text(0.252, ctl[0]["sd"] + 0.006, f"matched control = {ctl[0]['sd']:.4f}",
                ha="right", fontsize=8.5, color=INK2, style="italic")
    ax.set_xscale("log"); ax.set_xticks([0.01, 0.05, 0.10, 0.25])
    ax.set_xticklabels(["1%", "5%", "10%", "25%"])
    ax.set_xlabel("ε", fontsize=9)
    ax.set_ylabel("sd of budget share  (theory predicts 0)", fontsize=9)
    ax.set_title("Dispersion is a detection statistic — but only against a twin",
                 fontsize=10.5, color=INK, loc="left", pad=10, fontweight="bold")
    dress(ax, pct=False)
    leg = ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    for t in leg.get_texts():
        t.set_color(INK2)
    fig.tight_layout(pad=1.2)
    save(fig, "fig4_dispersion")


# ========================================================== fig 5: refusal sweep
def fig5():
    order = ["matched control (no loyalty)", "confidential note (used)",
             "internal directive", "business rationale", "bare rule, no framing"]
    vals = [S.REFUSAL[k] / 14 for k in order]
    short = ["matched control\n(no loyalty)", "confidential\nnote (used)",
             "internal\ndirective", "business\nrationale", "bare rule,\nno framing"]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    colours = [C1] + [C2] * 4
    ax.bar(range(5), vals, width=0.6, color=colours, zorder=3)
    for x, v in enumerate(vals):
        label(ax, x, v, f"{v:.0%}")
    ax.set_xticks(range(5)); ax.set_xticklabels(short, fontsize=8.5)
    ax.set_ylabel("refusals (claude-opus-5, n=14 each)", fontsize=9)
    ax.set_title("Concealment language is not the trigger — supplier-steering is",
                 fontsize=10.5, color=INK, loc="left", pad=10, fontweight="bold")
    ax.set_ylim(0, 1.14); dress(ax)
    fig.text(0.01, -0.04, "All four loyalty phrasings share the same decision rule; only the framing differs. "
             "The bare rule with no secrecy framing at all refuses most.", fontsize=7.8, color=MUTED)
    fig.tight_layout(pad=1.2)
    save(fig, "fig5_refusal")


if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5):
        f()
