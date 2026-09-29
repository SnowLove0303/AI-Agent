# Design

## Context

The DOCX reader already walks table cells in XML order and returns rows, merge spans, text and images. The GUI has a native Word-compatible PDF preview, which remains the visual authority for effective styles and page placement.

## Goals / Non-Goals

**Goals:** Store directly specified run/paragraph properties and table/row/cell geometry in the existing record dictionaries without changing the existing content order or search text.

**Non-Goals:** Reimplement Word's full style cascade, pagination, or layout engine; alter PDF extraction; add dependencies; or change the source document.

## Decisions

- Read OOXML properties from the same elements already traversed by the DOCX parser. Keep raw unit-bearing values (twips, half-points, EMUs, and enum strings) explicit in field names or values so callers do not mistake them for rendered dimensions.
- Attach `run_format` and `paragraph_format` to text segments. Merge adjacent text only when these formatting dictionaries match; preserve paragraph boundaries as newline segments with paragraph metadata.
- Add a `structure` dictionary at table level, row properties per row, and format properties per source cell. Include only properties specified in the document, while retaining null shading when the source has none.
- Keep native PDF rendering as the GUI's exact visual view. Structured table display continues to prioritize original grids, merges, and inline images; format metadata is available in the record and recognition output.
- Resolve effective style inheritance only for preview via Word-compatible rendering. Full Word style-cascade evaluation was considered but excluded because it duplicates a layout engine and is not needed to faithfully retain the source's explicitly stored format data.

## Risks / Trade-offs

- [Direct OOXML values omit inherited style values] → Preserve character/paragraph style IDs and use native rendered pages to inspect effective appearance.
- [OOXML encodes dimensions in mixed units] → Keep source units in field names and document them in the recognition Markdown.
- [Unsupported Word properties may exist] → Capture the specified high-value formatting/geometry fields and preserve existing XML-driven text/image order.

## Migration Plan

Extend the parser's returned record shape compatibly (existing keys remain unchanged), re-import PU-3011 through `read_file`, append/readable metadata to its recognition report, run structural assertions against known section/table counts, and validate the OpenSpec change. No source file migration is needed.
