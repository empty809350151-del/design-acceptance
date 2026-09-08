# Overlay acceptance standard

## Comparison boundary

- Normalize both artifacts with an evidenced uniform scale, then crop to a common viewport. Preserve source captures and transforms. Review the changed module and related layout, not all visible page content by default.
- Mask only differences that are explicitly outside scope: system status bars, dynamic user data, copy-only changes, or a different underlying page when the reviewed component is a modal.
- Keep the mask visible as a toggle in the report so exclusions are auditable.
- A high average score never overrides a low-scoring critical region.

## Four required acceptance dimensions

Inspect each platform × case state × changed module in this order: **字号 → 颜色 → 间距 → 元素尺寸**. Review all applicable dimensions even when the overlay looks close. Record a conclusion for each in the coverage record: `passed`, `failed`, `pending`, or `not_applicable` (with a reason). Zero reported issues alone is not evidence of a completed check. Missing design properties or inconclusive screenshots mean pending, not passed.

Use Figma properties and layout rules for expected values; measure the implementation in normalized design coordinates. Distinguish direct implementation properties from screenshot estimates. Include the element, expected value, actual value/estimate, deviation, and measurement evidence. Use explicit project tolerances when available; record measurement uncertainty rather than inventing precise values from ambiguous pixels.

| Dimension | Required comparison | Report mapping |
| --- | --- | --- |
| 字号 | Compare one screenshot text element with its corresponding design text element, measuring font-size difference; account for font family, weight and wrapping when estimating size. | Flagged `fields` linked to issues; 字号问题 |
| 颜色 | Sample one element's color from the screenshot and compare it with the corresponding design element's color to determine consistency. Repeat for text, icons, fills, strokes and states. | `category: color`; 颜色问题 |
| 间距 | Parent padding, sibling gaps, text-to-icon gaps, section spacing and alignment relative to stable reference edges. | `category: spacing`; 间距问题 |
| 元素尺寸 | Compare one screenshot element with its corresponding design element to measure width/height and shape differences, including aspect ratio, corner radius and border thickness. | `category: size`; 元素尺寸问题 |

The four group headings follow Figma file `heWxFEtEUDsUYJjFqJ7zbS`, nodes `9:811`, `9:829`, `9:833`, `9:837` within `9:802`. They define report organization, not product acceptance values. Do not copy the reference's example counts or measurements into real findings.

## Pixel and structure (supporting diagnostics)

- Default perceptual threshold: YIQ `0.02`; exclude obvious antialiasing noise when the engine supports it.
- Pixel fidelity evaluates eligible pixels after masking.
- Structural fidelity evaluates grayscale edges at 2×, 4×, 8×, and 16× downsampling.
- Default combined score: `0.70 × pixel + 0.30 × structural`.
- Suggested pass rule: combined ≥95%, every critical region ≥90%, and no P0 defect.

Scores support diagnosis; they do not replace the four checks. A score meeting the suggested rule cannot pass a unit with a failed or pending dimension.

## Font-size checks

This is a hard requirement learned from a missed heading-size defect.

For every in-scope field:

1. Match one screenshot text element to its corresponding design text node and crop that pair separately. Repeat for every scoped text element; do not combine multiple fields into one font-size judgment.
2. Detect each glyph region and use the glyph's top-left ink pixel as the anchor.
3. Reposition the crops so those anchors overlap.
4. Compare ink height. Only for identical text with identical wrapping, also compare ink width. Valid multi-line text requires separate line-height, overflow and contextual spacing checks; global pixel displacement cannot decide that check.
5. Estimate that element's screenshot font size against the known design font size. Record design size, screenshot estimate and signed difference (`screenshot − design`), with the paired crops as evidence. Keep both crops at the common scale; do not resize them independently to fill equal-sized previews.
6. Flag a comparable field when `|Δ| ≥ 1.5px`; use stricter judgment when the design size is small or hierarchy changes visibly.

Do not infer font size from baseline position, container top, or whole-page overlay. These are separate measurements. Do not compare text width when the strings differ.

## Color checks

- Read expected fill/stroke colors, opacity, gradient stops and applicable state or variable mode from the matching design node. Record HEX/RGBA values when available.
- For each element, sample its color directly from the screenshot and compare it with the corresponding design element's color. Record the element/node identity, sample coordinates or region, screenshot HEX/RGB value, design color, and whether they match. Implementation style values may explain a mismatch but cannot replace screenshot sampling.
- Sample comparable interior regions, avoiding antialiased edges, shadows and compression noise. Sample the original screenshot to avoid colors introduced by resizing, and retain the mapping to normalized coordinates. For transparency, compare against the design color composited over the matching background; for gradients or multicolor elements, compare corresponding stops/regions rather than one average color. Account for color-profile differences before attributing a mismatch to the implementation.
- Check text, icons, surfaces, borders and selected/disabled states separately. A global pixel score cannot establish their color correctness. If no reliable sample exists, mark the check pending.
- Example issue: `按钮背景：设计 #0073FF，截图采样约 #1684FF；采样位置位于按钮中心纯色区域。`

## Spacing checks

- Measure parent-to-child padding and edge-to-edge sibling gaps in the shared coordinate space. Name both reference elements and the direction; do not report only absolute page coordinates.
- Inspect horizontal and vertical gaps, alignment, section spacing and text-to-icon distance. Keep line-height checks contextual; do not mistake glyph ink bounds for a text layout box.
- For permitted text reflow, compare the resulting gaps against the layout rule. Trace downstream displacement to its cause; do not duplicate a size defect as spacing defects unless an independent gap rule also fails.
- Example issue: `标题与说明的垂直间距：设计 12px，实测 20px，偏大 8px。`

## Element-size checks

- Match and crop one screenshot element and its corresponding design element at a time. Compare the pair side by side or by local overlay at the common scale; preserve original locations as evidence. Repeat for each scoped element instead of judging size from a whole-page similarity score.
- Compare width and height independently after uniform normalization; also inspect aspect ratio, radius and stroke thickness. Distinguish an icon's visible artwork from its outer frame and an image's crop from its container size.
- Record the element identity, design width/height, screenshot width/height and signed differences (`screenshot − design`), plus any observed shape difference. Keep boundaries equivalent on both sides (visible artwork to visible artwork, frame to frame).
- Respect fixed, hug-content and fill-container rules. Content-driven dimensions require checking the constraint and padding rather than enforcing the reference screenshot's fixed height.
- Never scale the target element itself to make its dimensions match. Keep the same normalization used for spacing checks.
- Example issue: `按钮：设计 120×40px，实测 120×48px，高度偏大 8px；圆角设计 20px，实测约 24px。`

## Severity

- P0 / critical: missing or wrong brand asset, critical interaction/structure defect, wrong component count/state, or a blocking modal/container error.
- P1 / high: clearly wrong component geometry, important typography hierarchy, or major position error.
- P2 / medium: local spacing, minor geometry, or non-blocking visual consistency issue.

Issue copy should be concise and target-oriented, for example: `设计稿：按钮 x=24px，y=1468px，702×84px，圆角42px。`

## Report presentation

- Ignore copy-only inconsistencies by default.
- Do not show left severity color bars.
- Use a restrained black/white editorial layout, light borders, and subtle pale green code chips.
- Avoid card shadows and ornamental gradients.
- Keep failure fields and issues flat and scannable.
- Default to actual/design side-by-side with an optional overlay view. Red boxes mark actual problems and green boxes mark design targets. Hide all boxes and badges until a problem is selected; show only that problem, retaining selection across view modes and clearing it across pages or on Escape.
