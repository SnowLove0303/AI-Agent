# Tasks

## 1. Application

- [x] 1.1 Build the Tkinter GUI with file import, section/table navigation, and case-insensitive document search; verify the UI bindings and filtering code in `msds_table_search.py`.
- [x] 1.2 Parse DOCX tables and merged cells, convert DOC with Word to a temporary DOCX, and extract PDF page tables/text; verify each format path and source read-only handling in `msds_table_search.py`.
- [x] 1.3 Render source row/column grids and merged spans, plus header/footer and PDF page labels; verify render fields match the parser output in `msds_table_search.py`.
- [x] 1.4 Add launch and dependency instructions; verify the README and requirements are present under `检索功能`.
- [x] 1.5 Validate OpenSpec artifacts and inspect the delivered files and sample structure; `openspec validate` reports the change valid, and the sample contains 16 top-level tables (Section 9: 24 rows × 2 columns; Section 2: two embedded PNG images).

## 2. Regression fix

- [x] 2.1 Read optional cell shading through the underlying XML element so unshaded cells import safely; verify PU-202A parses with 16 tables, Section 9 is 24×2, Section 2 retains two images, and “离子性” search resolves to Section 9.

## 3. Native layout, header/footer, and pictogram search

- [x] 3.1 Group Word headers and footers under Section 0 and include their text and tables in search; sample yielded two header/footer tables plus searchable header text.
- [x] 3.2 Extract image metadata and add contextual GHS pictogram search aliases; sample GHS07, GHS08, 感叹号, 健康危害, and 象形图 queries find Section 2.
- [x] 3.3 Render Word/PDF pages with native page layout by default; retain structured tables as an alternate view; Tk UI smoke test rendered both Section 2 pages and structured widgets.
- [x] 3.4 Verify the sample document import, Section 0, pictogram searches/order, Word export, and PDF page rendering; update user instructions. Verified 16 body tables, Section 9 24×2, 8-page WPS export, page mapping, PDFium rendering, and unchanged source SHA-256.
