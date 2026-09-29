# Proposal

## Why

After inline text rendering was fixed, structured Word tables still used oversized default text-widget widths and fixed minimum heights. This makes narrow source tables stretch too wide and leaves short rows taller than their actual content.

## What Changes

- Size structured columns from the source table grid widths, with safe bounds for readable layout.
- Recalculate each cell's displayed line count after wrapping and size row height to its text and inline images.
- Keep horizontal scrolling available for genuinely wide tables.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `msds-table-search`: The structured table view follows source column geometry and adapts row heights to rendered content.

## Impact

Update `检索功能/msds_table_search.py` and its GUI smoke check. The source document and native page preview remain unchanged.
