# Proposal

## Why

The structured table view currently flattens each DOCX cell's text and appends its images afterward. This moves GHS pictograms away from the “GHS 象形图” line and adds a duplicate generated label, so the displayed cell no longer follows the source order.

## What Changes

- Preserve the order of text, paragraph breaks, and embedded images inside each Word table cell.
- Render pictograms at their source position and remove the generated duplicate pictogram label.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `msds-table-search`: The structured table view must preserve the source order of cell text and images.

## Impact

Update DOCX cell extraction and structured table rendering in `检索功能/msds_table_search.py`, plus the MSDS table-search specification and usage notes. No new dependency or source-document modification is required.
