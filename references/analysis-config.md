# Analysis configuration

`scripts/analyze_overlay.py` accepts a JSON file with:

- `actual`, `design`: PNG paths.
- `output_dir`, `slug`: output destination and stable page slug.
- `viewport`: `[width,height]` common comparison crop in design pixels, positive integers.
- `actual_transform`, `design_transform`: optional `{source_rect: [x0,y0,x1,y1], scale: 0.5, origin: [x,y]}`. Crop the original image first, resize uniformly, then take `viewport` at `origin` in the resized image. Defaults are full source, scale 1 and origin [0,0]. Out-of-bounds crops fail rather than padding missing evidence.
- `include_rects`: optional union of in-scope rectangles; everything outside is excluded. Omit for the whole contextual crop.
- `threshold`: default `0.02` YIQ distance.
- `exclude_rects`: rectangles `[x0,y0,x1,y1]` excluded from scoring.
- `fields`: field measurement definitions.

Each field contains:

- `name`, `expected`, `actual_rect`, `design_rect`;
- optional `same_text` and `same_wrap` (default true), `mode` (`dark` or `light`), `crop`, and `issue`. Width estimates require both same_text and same_wrap. Otherwise use first-line ink height as supporting evidence and inspect line-height/wrapping separately.

All field/include/exclude rectangles use `[x0,y0,x1,y1]` with exclusive right/bottom edges in the final normalized crop. Issue rectangles in the report instead use `[x,y,width,height,radius]`. Do not mix source and normalized coordinates.

The script writes `<slug>-actual.png`, `<slug>-design.png`, `<slug>-heatmap.png`, `<slug>-mask.png`, and `<slug>-metrics.json`. Use these normalized images in the report. Metrics retain transforms and scope rectangles; preserve original captures separately. Fully excluded scopes fail instead of scoring 100%. It uses a YIQ perceptual threshold and multi-scale grayscale edge F1. It does not decide severity or infer valid text reflow.

Example: a 1170px-wide device content viewport and a 750px-wide matching design export imply scale `750/1170`, AFTER cropping status/browser chrome. A different CSS breakpoint is not solved by scaling; select the right design variant. Never calculate scale from the target module's width, since that can hide a width defect.
