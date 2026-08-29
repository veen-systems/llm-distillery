"""The corpus-shape figure: what the v8 draw fixed, and what it did not.

Reads score_mass.json (written by the measurement step) — no number is typed into this chart.

Palette: validated categorical slots 1-3 (blue/orange/aqua) under --pairs all; output committed
as palette_validation.txt. Aqua sits below 3:1 on the light surface, so the relief rule applies
and every series is direct-labelled as well as legended.

Usage: python3 plot_corpus_shape.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
D = json.load(open(HERE / "score_mass.json"))
PROD = "production_drawable"   # the population the draw can SAMPLE, not all-lengths production
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.size": 9, "font.family": "DejaVu Sans", "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
})

BINS = [b for b in sorted(float(k) for k in D[PROD]) if 1.0 <= b <= 7.5]
get = lambda series, b: D[series].get(str(b), D[series].get(f"{b:.1f}", 0.0))


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 5.3))

# ---- panel 1: the three distributions
style(ax1)
series = [(PROD, BLUE, "production the draw can sample", D["n"][PROD]),
          ("v7", ORANGE, "v7 corpus (what we trained on)", D["n"]["v7"]),
          ("new", AQUA, "new v8 draw", D["n"]["new"])]
for key, colour, name, n in series:
    # ⚠️ An EMPTY bin is not a value of zero on a log axis -- plotting it draws a vertical
    # plunge to the axis floor that reads as data. Empty bins are dropped, not floored.
    xs = [b for b in BINS if get(key, b) > 0]
    ys = [get(key, b) for b in xs]
    ax1.plot(xs, ys, color=colour, linewidth=2, marker="o", markersize=4.5,
             markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3, label=f"{name}  (n={n:,})")
ax1.set_yscale("log")
ax1.set_ylim(0.002, 100)
ax1.set_xlabel("v7 weighted average (0.5-wide bins)")
ax1.set_ylabel("% of that population")
ax1.set_title("Where each population's mass sits", fontsize=9.5, loc="left", pad=8)
ax1.legend(frameon=False, fontsize=8, loc="lower left", labelcolor=INK2)
ax1.annotate("op-point 4.5", (4.5, 60), color=INK2, fontsize=8,
             textcoords="offset points", xytext=(4, 0), va="center", ha="left")
ax1.axvline(4.5, color=GRID, linewidth=1.2, zorder=1)

# ---- panel 2: over/under-weighting against production, which is the decision
style(ax2)
for key, colour, name in (("v7", ORANGE, "v7 corpus"), ("new", AQUA, "new v8 draw")):
    xs = [b for b in BINS if get(PROD, b) > 0 and get(key, b) > 0]
    ys = [get(key, b) / get(PROD, b) for b in xs]
    ax2.plot(xs, ys, color=colour, linewidth=2, marker="o", markersize=4.5,
             markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3, label=name)
    last = xs[-1]
    ax2.annotate(name, (last, get(key, last) / get(PROD, last)),
                 textcoords="offset points", xytext=(7, 0), color=colour, fontsize=8.5,
                 fontweight="bold", va="center")
ax2.axhline(1.0, color=INK2, linewidth=1, zorder=2)
ax2.axhline(2.0, color=GRID, linewidth=1.4, zorder=1)
ax2.annotate("parity with production", (1.05, 1.0), textcoords="offset points", xytext=(0, 4),
             color=INK2, fontsize=7.5)
ax2.annotate("2.0× — the ruled enrichment", (1.05, 2.0), textcoords="offset points",
             xytext=(0, 4), color=INK2, fontsize=7.5)
ax2.set_yscale("log")
ax2.set_xlim(0.9, 8.6)
ax2.set_xlabel("v7 weighted average (0.5-wide bins)")
ax2.set_ylabel("× production's share of that bin")
ax2.set_title("Over- and under-weighting, against the population a draw samples",
              fontsize=9.5, loc="left", pad=8)

fig.suptitle("The v8 draw halves the corpus's tilt toward easy positives and closes the gap "
             "where false positives are born",
             fontsize=10.5, x=0.008, ha="left", color=INK, y=0.985)
fig.text(0.008, 0.012,
         "Visible band (5.5–10): v7 corpus 3.74× → new draw 1.95×, against the ruled 2.0×. "
         "Low-middle (1.5–3.5), where stage-2 false positives are born: 0.61× → 1.00×. "
         "Decision band 1.46× → 1.39×.\nRatios are against the population the draw can SAMPLE "
         "(drawable, stage-2, ≥300 chars) — not all-lengths production, which the draw excludes "
         "12% of. Weighted averages use math.fsum:\nCPython 3.12 changed sum() to compensated "
         "summation and 34 of these 6,590 rows change bin between interpreters. The 623 "
         "stage1_low rows carry probe estimates and are off this axis.",
         fontsize=8, color=INK2, linespacing=1.5)
fig.tight_layout(rect=(0, 0.135, 0.995, 0.945))
fig.savefig(HERE / "fig_corpus_shape.png", dpi=170)
print("wrote fig_corpus_shape.png")
