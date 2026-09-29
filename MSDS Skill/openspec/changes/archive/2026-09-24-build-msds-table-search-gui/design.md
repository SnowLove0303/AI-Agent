# Design

## Context

The sample `PU-202A msds_CN 冠志.docx` contains 16 top-level tables with varying grid widths (one to three columns), horizontal merges, and vertical merges. Section 9 is a 24-row, two-column table. The numbered section title is in the first row of each table; the document also has header text.

## Goals / Non-Goals

**Goals:** Keep one extracted record per source Word table, including its grid width, cells, text, and merged spans; group header/footer in Section 0; search embedded pictograms; display native-rendered pages to preserve Word layout and text formatting.

**Non-Goals:** Edit or regenerate MSDS documents; translate content; infer missing safety data; guarantee reconstruction of visual table geometry in arbitrary PDFs.

## Decisions

- Use one Python/Tkinter application. Tkinter is included with the target Windows Python and avoids a web server or extra UI framework.
- Read DOCX table XML through `python-docx` and represent each cell with a starting grid column, `gridSpan`, `vMerge` span, and paragraph text. Render those values with Tk grid `columnspan` and `rowspan` so merged cells remain merged.
- Convert legacy DOC to a temporary DOCX with Microsoft Word COM automation. Never save to the selected source path.
- Use WPS/Word automation to export Word files to temporary PDF and PDFium to render native pages in the default preview. PDFs render directly. Keep structured extraction as a separate view.
- Use `pdfplumber` to detect PDF page tables and retain page numbers. If no table is detected, retain page text as a page-level record.
- Search pictogram image metadata and contextual GHS aliases; show pictogram objects after cell text in the structured view.
- Derive section labels from each table's leading title and retain unclassified tables under an “Unclassified” group rather than dropping them.
- Search extracted text case-insensitively; selecting a result opens the complete original table, not a flattened search excerpt.

## Risks / Trade-offs

- [PDF table boundaries and merged cells are inferred from page geometry] → Preserve native PDF pages as the primary visual presentation.
- [Pictogram meaning cannot be reliably inferred for arbitrary images] → Search accessible image metadata and known hazard codes/context; native page preview retains the original pictogram placement.
- [Legacy DOC conversion requires Microsoft Word on Windows] → Show a direct dependency error and leave the source untouched when Word automation is unavailable.
- [Large or malformed files may take time to parse] → Perform import outside the Tk event loop and report the failure instead of displaying incomplete data.
