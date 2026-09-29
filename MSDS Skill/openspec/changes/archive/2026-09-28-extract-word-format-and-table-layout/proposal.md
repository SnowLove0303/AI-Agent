# Proposal

## Why

The importer currently captures DOCX text, row/column counts, merges, and image order, but drops most run and paragraph formatting as well as detailed table and cell geometry. Reading these properties is needed to inspect recognition completeness and compare structured results with source MSDS layout.

## What Changes

- Capture text-run formatting and paragraph formatting alongside ordered text and image content.
- Capture table grid widths, table properties, row properties, and cell properties including widths, vertical alignment, shading, and borders where specified.
- Include the new recognized format and structure fields in the PU-3011 Markdown recognition record without changing source content.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `msds-table-search`: Word table records must expose text/paragraph formatting and table/row/cell geometry while preserving the existing row, column, merge, text, and image behavior.

## Impact

Update DOCX parsing in `检索功能/msds_table_search.py` and extend the PU-3011 recognition Markdown. No new runtime dependency or source-document modification is required. The native page preview remains the visual reference for inherited styles and Word layout.
