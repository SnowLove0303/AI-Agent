# Tasks

## 1. Import and record recognition output

- [x] 1.1 Import PU-3011 through the existing parser and verify 19 records, Section 0 tables, all 16 numbered section tables, row/column dimensions, and two image markers.
- [x] 1.2 Generate `检索功能/PU-3011_MSDS_识别结果.md` from the returned records without truncating cell text; verify all 203 non-empty text segments, labels, metadata, and both embedded image payloads are present.
- [x] 1.3 Validate the Markdown file through EOF, match record counts and source DOCX SHA-256, and pass `openspec validate record-pu3011-msds-import --strict`.
