---
name: figma-overlay-acceptance
description: Compare a Figma design with an implementation screenshot using masked overlays, per-field font anchoring, structured issue framing, and an interactive multi-page HTML acceptance report. Use for visual design acceptance and screenshot-versus-Figma QA; not for implementing the product UI itself.
---

# Figma Overlay Acceptance

Produce an evidence-backed visual acceptance result and a reusable HTML preview. Preserve existing pages when appending another review.

## Required workflow

1. Use the Figma tools to resolve the exact implementation screenshot node and matching design node. A broad canvas URL is intake context, not proof that every visible pair belongs together.
2. Retrieve metadata, design context, and screenshots for both nodes. Inspect exact component nodes when a page-level design response is sparse.
3. Establish the comparison boundary before scoring. Mask dynamic copy, unrelated bottom-page content, system UI, and intentional data differences. Do not hide geometry, brand assets, icons, borders, or interactive states.
4. Run `scripts/analyze_overlay.py` with a page-specific analysis config. Inspect the output rather than accepting the score blindly.
5. Review every visible text field by its own glyph anchor. Size checks must be independent of whole-page or container displacement.
6. Write short issue cards that state the design target directly. Ignore copy-only differences unless the copy changes geometry or interaction.
7. Add the result to the HTML manifest and run `scripts/build_report.py`. Each sidebar tab represents one independent acceptance page.
8. Verify JSON, referenced assets, unique HTML IDs, inline JavaScript syntax, and the final page hash before reporting completion.

Read [references/review-standard.md](references/review-standard.md) before judging differences. Read [references/analysis-config.md](references/analysis-config.md) before configuring metrics. Read [references/manifest-schema.md](references/manifest-schema.md) when creating or updating a report manifest. Read [references/figma-intake.md](references/figma-intake.md) when the supplied Figma URL points to a broad canvas or ambiguous selection.

## Output contract

- Save user-facing HTML and its image assets in the task's output directory.
- Treat the bundled builder as the fixed visual system: Geist typography, a 220px collapsible sidebar, black-and-white editorial layout, green active states, flat cards, and an approximately 70vh comparison image. Do not replace or post-process its CSS per task; vary report content only through the manifest.
- Use `页面名 | Overlay Design Review and Acceptance` as the document title and show the suffix below the page name.
- Keep the comparison image within one viewport (approximately 70vh).
- Include a collapsible sidebar with designer, frontend owner, and one tab per page.
- Put the screenshot opacity control directly below the image with no filled container.
- Place overlay mode controls in one outlined-button row.
- Show only failed font fields as flat cards; allow expanding the complete field table.
- Lay issue cards out as a two-column grid. Clicking a font or issue card must scroll to and highlight the matching screenshot rectangle.
- Keep technical engine details, raw measurement tables, and pass-rule explanations out of the default view.
- Use GSAP when network access is acceptable; provide functional behavior without it and respect `prefers-reduced-motion`.
- Reset alignment, difference, heatmap, mask, and opacity controls when switching pages so a prior page cannot leave the next page black or visually altered.

## Tools and scripts

```bash
python3 scripts/analyze_overlay.py analysis-config.json
python3 scripts/build_report.py report-manifest.json --output outputs/design-acceptance.html
```

`assets/example-manifest.json` is a runnable schema example. `assets/preview.html` is the generated preview of that example and should be regenerated after changing the builder.

## Stopping conditions

Do not invent a match when a broad Figma selection does not expose an identifiable screenshot/design pair. Report the resolved nodes and any excluded regions. Do not call a page passed when any P0 structural, brand, or interaction defect remains, regardless of the average score.
