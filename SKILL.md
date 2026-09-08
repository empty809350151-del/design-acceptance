---
name: design-acceptance
description: Review APP and H5 screenshots from test-case documents against matching Figma designs within the development scope. Normalize capture scale, distinguish valid content reflow, and generate side-by-side and overlay HTML acceptance reports. Use for visual design acceptance and screenshot-versus-Figma QA; not for implementing the product UI itself.
---

# Design Acceptance

Produce an evidence-backed visual acceptance result and a reusable HTML preview. Review every scoped unit in this order: **字号 (font size), 颜色 (color), 间距 (spacing), 元素尺寸 (element size)**. Pixel and structural scores are supporting diagnostics, not substitutes for these four checks. Preserve existing pages when appending another review.

## Required workflow

For font size, color and element size, compare **one screenshot element against its corresponding design element** at a time. Crop each pair for font-size and element-size comparison; preserve the common scale so size differences remain visible. For color, sample the element directly from the screenshot and compare with the corresponding design color; implementation style values may support diagnosis but cannot replace screenshot sampling. Retain paired element locations and measurement evidence for each conclusion.

1. Read the test-case document and development scope. Extract original embedded images or original attachments with their case ID, heading, expected result, platform, state and source location. Do not assume screenshots live in Figma. Follow references/test-case-intake.md; retain missing APP/H5 coverage explicitly.
2. Build separate review units for platform × case state × changed module. Record the APP and H5 frontend owners separately. Keep the original page screenshot as context; review only the changed module and its relevant parent, sibling, spacing and interaction relationships.
3. Retrieve Figma metadata, design context and exact component screenshots. Map each test screenshot using case context, route/page, component identity, state and platform variant. Record candidate nodes and supporting evidence. Do not force ambiguous matches; mark them pending and continue independent matches.
4. Normalize source screenshots into design coordinates using an evidenced uniform scale after removing system/browser chrome. Record original dimensions, crop, scale and anchors. Never resize each axis independently or fit the changed element's own dimensions to the design; that hides geometry defects. Different responsive layouts require a matching design variant or rule-based review.
5. Separate comparable pixels from legal content reflow. For one-line versus permitted two-line text, inspect line count, line height, overflow and sibling spacing against layout rules. Compare stable local blocks separately without erasing unexpected movement. Preserve the original context and document allowed reflow; do not score global displacement as a defect automatically.
6. Run scripts/analyze_overlay.py with a config for each comparable region. Use include_rects for scoped metrics and exclude_rects for justified differences. Use its normalized actual/design outputs in the report. Review each in-scope text field by glyph anchor; use same_text=false or same_wrap=false as appropriate. Missing evidence or fully excluded scopes are unscorable, never passed.
7. Complete all four checks in references/review-standard.md for each unit. Record each dimension as passed, failed, pending evidence, or not applicable with a reason in the coverage record. Write concise issues with design value, actual value or labeled estimate, deviation and location, tied to platform, case and scope. Group them in order: 字号问题 → 颜色问题 → 间距问题 → 元素尺寸问题. Add independent units to the report manifest. Default to actual/design side-by-side; offer overlay mode. Show only the selected issue's rectangles after a click or keyboard activation; clear selection on page change.
8. Verify JSON, assets, unique IDs, JavaScript syntax and browser interactions, including switching APP/H5, comparison modes and selected issues. Keep unmatched cases and missing platforms in the coverage record; report partial completion accurately.

Read [references/review-standard.md](references/review-standard.md) before judging differences. Read [references/analysis-config.md](references/analysis-config.md) before configuring metrics. Read [references/manifest-schema.md](references/manifest-schema.md) when creating or updating a report manifest. Read [references/figma-intake.md](references/figma-intake.md) when the supplied Figma URL points to a broad canvas or ambiguous selection.

## Output contract

Before generating HTML, read [references/html-output.md](references/html-output.md). It records the approved preview styles and motion behavior. Generate every report with `scripts/build_report.py`; the bundled preview is the reference output, not a template to rewrite.

- Deliver a shareable single-file HTML in the task's output directory. The builder embeds all screenshot, design, heatmap and mask images along with CSS, JavaScript and icons; recipients need only the HTML file. Keep originals as working evidence, not recipient dependencies. Missing referenced images must fail generation. Download temporary remote screenshot URLs to local files before building. Explain that recipients download the attachment and open it in a browser; a local file link is not a public sharing URL. If a web link is requested, publish only to the user's chosen/authorized hosting destination and verify the deployed URL before delivering it.
- Treat the bundled builder as the fixed visual system: PingFang SC typography, a 320px collapsible sidebar, a central comparison workspace, a 572px independently scrolling issue panel, blue active controls, and pale-gray cards. Use the approved adjustments in references/html-output.md over the original Figma heWxFEtEUDsUYJjFqJ7zbS nodes 9:743 and 9:862; adapt columns at smaller widths and cap comparison images near 70vh. Do not replace or post-process its CSS per task; vary report content only through the manifest.
- Use `页面名 | Design Acceptance` as the document title and show `Figma Design Review` below the fixed `Design Acceptance` sidebar brand, and `Acceptance Issue` in the issue panel. Both the sidebar project heading and page eyebrow show the requirement name from `meta.project`, never a review status.
- Default to side-by-side actual screenshot (left) and design (right); keep comparison images within approximately 70vh and preserve aspect ratio. Offer an explicit overlay switch.
- Include a collapsible sidebar with designer, frontend owner, and one tab per page. Hide scrollbars in both sidebars while preserving scrolling access to overflowing content. Always show the embedded Figma logo and design-link label below the page title, even when no URL is available; keep missing links disabled. Show a matching test-case document link beside the Figma link, using the bundled test-case-logo.png and page/meta.test_case_url; keep missing destinations disabled. Put review context in the footer.
- Keep screenshot labels below their images. Keep opacity controls below the overlay tools with no filled container; slider track and thumb have no border.
- Place overlay tools in one row with blue outlined active states. The comparison Tab uses the bundled 16px compare-overlay.svg / compare-split.svg icons before its labels, and one horizontally sliding white selection plate (240ms).
- Always show 字号问题、颜色问题、间距问题、元素尺寸问题, including empty categories with a `0项` count colored `#13B36B`. Zero findings do not establish completed review or a passing result. Show failed font fields as cards; allow expanding the complete field table.
- All four categories require on-image annotations: actual/design font sizes, color hex values and swatches, measured spacing direction and rulers, or element width/height. Read the annotation fields in references/manifest-schema.md; show pending labels when measurements are missing.
- Every issue card must include image evidence: anchored font comparison or actual/design crops from the source images and issue rectangles. Label missing source images explicitly; never fabricate illustrations. Lay issue cards out in a single-column inspector grouped in collapsible categories. All rectangles and number badges start hidden. Clicking a font or issue card shows only that issue without scrolling or moving the comparison workspace, on the corresponding actual/design sides or overlay. Support Enter/Space, clearing selection, and Escape.
- Use the four acceptance categories from [the supplied Figma reference](https://www.figma.com/design/heWxFEtEUDsUYJjFqJ7zbS/Untitled?node-id=9-811): headings 9:811 (字号), 9:829 (颜色), 9:833 (间距), and 9:837 (元素尺寸) inside inspector 9:802. Counts come from actual findings. This is the report presentation reference; use each reviewed product's matching design node for expected values. Keep unrelated blocking defects explicit, without treating “其他” as a replacement for any of the four checks.
- Keep technical engine details, raw measurement tables, and pass-rule explanations out of the default view.
- Use native Web Animations and CSS transitions for disclosures, page/mode switching, and sidebar folding; keep animations off fixed-position ancestors, handle interrupted transitions, and respect `prefers-reduced-motion`.
- Keep actual/red and expected/blue strokes at 2px, including selection and pulse animations. Size-issue previews use equal scale on both sides, width/height dimension rulers from the issue rectangles, and explicit width/height deltas; retain estimate uncertainty.
- Reset alignment, difference, heatmap, mask, and opacity controls when switching pages so a prior page cannot leave the next page black or visually altered.

## Tools and scripts

```bash
python3 scripts/analyze_overlay.py analysis-config.json
python3 scripts/build_report.py report-manifest.json --output outputs/design-acceptance.html
```

`assets/figma-logo.png` and the user-supplied 24px `assets/disclosure-arrow.svg` are required by the builder and embedded into generated HTML. Render this SVG at 16×16px for all disclosure arrows with the existing rotation animation. `assets/example-manifest.json` is a runnable schema example. `assets/preview.html` is the generated preview of that example and should be regenerated after changing the builder.

## Stopping conditions

Do not invent a match when a broad Figma selection does not expose an identifiable screenshot/design pair. Report the resolved nodes and any excluded regions. Do not call a page passed when any P0 structural, brand, or interaction defect remains, regardless of the average score.
