# Proposal

## Why

The structured table view currently creates a separate expanding label for every formatted text run. Documents with many runs therefore show large artificial gaps and lose normal inline reading flow.

## What Changes

- Render text runs inline within each source cell and keep embedded images in their original order.
- Apply available font size, bold, italic, underline, and text color in the structured view.
- Keep the original page preview as the reference for exact Word layout.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `msds-table-search`: Structured Word cells preserve inline text flow, formatting cues, and image order without artificial vertical gaps.

## Impact

Update `检索功能/msds_table_search.py`; no new dependency or source-document modification is required.
