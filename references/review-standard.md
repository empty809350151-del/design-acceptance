# Overlay acceptance standard

## Comparison boundary

- Crop both artifacts to a common viewport before analysis.
- Mask only differences that are explicitly outside scope: system status bars, dynamic user data, copy-only changes, or a different underlying page when the reviewed component is a modal.
- Keep the mask visible as a toggle in the report so exclusions are auditable.
- A high average score never overrides a low-scoring critical region.

## Pixel and structure

- Default perceptual threshold: YIQ `0.02`; exclude obvious antialiasing noise when the engine supports it.
- Pixel fidelity evaluates eligible pixels after masking.
- Structural fidelity evaluates grayscale edges at 2×, 4×, 8×, and 16× downsampling.
- Default combined score: `0.70 × pixel + 0.30 × structural`.
- Suggested pass rule: combined ≥95%, every critical region ≥90%, and no P0 defect.

Scores support diagnosis; they do not replace visual inspection.

## Font-size checks

This is a hard requirement learned from a missed heading-size defect.

For every visible field:

1. Crop the same field from implementation and design.
2. Detect each glyph region and use the glyph's top-left ink pixel as the anchor.
3. Reposition the crops so those anchors overlap.
4. Compare ink height. For identical text, also compare ink width.
5. Estimate the implementation size against the known design font size.
6. Flag a comparable field when `|Δ| ≥ 1.5px`; use stricter judgment when the design size is small or hierarchy changes visibly.

Do not infer font size from baseline position, container top, or whole-page overlay. These are separate measurements. Do not compare text width when the strings differ.

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
- The actual screenshot is the framing surface: red dashed boxes mark problems and green dashed boxes mark design targets.
