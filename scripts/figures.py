# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Regenerate committed SVG figures from data/*.json into figures/.

Run via `npm run figures` (called before dev/build) or directly with
`uv run scripts/figures.py` — uv resolves the matplotlib dependency declared
in the inline metadata above, so there's no venv to manage or commit.

Figures are styled to the site's design tokens (colours hard-coded to match
tokens.css) and written with `svg.fonttype='none'` so the text stays as real
<text> and inherits the page's sans stack.
"""

import json
import pathlib
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "benchmark.json").read_text())

# ── Design tokens (mirror of tokens.css; SVG can't read CSS vars) ──
INK_SOFT = "#33322e"
MUTED    = "#54534b"
FAINT    = "#84837a"
RULE     = "#ddd9cd"
ACCENT   = "#9a2b1d"
GREEN    = "#1d6e56"   # NPSS fast-equilibrium
FILL = {"fast": GREEN, "npss": MUTED, "py": ACCENT}

plt.rcParams.update({
    "svg.fonttype": "none",
    "font.family": "Gill Sans, Gill Sans MT, Avenir Next, system-ui, sans-serif",
    "text.color": MUTED,
    "axes.edgecolor": FAINT,
})


def timing_figure(rows, headline):
    labels = [r["label"] for r in rows]
    vals   = [r["ms"] for r in rows]
    colors = [FILL[r["kind"]] for r in rows]
    y = range(len(rows))

    fig, ax = plt.subplots(figsize=(6.0, 2.9))
    ax.barh(y, vals, color=colors, height=0.62, zorder=3)

    ax.set_xscale("log")
    ax.set_xlim(1, 10_000)
    ax.set_yticks(list(y), labels, fontsize=9, color=MUTED)
    ax.invert_yaxis()                          # first row on top
    ax.set_xticks([1, 10, 100, 1000, 10_000],
                  ["1 ms", "10 ms", "100 ms", "1 s", "10 s"],
                  fontsize=8, color=FAINT)
    ax.tick_params(length=0)

    # Tufte-ish chrome: drop the box, keep faint vertical gridlines only.
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=RULE, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)

    # Value labels: outside short bars, inside long ones.
    for yi, v in zip(y, vals):
        if v < 100:
            txt = f"{v:.1f} ms"
        elif v >= 1000:
            txt = f"{v:,.0f} ms"   # comma thousands, matches the table
        else:
            txt = f"{v:.0f} ms"
        if v < 100:
            ax.text(v * 1.15, yi, txt, va="center", ha="left",
                    fontsize=8.5, color=INK_SOFT, family="monospace", zorder=4)
        else:
            ax.text(v * 0.92, yi, txt, va="center", ha="right",
                    fontsize=8.5, color="#faf9f6", family="monospace", zorder=4)

    # Headline annotation: dashed marker at the fast bar between the two rows.
    idx = {r["label"]: i for i, r in enumerate(rows)}
    if headline["from"] in idx and headline["to"] in idx:
        xv = rows[idx[headline["to"]]]["ms"]
        i0, i1 = idx[headline["from"]], idx[headline["to"]]
        ax.plot([xv, xv], [min(i0, i1) + 0.3, max(i0, i1) - 0.3],
                color=ACCENT, lw=0.8, ls=(0, (3, 3)), zorder=5)
        ax.text(xv * 1.2, (i0 + i1) / 2, headline["factor"],
                color=ACCENT, fontsize=8.5, style="italic", va="center", zorder=5)

    ax.set_title("Per-solve median time — log scale",
                 fontsize=8.5, color=FAINT, loc="left", pad=10)

    fig.tight_layout()
    out = ROOT / "figures" / "timing.svg"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"wrote {out.relative_to(ROOT)}")


timing_figure(DATA["solve_timing"], DATA["headline"])
