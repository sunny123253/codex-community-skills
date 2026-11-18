---
name: scientific-plotting
description: Use when creating, editing, or reviewing scientific research figures, publication plots, Matplotlib/Seaborn/R/Origin-like charts, line plots, point-line plots, scatter plots, dot plots, axes, ticks, fonts, color palettes, markers, or grid styling.
---

# Scientific Plotting

## Core Rule

Default to clean publication-style figures: Chinese text in Songti/SimSun (宋体), Western text and numerals in Times New Roman, inward major ticks, no minor ticks, and no grid unless the user explicitly requests one. Control image-edge whitespace strictly: remove unnecessary blank bands while preserving every data boundary, label, legend, colorbar, and annotation.

## Required Defaults

| Element | Default |
|---|---|
| Chinese font | 宋体 / SimSun. If unavailable, ask before substituting. |
| Western font | Times New Roman. |
| Math text | STIX/Times-like math where possible. |
| Major ticks | Point inward on line plots, point-line plots, scatter plots, and dot plots. |
| Minor ticks | Off. Do not add minor ticks unless requested. |
| Single-y-axis top/right ticks | Off. Keep top/right spines unless the user asks to remove the frame. |
| Grid | Off unless specifically requested. |
| Background | White, publication-clean. |
| Page margins | Strictly minimize unnecessary edge whitespace; verify after export and never clip text, data, legends, colorbars, or boundaries. |

## Color Sequence

Use this sequence first, cycling only after it is exhausted:

```text
#4D4D4D, #F23B3B, #2E75B6, #3CA65A, #A879D9, #D69A00,
#00A7A7, #7F4C4C, #7A7A00, #E56B00, #6F97C5, #60B800
```

For monochrome or accessibility-sensitive output, preserve line style and marker differences as well as color.

## Point And Marker Style

For point-line plots, place markers at every data point unless density makes this unreadable. Use solid black or series-colored marker edges, compact marker sizes, and simple filled shapes. Prefer this marker cycle:

```text
s, o, ^, v, D, <, >, h, *, p
```

The first marker may be an open square with colored edge and no fill when matching the provided reference style. Use black filled circle/triangle/diamond styles when the plot has a single series or when the user asks for the exact reference feel.

## Matplotlib Pattern

Use this pattern as the baseline for Python/Matplotlib figures. Do not run Python commands until the project Python environment is confirmed by local project instructions.

```python
import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler

SCIENTIFIC_COLORS = [
    "#4D4D4D", "#F23B3B", "#2E75B6", "#3CA65A", "#A879D9", "#D69A00",
    "#00A7A7", "#7F4C4C", "#7A7A00", "#E56B00", "#6F97C5", "#60B800",
]

MARKERS = ["s", "o", "^", "v", "D", "<", ">", "h", "*", "p"]

mpl.rcParams.update({
    "font.family": ["Times New Roman", "SimSun"],
    "font.serif": ["Times New Roman", "SimSun"],
    "font.sans-serif": ["SimSun", "Times New Roman"],
    "mathtext.fontset": "stix",
    "axes.unicode_minus": False,
    "axes.grid": False,
    "axes.prop_cycle": cycler(color=SCIENTIFIC_COLORS),
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.minor.visible": False,
    "ytick.minor.visible": False,
})

fig, ax = plt.subplots(figsize=(3.5, 2.6), dpi=300)

for i, (x, y, label) in enumerate(series):
    ax.plot(
        x, y,
        color=SCIENTIFIC_COLORS[i % len(SCIENTIFIC_COLORS)],
        marker=MARKERS[i % len(MARKERS)],
        markersize=5,
        markeredgewidth=1.0,
        linewidth=1.4,
        label=label,
    )

ax.grid(False)
ax.minorticks_off()
ax.tick_params(axis="both", which="major", direction="in", top=False, right=False)
ax.tick_params(axis="both", which="minor", bottom=False, top=False, left=False, right=False)

ax.set_xlabel("Time (s)")
ax.set_ylabel("Response")
ax.legend(frameon=False)
fig.tight_layout(pad=0.2)
# If manual layout is needed, tighten each edge independently and reserve only
# the space required by labels, legends, colorbars, and annotations.
```

For a single-series reference-style open square:

```python
ax.plot(
    x, y,
    color="#F23B3B",
    marker="s",
    markerfacecolor="none",
    markeredgecolor="#E56B00",
    markeredgewidth=1.4,
    markersize=5.5,
    linewidth=1.4,
)
```

## Review Checklist

Before delivering a scientific plot, check:

- Chinese text renders as 宋体/SimSun and Western text renders as Times New Roman.
- Major ticks point inward.
- Minor ticks are absent.
- Single-y-axis figures do not show top or right ticks.
- Grid lines are absent unless requested.
- Colors follow the specified sequence.
- Point-line markers follow the compact reference style.
- Edge whitespace is tightly controlled, with no clipped labels, legends, colorbars, data, or boundaries.
