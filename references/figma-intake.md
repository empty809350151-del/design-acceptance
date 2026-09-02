# Figma intake and pairing

## Broad canvas links

A canvas URL may resolve to many screenshot/design pairs. Use metadata to enumerate candidates and look for:

- implementation frames named as validation screenshots or containing bitmap fills;
- nearby design frames with matching state, page, and business meaning;
- explicit state labels such as success, failure, registered, or unregistered;
- matching viewport dimensions.

Record three IDs when available:

1. requested intake node;
2. implementation screenshot node;
3. design page or exact component node.

If the page-level design context is sparse, query the exact component node visible in the screenshot. Never use a visually adjacent frame as a match without state evidence.

## Evidence set

For each page retain:

- actual screenshot PNG;
- design screenshot PNG;
- heatmap PNG;
- mask PNG;
- metrics JSON;
- node IDs and exclusion rationale.

Use stable page slugs so later pages can be appended without rewriting previous review results.
