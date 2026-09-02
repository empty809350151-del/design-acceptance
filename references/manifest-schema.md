# Report manifest schema

Use UTF-8 JSON. Start from `assets/example-manifest.json`.

## Root

- `meta`: `title`, `date`, `designer`, `frontend`.
- `pages`: ordered array; one object per independent sidebar tab.

## Page

- `id`: stable lowercase slug.
- `title`, `lead`, `source`.
- `metrics`: `overall`, `pixel`, `structural`, `critical`; numbers, not formatted strings.
- `images`: paths for `actual`, `design`, optional `heatmap`, optional `mask`.
- `align_offset_percent`: optional percentage for moving the actual screenshot during anchor alignment.
- `scope_note`: short, user-readable exclusion note.
- `fields`: complete inspected field list.
- `issues`: failed issue list.

## Field

- `name`, `expected`, `estimate`, `delta`.
- `flag`: only flagged fields are shown as open cards.
- `actual_anchor`, `design_anchor`: `[x,y]` glyph anchors in original pixels.
- `crop`: `[width,height]` for the anchor overlay crop.
- `actual_ink_height`, `design_ink_height`.
- `issue`: numeric issue ID used for screenshot focus.

## Issue

- `id`: one-based integer; must match SVG/overlay focus ordering.
- `severity`: `P0`, `P1`, or `P2`.
- `title`.
- `design`: concise target statement.
- `actual_rect`, `expected_rect`: `[x,y,width,height,radius]` in original image pixels.

Paths are resolved relative to the generated HTML location. Keep images next to the report or use paths that remain valid after delivery.
