# Proposal

## Why

Verify that the existing MSDS import program can read the supplied PU-3011 document and provide a complete, auditable Markdown record of exactly what the importer recognizes.

## What Changes

- Import the specified DOCX through the existing GUI parser.
- Record every recognized Section 0 and section table, row, cell, and image marker in a Markdown report.
- Include parser counts and extraction limitations without filling in content the program did not recognize.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is a one-time recognition and reporting task; application behavior does not change.

## Impact

Reads the specified DOCX with `检索功能/msds_table_search.py` and writes `检索功能/PU-3011_MSDS_识别结果.md`. The source document remains unchanged.
