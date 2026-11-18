"""Matplotlib helpers for the solid-liquid-gas reference figure style."""

from __future__ import annotations

import matplotlib as mpl


COLORS = ("#595959", "#F04A4A", "#2878D4", "#50A968", "#D88718")
MARKERS = ("s", "o", "^", "D", "v")


def configure() -> None:
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "axes.linewidth": 1.35,
        "axes.grid": False,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.minor.visible": False,
        "ytick.minor.visible": False,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })


def style_axis(ax: mpl.axes.Axes) -> None:
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(1.35)
    ax.grid(False)
    ax.minorticks_off()
    ax.tick_params(which="major", direction="in", top=True, right=True, width=1.35, length=6)


def plot_open_marker(ax: mpl.axes.Axes, x, y, *, index: int = 0, label: str | None = None, markevery: int = 1):
    """Plot a solid curve and open reference-style sample markers."""
    return ax.plot(
        x, y, color=COLORS[index % len(COLORS)], marker=MARKERS[index % len(MARKERS)],
        markerfacecolor="white", markeredgewidth=1.15, markersize=5.3,
        linewidth=1.75, markevery=markevery, label=label,
    )
