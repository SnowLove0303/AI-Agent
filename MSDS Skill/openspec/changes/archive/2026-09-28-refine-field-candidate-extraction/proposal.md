# Proposal

## Why

The shared field-candidate extractor can mistake a table header for a label/value pair and can absorb unrelated text that follows a label delimiter. Either error can mislead an Agent making edits from the recognition record.

## What Changes

- Make label/value candidates conservative and evidence-backed across all sections and supported table sources.
- Keep delimiter-following text in its original cell and report it as an explicit candidate warning instead of silently mapping it to the value.
- Add full-document regression checks for header false positives, Section 8 mixed-cell text, and preservation of original cell content.

## Capabilities

### New Capabilities

### Modified Capabilities
- `msds-table-search`: define reliable label/value candidates, source-preserving mixed-cell warnings, and conservative handling of delimiter-free fields.

## Impact

- `检索功能/msds_table_search.py` shared field-candidate extraction used by Word and PDF table records.
- `检索功能/check_msds_format_reading.py` PU-3011 whole-document structural and GUI regression checks.
- Exported JSON candidate metadata and the recognition-result contract.
