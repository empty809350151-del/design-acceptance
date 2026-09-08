# Report manifest schema

Use UTF-8 JSON. Start from `assets/example-manifest.json`.

## Root

- `meta`: `title`, `date`, `designer`, `frontend`; `project` supplies the requirement name in both the sidebar project title and header eyebrow; never place review status here. The sidebar brand is always `Design Acceptance`, independent of `title`. Optional `review_status` retains status metadata without replacing the requirement name. Platform owners come from each page.
- `pages`: ordered array; one object per platform × case state × scoped module, displayed as independent sidebar tabs. Keep unresolved/missing units in a sibling coverage JSON rather than inventing numeric metrics. For every unit, the coverage record must include `font_size`, `color`, `spacing`, and `element_size` conclusions (`passed`, `failed`, `pending`, or `not_applicable`) with evidence and reasons for pending/not applicable checks. This record is maintained by the reviewing agent; the builder does not infer completion from issue counts.

## Page

- `id`: stable lowercase slug.
- `title`, `lead`, `source`. Optional `nav_group` and `nav_label` group sidebar links; `figma_url` provides the real design destination. The icon and label remain visible but disabled when the URL is absent; never invent a destination.
- `platform`: APP or H5; `frontend`: owner of this platform; `case_id`, `state`: test context. These appear in the footer review context and platform appears in navigation. IDs must be unique across both platforms (for example `app-tc023-card`, `h5-tc023-card`).
- `metrics`: `overall`, `pixel`, `structural`, `critical`; numbers, not formatted strings.
- `viewport`: optional `[width,height]` comparison coordinate space; defaults to `[750,1624]`. Use the exact common crop so short components are not stretched to a phone-screen aspect ratio.
- `images`: used for both the central comparison and issue-card illustrations. Missing sources are explicitly labeled in cards. Paths for `actual`, `design`, optional `heatmap`, optional `mask`.
- `align_offset_percent`: optional percentage for moving the actual screenshot during anchor alignment.
- `scope_note`: short, user-readable exclusion note.
- `fields`: complete inspected field list.
- `issues`: failed issue list.

## Field

- `name`, `expected`, `estimate`, `delta`.
- `flag`: only flagged fields are shown as open cards.
- `actual_anchor`, `design_anchor`: `[x,y]` glyph anchors in normalized comparison pixels.
- `crop`: `[width,height]` for the anchor overlay crop.
- `actual_ink_height`, `design_ink_height`.
- `issue`: numeric issue ID used for screenshot focus.

## Issue

- `id`: one-based integer; must match SVG/overlay focus ordering.
- `severity`: `P0`, `P1`, or `P2`.
- Optional `category`: `color`, `spacing`, `size`, or `other`. Missing or unknown categories use Other; flagged font fields are grouped separately and do not duplicate their linked issue cards.
- For new reviews, explicitly classify color, spacing and element-size findings as `color`, `spacing`, and `size`; represent font-size findings through linked flagged `fields`. Follow 字号 → 颜色 → 间距 → 元素尺寸 order. Reserve `other` for additional blocking findings outside these dimensions, never for unclassified routine visual differences.
- `title`.
- `design`: concise comparison statement including design value, actual value (label screenshot estimates), deviation and element/reference location. The builder displays this text directly; do not add unsupported measurement fields expecting automatic rendering.
- `actual_rect`, `expected_rect`: `[x,y,width,height,radius]` in normalized comparison pixels. Both are hidden initially; selection shows only the matching issue. Side-by-side places actual boxes on the actual image and expected boxes on the design image.

Source image paths are resolved relative to the output HTML directory by the CLI, or an explicit `--asset-dir`. Python callers can pass `build(manifest, asset_dir=...)` (default: working directory). All image evidence is embedded as base64 in the generated HTML. Send only that HTML file; recipients do not need the original image folder. Download remote images first; missing or unsupported images fail generation. Raster formats: PNG, JPEG, WebP, GIF, BMP. Existing base64 raster data URIs are accepted. Optional design/test hyperlinks retain their source platform permissions.

The four standard issue categories remain visible even with no findings; zero counts use `#13B36B` and do not imply review completion. Each non-font issue automatically includes actual/design image crops using its rectangles; linked font fields use their glyph-anchor illustration.

## Image annotation data

All four categories include on-image labels. Font labels use `fields.estimate` / `fields.expected`; size rulers use rectangle widths/heights.

- Color issues: `annotation: {"actual": "#8C8A89", "design": "#5C5F66"}` displays sampled/expected hex colors with swatches. Use measured values; retain sampling uncertainty in `design`.
- Spacing issues: `annotation: {"axis": "x", "actual": 17, "design": 24}` (`y` for vertical) specifies measured gap and direction. Rectangles must span the measured gap on this axis, not the enclosing element. The ruler uses this axis only; do not invent spacing from an arbitrary bounding box.
- Missing color/spacing annotation values display 待测. For existing reports, copy only unambiguous recorded measurements into these fields, preserving original issue descriptions and uncertainty.

`meta.test_case_url` supplies the shared test-case document URL; optional `pages[].test_case_url` overrides it per unit. The header shows the test-case link next to the Figma link with matching typography, color, icon sizing and spacing. Missing URLs keep a disabled entry; do not substitute the presentation-reference Figma URL.
