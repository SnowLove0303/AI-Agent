# Proposal

## Why

The structured table view can calculate a cell as one display line too short, clipping the bottom of the final wrapped line. Users must be able to read all imported MSDS cell text.

## What Changes

- Count every rendered display line when fitting structured cell height.
- Add a GUI regression check for final-line visibility in Section 12.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `msds-table-search`: Require the final wrapped line to remain visible in structured cells.

## Impact

- Affected: `检索功能/msds_table_search.py`, its GUI smoke check, and the `msds-table-search` spec.
- No new dependencies or source document changes.
