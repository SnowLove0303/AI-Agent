# Tasks

## 1. Preserve cell content order

- [x] 1.1 Extract DOCX cell text and embedded image markers in XML order, remove the generated pictogram label, and verify the Section 2 record has the source sequence.
- [x] 1.2 Render the mixed segments sequentially in the structured table view and verify both Section 2 pictograms appear directly after the “GHS 象形图” line with no duplicate label; Tk smoke test reports widget order text → image → image → text and one source label.
- [x] 1.3 Run the PU-202A import/search/render regression and `openspec validate --strict`; confirm 16 body tables, Section 9 24×2, six search terms, WPS/PDFium render, and unchanged source file.
