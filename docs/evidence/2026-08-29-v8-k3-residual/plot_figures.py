"""Figures for H-V8-6. Reads figures_data.json — never the prose, and never re-deriving a
number the analysis already produced (two hand-maintained copies of a figure disagree the
moment one is updated).

Palette: the validated categorical default (blue #2a78d6, orange #eb6834), slots 1-2 in fixed
order, checked with the dataviz validator at light surface #fcfcfb — ALL CHECKS PASS, worst
adjacent CVD dE 24.7, normal-vision dE 33.6, both slots >= 3:1 contrast (validator output
committed as palette_validation.txt). Both series are also direct-labelled, so identity
never rests on colour.

Surface is OPAQUE light on purpose: a transparent PNG with dark text is unreadable on GitHub's
dark theme, and a single light card renders correctly under both themes.

Usage: python3 plot_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
D = json.load(open(HERE / "figures_data.json"))

SURFACE = "#fcfcfb"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e3e2df"
BLUE, ORANGE = "#2a78d6", "#eb6834"
KS = [1, 3, 5, 7]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.size": 9,
    "font.family": "DejaVu Sans", "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.titlecolor": INK,
})


def style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------- figure 1
def fig_k_curve(arm="A"):
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.1), sharey=True)
    panels = [("gate", "Scope gate\n(scope_verdict flips)"),
              ("label", "Op-point label\n(crosses 4.5 — what a reader sees)")]
    for ax, (est, title) in zip(axes, panels):
        style(ax)
        for st, colour, name in (("R", BLUE, "production-mix"), ("B", ORANGE, "boundary")):
            c = D["cells"][f"{est}|{arm}|{st}"]
            ys = [100 * c["residual"][str(k)] for k in KS]
            ax.plot(KS, ys, color=colour, linewidth=2, marker="o", markersize=6,
                    markeredgecolor=SURFACE, markeredgewidth=2, zorder=3, label=name)
            lo, hi = 100 * c["k3_ci"][0], 100 * c["k3_ci"][1]
            ax.plot([3, 3], [lo, hi], color=colour, linewidth=6, alpha=0.22,
                    solid_capstyle="butt", zorder=2)
            ax.annotate(f"{name}\n{ys[1]:.1f}% at k=3", (KS[-1], ys[-1]),
                        textcoords="offset points", xytext=(6, -2), color=colour,
                        fontsize=8, va="center", fontweight="bold")
        ax.set_title(title, fontsize=9.5, loc="left", pad=10)
        ax.set_xticks(KS)
        ax.set_xlabel("k  (oracle calls per article)")
        ax.set_xlim(0.6, 10.8)
    axes[0].set_ylabel("% of rows whose k-majority differs\nfrom the limit verdict")
    axes[0].set_ylim(0, 10)
    axes[0].legend(frameon=False, loc="upper right", fontsize=8, labelcolor=INK2)
    fig.suptitle("Repeating the oracle: what each extra pair of draws removes  "
                 "(reordered prompt; bands are 95% CI at k=3)",
                 fontsize=10.5, x=0.012, ha="left", color=INK, y=0.99)
    fig.text(0.012, 0.015,
             f"Each step of +2 draws costs ≈ ${D['corpus_rows'] * 2 * D['price'][arm][1]:.2f} "
             f"on a {D['corpus_rows']:,}-row corpus. The curve flattens because the residual is "
             f"rows the oracle has no stable answer for.", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.05, 0.995, 0.95))
    fig.savefig(HERE / "fig1_k_vs_residual.png", dpi=170)
    print("wrote fig1_k_vs_residual.png")


# ---------------------------------------------------------------- figure 2
def fig_fit_check(est="gate"):
    fig, axes = plt.subplots(2, 2, figsize=(8.6, 5.5))
    cells = [("A", "R"), ("A", "B"), ("B", "R"), ("B", "B")]
    names = {"A": "reordered", "B": "as-is", "R": "production-mix", "B_": "boundary"}
    for ax, (arm, st) in zip(axes.ravel(), cells):
        style(ax)
        c = D["cells"][f"{est}|{arm}|{st}"]
        xs = range(4)
        ax.bar([x - 0.20 for x in xs], c["observed"], width=0.33, color=BLUE,
               zorder=3, label="observed")
        ax.bar([x + 0.20 for x in xs], c["expected"], width=0.33, color=ORANGE,
               zorder=3, label="model")
        for x, (o, e) in enumerate(zip(c["observed"], c["expected"])):
            ax.text(x - 0.20, o, f"{o}", ha="center", va="bottom", fontsize=7.5, color=INK2)
            ax.text(x + 0.20, e, f"{e:.1f}", ha="center", va="bottom", fontsize=7.5, color=INK2)
        ax.set_xticks(list(xs))
        ax.set_xticklabels(["0 of 3", "1", "2", "3 of 3"])
        ax.set_title(f"{names[arm]} · {names['R'] if st == 'R' else names['B_']}  (n={c['n']})",
                     fontsize=9, loc="left")
        ax.set_ylim(0, max(max(c["observed"]), max(c["expected"])) * 1.28)
    axes[0][0].legend(frameon=False, fontsize=8, labelcolor=INK2)
    axes[1][0].set_xlabel("runs calling the article in_scope")
    axes[1][1].set_xlabel("runs calling the article in_scope")
    fig.suptitle("Does the model describe the data it was fitted to? "
                 "(scope gate; y-scale is per panel)",
                 fontsize=10.5, x=0.012, ha="left", color=INK, y=0.985)
    fig.text(0.012, 0.010,
             "Two free parameters against four cells leaves one degree of freedom, so a good fit "
             "here is a weak test.\nThe held-out check in the README — fit on two runs, predict "
             "the third — is the one that carries weight.", fontsize=8, color=INK2, linespacing=1.5)
    fig.tight_layout(rect=(0, 0.075, 1, 0.95))
    fig.savefig(HERE / "fig2_fit_check.png", dpi=170)
    print("wrote fig2_fit_check.png")


if __name__ == "__main__":
    fig_k_curve()
    fig_fit_check()
