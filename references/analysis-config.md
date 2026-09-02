# Analysis configuration

`scripts/analyze_overlay.py` accepts a JSON file with:

- `actual`, `design`: PNG paths.
- `output_dir`, `slug`: output destination and stable page slug.
- `viewport`: `[width,height]` common crop.
- `threshold`: default `0.02` YIQ distance.
- `exclude_rects`: rectangles `[x0,y0,x1,y1]` excluded from scoring.
- `fields`: field measurement definitions.

Each field contains:

- `name`, `expected`, `actual_rect`, `design_rect`;
- optional `same_text` (default true), `mode` (`dark` or `light`), `crop`, and `issue`.

The script writes `<slug>-heatmap.png`, `<slug>-mask.png`, and `<slug>-metrics.json`. It uses a YIQ perceptual threshold and multi-scale grayscale edge F1. It does not decide severity; inspect component meaning and interaction state separately.
