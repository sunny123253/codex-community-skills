---
name: solid-liquid-gas-figure-style
description: Recreate scientific line, scatter, validation, and multi-panel figures in the laboratory's solid-liquid-gas reference style. Use when restyling or creating publication figures from CSV data, especially when the reference uses a full black frame, inward ticks, Times-style text, white background, gray/red/blue curves, and open square/circle/triangle data markers.
---

# Solid-liquid-gas reference figure style

## Style contract

- Use a white background, no grid and no minor ticks.
- Use Times New Roman for Latin text and numerals. Use STIX/Times-like math text. For Chinese labels, use SimSun when available.
- Keep all four black spines. Set their line width to approximately 1.35 pt.
- Draw major ticks inward on bottom/top/left/right. Use 6 pt long, 1.35 pt wide ticks; do not show top/right tick labels unless they convey a second axis.
- Use solid lines about 1.75 pt wide. Overlay white-filled markers at sampled data points: gray square, red circle and blue triangle, in that order. Use a 1.15 pt marker edge and a compact 5.3 pt marker size.
- Use `#595959`, `#F04A4A` and `#2878D4` as the default gray/red/blue sequence. Extend with `#50A968` or `#D88718` only when necessary.
- Keep legends frameless; prefer short labels and avoid covering data.
- Strictly control image-edge whitespace: remove unnecessary blank bands while retaining enough space for labels, legends, colorbars, and all plotted data.
- For multi-panel figures, place bold panel tags a, b, c... just outside the upper-left plotting area. Use shared x axes where it improves comparison.
- Export PNG and TIFF at 600 dpi, plus PDF and SVG. Inspect the PNG visually before delivery.

## Matplotlib baseline

Copy `scripts/reference_style.py` into the analysis directory, call `configure()` before constructing figures, then use `style_axis(ax)` for every axes and `plot_open_marker(...)` for sampled series. Preserve source data and write figures from a repeatable script; never edit an exported raster by hand.

## Validation

- Confirm no grid or minor tick remains.
- Confirm every axis has black top/right spines and inward major ticks.
- Confirm fonts, marker fill, line thickness and legend placement remain legible at the final page width.
- Compare the final raster side-by-side with the supplied reference before replacing older exports.
- Verify that exported edge whitespace is minimized and that no text, tick, legend, colorbar, or plotted data is clipped.
