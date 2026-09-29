# Proposal

## Why

The current recognition view exposes some formatting and table geometry but does not give downstream Agent skills a stable, complete record of source structure and uncertain extraction. Missing label/value links or unreported unsupported elements can lead to incorrect document edits.

## What Changes

- Provide a versioned JSON export with table, row, cell, paragraph, text-run, layout, and source-coordinate data.
- Expose evidence-backed label/value candidates with their source cell coordinates.
- Preserve readable Word OOXML parts and report elements that are retained but not normalized.
- Include PDF word and detected-table geometry where available and report inference limits.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `msds-table-search`: Expose complete, traceable recognition records suitable for downstream Agent processing.

## Impact

- Affected: `检索功能/msds_table_search.py`, GUI result metadata/export, regression checks, and README.
- No new runtime dependencies. Source MSDS files remain read-only.
