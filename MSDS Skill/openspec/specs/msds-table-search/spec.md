# msds-table-search Specification

## Purpose
This capability lets users inspect and find information in complete MSDS documents while keeping section boundaries, table rows, columns, cell contents, and merged-cell relationships visible as they appeared in the source.

## Requirements

### Requirement: Import MSDS documents

The application SHALL let users select DOC, DOCX, and PDF files for local reading. It SHALL report unsupported, unreadable, or conversion-failed files without changing the source file.

#### Scenario: Import a supported file
- **WHEN** the user selects a readable DOC, DOCX, or PDF file
- **THEN** the application extracts its text and tables for viewing
- **AND** leaves the selected source file unchanged

#### Scenario: Report an import failure
- **WHEN** a file is unsupported, unreadable, or cannot be converted
- **THEN** the application shows an actionable error
- **AND** does not present partial extraction as a complete document

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

### Requirement: Navigate and search extracted content

The application SHALL provide section navigation and a case-insensitive search across extracted cell and page text. Search results SHALL identify the containing section or page and show matching content without flattening the displayed source tables.

#### Scenario: Find content in a section
- **WHEN** the user enters text present in an MSDS table cell
- **THEN** matching sections or pages are identified
- **AND** the user can open the matching source table in its original grid

#### Scenario: Navigate all numbered sections
- **WHEN** the document contains the 16 numbered MSDS sections
- **THEN** the application makes all 16 sections individually accessible
- **AND** tables within each section remain separately viewable

### Requirement: Search and group page furniture
The application SHALL combine Word headers and footers into a searchable Section 0 record group, including header/footer tables. Section 0 SHALL be associated with all native-rendered document pages.

#### Scenario: Search header/footer text
- **WHEN** the user searches text from a Word header or footer
- **THEN** a Section 0 result is shown
- **AND** the result opens the source's native page preview

### Requirement: Search pictograms and preserve native layout

The application SHALL search embedded image metadata and contextual GHS hazard aliases. In the structured table view, DOCX cell text and images SHALL appear in their original document order, with adjacent text runs flowing inline in the same paragraph and their recognized basic character formatting shown without artificial vertical gaps. The application SHALL NOT insert duplicate pictogram labels. The application SHALL use native Word/PDF page rendering as the primary visual representation to preserve source table geometry, typography, and layout.

#### Scenario: Find a contextual GHS pictogram
- **WHEN** an embedded pictogram or nearby known GHS hazard code is present
- **THEN** searches for its image metadata and supported GHS aliases find the containing section
- **AND** the native page preview shows the pictogram in its source position

#### Scenario: Preserve pictogram position in a structured table
- **WHEN** the user views a DOCX table cell containing text followed by an embedded pictogram
- **THEN** the structured view renders the text and pictogram in the source order
- **AND** it does not append another generated “GHS 象形图” label at the end of the cell

#### Scenario: Inspect Word formatting
- **WHEN** the user opens a Word record in the default preview
- **THEN** the application displays a page rendered by Word-compatible software
- **AND** source table layout and text formatting are retained

#### Scenario: Render formatted runs inline
- **WHEN** a Word cell contains adjacent text runs with different formatting
- **THEN** the structured table view keeps the text in normal inline flow and applies supported font, size, emphasis, and color attributes
- **AND** the cell does not add artificial vertical gaps between runs

### Requirement: Provide an agent-readable recognition result

After import, the application SHALL make a versioned JSON record available for export. For Word sources, normalized records SHALL retain table and row indices, grid gaps, cell coordinates, merge spans, paragraphs, ordered text/image segments, directly recorded text and paragraph formatting, and table/row/cell layout properties. The result SHALL include the readable source OOXML parts needed to inspect source tags not represented by normalized fields. Label/value extraction SHALL be represented as evidence-backed candidates with the recognition method, exact label and value text, and source coordinates; it SHALL not replace or rewrite source cell content. A delimiter-free adjacent-cell candidate SHALL be emitted only when the label has formatting evidence and its value has data evidence; it SHALL not map a table header to another header. When a label cell contains text after its delimiter, the result SHALL preserve that text in the source cell and report it as unmapped candidate evidence with a warning and source coordinates. The result SHALL report table-count mismatches and elements retained only in source OOXML. For PDFs, the result SHALL include detected word and table coordinates and font name/size where available, and SHALL identify when these layout properties could not be detected or semantically inferred.

#### Scenario: Export a Word recognition record
- **WHEN** the user exports an imported DOC or DOCX document
- **THEN** the JSON includes its version, source type, section/table records, normalized formatting and layout, label/value candidates, and readable source OOXML parts
- **AND** every candidate links back to its source row, cell, paragraph, or text segment

#### Scenario: Inspect a label and its value
- **WHEN** a table row or paragraph presents a visibly marked label and a corresponding value
- **THEN** the recognition record exposes a label/value candidate with the exact source text and coordinates
- **AND** the original cell and text-run content remains available unchanged

#### Scenario: Reject a header-to-header candidate
- **WHEN** adjacent cells contain column headings without a delimiter or data-like value evidence
- **THEN** the recognition record does not report them as a label/value candidate
- **AND** qualifying data rows in the same table remain available as candidates

#### Scenario: Retain mixed label-cell text as a warning
- **WHEN** a label cell contains a delimiter followed by additional text and the adjacent value cell contains the corresponding value
- **THEN** the candidate uses only the delimited label and the adjacent value
- **AND** the additional text is preserved unchanged in the source cell and reported as unmapped warning evidence with its source coordinates

#### Scenario: Report unnormalized source content
- **WHEN** the importer encounters a source element it does not normalize
- **THEN** the recognition result preserves readable source XML and reports the element and count as a warning
- **AND** it does not claim that the normalized view fully interpreted that element

#### Scenario: Export PDF layout evidence
- **WHEN** a user imports and exports a PDF with detectable text or tables
- **THEN** word font names, sizes, word positions, and detected table/cell bounds are included where the extractor provides them
- **AND** unavailable structure or Word-style semantics are marked as unavailable or inferred
