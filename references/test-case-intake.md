# Test document intake and scoped coverage

The normal input is a test-case document with screenshots, a Figma URL, and the current development scope. Use the appropriate document/browser tools for the supplied format. Extraction and semantic pairing are agent workflow steps, not functionality implemented by the Python image analyzer. If originals cannot be retrieved, record that limitation; do not silently use compressed thumbnails.

## Inventory before pairing

Keep a coverage JSON alongside the report with one record per expected platform/case/module:

```json
{
  "case_id": "TC-023",
  "platform": "APP",
  "frontend": "APP owner",
  "state": "two-line title",
  "module": "booking card",
  "source": {"document": "test document URL or path", "location": "TC-023 / attachment 2", "image": "originals/TC-023-app.png"},
  "capture": {"kind": "device", "original_size": [1170, 2532], "content_rect": [0, 132, 1170, 2400]},
  "scope": {"target": "booking card", "related": ["parent padding", "next-section gap"], "excluded": ["unchanged recommendation list"]},
  "mapping": {"status": "matched", "node": "123:456", "evidence": ["same route", "same component and state"], "candidates": ["123:456"]}
}
```

Create a separate H5 record even if it shares a design node. Never infer a platform merely from a browser-looking screenshot: APP webviews can look similar. Use test metadata; mark unknown identity pending. APP and H5 may have different owners, captures, states, defects and results. Missing screenshots are `missing`, unresolved matching is `pending`, evidence that cannot be compared is `unscorable`. These are not passes. Keep these records in the coverage file and mention them in the delivered summary; only resolved, scored units go into the numeric report pages.

## Automated pairing policy

1. Prefer an explicit Figma node link in the case or requirement. Verify its component, platform variant and state rather than trusting a stale link.
2. Otherwise enumerate design candidates from Figma metadata; filter by requirement/page/route, changed component, platform and state.
3. Use screenshot labels, OCR where available, stable icons/assets and layout hierarchy as supporting evidence. Dynamic text and screenshot pixel dimensions are weak signals.
4. Accept only a unique candidate with semantic AND state/layout evidence and no contradiction. Keep the evidence and rejected candidates. A nearest-looking frame alone is insufficient.
5. If two candidates remain plausible, preserve both and ask for the smallest missing discriminator. Continue other units. Do not invent a numeric confidence score or claim automatic certainty.

## Scope and content variants

The review boundary includes the changed element, its parent alignment/padding, directly affected sibling gaps and relevant interaction states. Keep a full original screenshot for context, but use a contextual crop or separate regions for review. Document what is out of scope.

For permitted two-line text, inspect width constraints, line height, maximum lines, truncation, wrapping, container expansion and the gap to the next element. Expected downstream displacement may equal the extra line's height plus documented layout rules. If those rules are unavailable, record a pending rule check instead of declaring the shift valid or defective. Masking text alone does not correct reflow. Compare unaffected subregions with their own justified anchors; keep contextual geometry checks separate. Never move every element independently until it matches.

Normalization scale comes from known content viewport width/DPR/export scale or multiple unchanged anchors, never from the changed module's measured width. After uniform normalization, crop both sides to a common coordinate space. If legitimate content makes extents differ, use context crops that retain the expanded content, exclude non-comparable areas, and separate local checks; do not stretch or truncate the extra line to manufacture a match.
