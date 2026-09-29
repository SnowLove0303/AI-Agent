# Proposal

## Why

MSDS documents contain 16 numbered sections whose tables use different row and column counts, merged cells, and long cell contents. A searchable viewer must retain those source table boundaries and cell positions so that searching does not flatten or misrepresent the safety data.

## What Changes

- Add a desktop GUI to import DOC, DOCX, and PDF MSDS files.
- Extract numbered section tables, cell text, row/column shape, merged cells, and searchable header/footer content grouped in Section 0.
- Find embedded GHS pictograms through image metadata and section context.
- Display native-rendered pages for faithful layout, alongside structured table inspection and whole-document search.
- Handle multiple extracted tables or pages without assuming every MSDS uses the same template.

## Capabilities

### New Capabilities

- `msds-table-search`: Import, search, and faithfully present MSDS section tables.

### Modified Capabilities

None.

## Impact

Adds a standalone Python GUI and dependency notes under `检索功能`. DOCX extraction uses `python-docx`; legacy DOC conversion uses Microsoft Word automation; PDF table extraction uses `pdfplumber`. Original files remain read-only.
