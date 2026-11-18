---
name: cmg-figure
description: Use when plotting three-dimensional CMG GEM CO2 transport results from .sr3 files, including gas saturation, pressure, full-grid transparency, model-boundary rendering, target-year extraction, or Chinese/English figure naming.
---

# CMG-FIGURE

## Overview

Use the verified project plotting implementation to turn completed CMG GEM `.sr3` outputs into publication-ready full-volume 3D figures. The result must show every grid block, emphasize CO2-bearing blocks, retain the actual model boundary, and keep saturation, pressure, typography, colorbars, and filenames consistent across cases.

This skill plots existing results. It does not edit `.dat` decks or claim that a GEM simulation completed.

## When to Use

Use this skill when the request mentions any of the following:

- CMG/GEM `.sr3`, `.out`, `.log`, `.rst`, or `.dat` result sets;
- 3D CO2 migration, gas saturation `SG`, pressure `PRES`, or full-grid visualization;
- the `101 x 101 x 131` model, target years `1, 2, 5, 10, 20, 50, 100`;
- transparent no-CO2 cells, a real model boundary, no internal mesh lines, or extra axis spacing;
- output names such as `4-S1-30Wt-100年.png`.

## Fixed Conventions

| Item | Required convention |
|---|---|
| Grid | Read the first `101 x 101 x 131` blocks from SR3; reshape `(NZ, NY, NX)` |
| Geometry | Read `SpatialProperties/000000/GRID/BLOCKDEPTH` and `BLOCKSIZE`; derive top/bottom boundaries from `dz` |
| CO2 presence | `SG > 1e-4` and finite value |
| Opacity | CO2 blocks `alpha=0.92`; no-CO2 blocks `alpha=0.01` |
| Block rendering | Plot all block centers as square markers; `linewidths=0`, no internal grid/mesh lines |
| Boundary | Draw actual top, bottom, four side surfaces and 12 outer edges; keep boundary independent of cell opacity |
| View | 3D axes, `view_init(elev=25, azim=-58)`, box aspect `(1, 1, 0.62)`, depth axis reversed |
| XY spacing | `AXIS_PAD=0.08`, so the model has visible front/back whitespace |
| Page margins | Strictly minimize unnecessary page-edge whitespace; retain only the space required for the 3D boundary, axis labels, colorbars, and annotations |
| Saturation | Fixed range `0-0.38`; `turbo` colormap |
| Pressure | `floor(min)` to `ceil(max)` in kPa; tick labels formatted as integers; `jet` colormap |
| Colorbars | Horizontal, below each subplot, compact padding; labels `SG (-)` and `压力 (kPa)` |
| Fonts | English/numerals Times New Roman; Chinese SimSun, with local fallback if unavailable |
| Titles | Figure: `{case}-{group}-{weight}-{year}年`; subplots: `饱和度-{year}年`, `压力-{year}年` |
| Output | PNG, `220 dpi`, under `{group}/figures/` |

## Workflow

1. Confirm the active project root is `E:\projects\cmg_agent` and inspect the relevant `guanwang/<group>` directory. The confirmed Python is `E:\APP\anaconda\envs\env_skill\python.exe`.
2. Treat `.sr3` as the plotting data source. Use `.out`/`.log` only to check whether the simulation has a normal-termination marker when completion matters. `.dat` and `.rst` are not substitutes for SR3 spatial properties.
3. Check the SR3 contains `General/MasterTimeTable`, `SpatialProperties`, `SpatialProperties/000000/GRID`, `BLOCKDEPTH`, `BLOCKSIZE`, `SG`, and `PRES` at the selected spatial output.
4. Select the nearest available spatial output to target days `365, 730, 1825, 3650, 7300, 18250, 36500`. Record the actual output day; do not silently call an unavailable timestep exact.
5. Use the existing implementation:

   ```powershell
   $py = 'E:\APP\anaconda\envs\env_skill\python.exe'
   Set-Location 'E:\projects\cmg_agent\guanwang'
   & $py '.\plot_group_volume_results.py' --group S1
   & $py '.\plot_group_volume_results.py' --group S2
   & $py '.\plot_group_volume_results.py' --group All
   ```

   Add `--case 1`, `--case 2`, `--case 3`, or `--case 4` for a single weight case. `S3` uses `S3\plot_s3_volume_results.py`; run it without `--case` when a complete S3 summary CSV is needed.

6. For each subplot, flatten the complete volume and draw absent blocks first (`s=0.45`), then CO2-bearing blocks (`s=2.2`) on top. Apply colors from the displayed variable but alpha from the CO2 presence mask. Draw the model boundary after the points.
7. Save the exact requested filename and verify the output count. For one group with four cases and seven years, expect `28` PNG files.

## Implementation Notes

The canonical implementation is:

- `E:\projects\cmg_agent\guanwang\S1\plot_co2_diagonal_section.py`: SR3 reading, geometry, boundary, font, and 3D panel primitives;
- `E:\projects\cmg_agent\guanwang\plot_group_volume_results.py`: batch generation for `S1`, `S2`, and `All`;
- `E:\projects\cmg_agent\guanwang\S3\plot_s3_volume_results.py`: S3 batch generation.

Do not replace the real boundary with a generic cuboid. The boundary surfaces use the SR3 top and bottom geometry and are padded from block-centered arrays to edge arrays. Keep `ax.grid(False)`, `edgecolor="none"`, and zero line width for cell markers.

The pressure range is calculated independently for each output year. Integer formatting means labels have no decimal places; it does not mean pressure data should be rounded before color mapping.

## Validation Checklist

- Confirm every requested SR3 opened successfully and the selected spatial output exists.
- Check the console reports the actual day for every target year.
- Check each PNG is non-empty and has two 3D subplots.
- Check titles and filenames use `1、2、5、10、20、50、100年` exactly.
- Check saturation colorbar spans `0` to `0.38`.
- Check pressure colorbar labels are integers.
- Check no-CO2 cells remain visible at 99% transparency, CO2 cells are visible, and no internal cell mesh is visible.
- Check the irregular/actual outer model boundary remains visible and XY axes have whitespace.
- Check exported outer page whitespace is minimized where compatible with the 3D boundary and colorbars; do not remove spacing required to show the actual model boundary.
- Check the summary CSV includes all cases. The batch script rewrites the CSV on each invocation; running one case at a time leaves a partial summary.

## Common Mistakes

| Mistake | Correction |
|---|---|
| Plotting only the diagonal section | Use `read_volume` and the full `NZ x NY x NX` cube for the requested 3D view |
| Omitting zero-CO2 blocks | Plot all finite blocks with `alpha=0.01`; do not filter them out |
| Drawing a generic wireframe box | Build the boundary from SR3 `BLOCKDEPTH` and `BLOCKSIZE` |
| Showing internal mesh lines | Use square markers with `linewidths=0` and no edge color |
| Using automatic saturation limits | Keep `vmin=0`, `vmax=0.38` for comparability |
| Calling nearest output an exact year | Report the actual MasterTimeTable day |
| Overwriting a complete summary with a one-case run | Run all cases in one batch or merge summaries explicitly |
| Running GEM just to make a figure | Plot the existing `.sr3`; simulation execution is a separate CMG workflow |
