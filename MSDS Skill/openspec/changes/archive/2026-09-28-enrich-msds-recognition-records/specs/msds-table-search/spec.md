# Spec Delta

## MODIFIED Requirements

### Requirement: Preserve source table structure

For Word documents, the application SHALL present every source table with its original row count, column grid, cell text, and horizontal or vertical merged-cell spans. For PDFs, it SHALL present detected tables as page-scoped row and column grids and retain cell text; when a page has no detected table, it SHALL keep that page's text accessible rather than omit it. For Word documents, the extracted record SHALL also retain explicitly specified text-run and paragraph formatting plus table, row, and cell layout properties, including source values and units where present. The application SHALL keep text and image segments in source order and the native Word-compatible preview as the visual reference for effective inherited styling and page layout. In the structured table view, Word column widths SHALL be based on source grid widths within readable minimum and maximum bounds, and row heights SHALL adapt to wrapped text and inline image dimensions without unnecessary blank space. Every rendered text line, including the final wrapped line in a cell, SHALL remain fully visible.

#### Scenario: View a varied Word table
- **WHEN** the user opens a document whose sections use different table shapes or merged cells
- **THEN** each table is rendered with its own row and column structure and merged spans
- **AND** cell content remains in its source cell

#### Scenario: View a PDF page without a detected table
- **WHEN** the PDF table extractor finds no table on a page
- **THEN** the page's extracted text remains available in the document view

#### Scenario: Read Word text and paragraph formatting
- **WHEN** a Word cell contains text with explicitly set run or paragraph properties
- **THEN** the extracted text segments retain their character style, font, size, emphasis, color, and applicable paragraph alignment, spacing, and indentation properties
- **AND** adjacent text with different formatting remains distinguishable

#### Scenario: Read Word table geometry
- **WHEN** a Word table contains explicitly set grid, table, row, or cell layout properties
- **THEN** the extracted table record retains those properties, including grid and cell widths, table layout and alignment, row height and repeat/header flags, cell vertical alignment, shading, margins, and borders where specified
- **AND** existing row counts, columns, merge spans, cell text, and ordered images remain unchanged

#### Scenario: Preserve native Word formatting preview
- **WHEN** the user opens a Word record in the default preview
- **THEN** the application displays a page rendered by Word-compatible software
- **AND** source table layout and text formatting are retained

#### Scenario: Fit columns and row heights to source content
- **WHEN** a Word table has narrow source columns, wrapped text, or inline images
- **THEN** the structured view sizes columns from the source grid widths and rows from the rendered cell content
- **AND** it does not stretch short tables across the full viewport or leave excess blank row height

#### Scenario: Keep the final wrapped line visible
- **WHEN** a Word table cell contains wrapped or multiple lines of text
- **THEN** the structured cell height includes every rendered display line
- **AND** the bottom of the final line remains visible without clipping

## ADDED Requirements

### Requirement: Provide an agent-readable recognition result

After import, the application SHALL make a versioned JSON record available for export. For Word sources, normalized records SHALL retain table and row indices, grid gaps, cell coordinates, merge spans, paragraphs, ordered text/image segments, directly recorded text and paragraph formatting, and table/row/cell layout properties. The result SHALL include the readable source OOXML parts needed to inspect source tags not represented by normalized fields. Label/value extraction SHALL be represented as candidates with the recognition method, evidence, exact value text, and source coordinates; it SHALL not replace or rewrite source cell content. The result SHALL report table-count mismatches and elements retained only in source OOXML. For PDFs, the result SHALL include detected word and table coordinates and font name/size where available, and SHALL identify when these layout properties could not be detected or semantically inferred.

#### Scenario: Export a Word recognition record
- **WHEN** the user exports an imported DOC or DOCX document
- **THEN** the JSON includes its version, source type, section/table records, normalized formatting and layout, label/value candidates, and readable source OOXML parts
- **AND** every candidate links back to its source row, cell, paragraph, or text segment

#### Scenario: Inspect a label and its value
- **WHEN** a table row or paragraph presents a visibly marked label and a corresponding value
- **THEN** the recognition record exposes a label/value candidate with the exact source text and coordinates
- **AND** the original cell and text-run content remains available unchanged

#### Scenario: Report unnormalized source content
- **WHEN** the importer encounters a source element it does not normalize
- **THEN** the recognition result preserves readable source XML and reports the element and count as a warning
- **AND** it does not claim that the normalized view fully interpreted that element

#### Scenario: Export PDF layout evidence
- **WHEN** a user imports and exports a PDF with detectable text or tables
- **THEN** word font names, sizes, word positions, and detected table/cell bounds are included where the extractor provides them
- **AND** unavailable structure or Word-style semantics are marked as unavailable or inferred
