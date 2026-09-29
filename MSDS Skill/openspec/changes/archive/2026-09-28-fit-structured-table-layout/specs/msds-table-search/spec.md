# Spec Delta

## MODIFIED Requirements

### Requirement: Preserve source table structure

For Word documents, the application SHALL present every source table with its original row count, column grid, cell text, and horizontal or vertical merged-cell spans. For PDFs, it SHALL present detected tables as page-scoped row and column grids and retain cell text; when a page has no detected table, it SHALL keep that page's text accessible rather than omit it. For Word documents, the extracted record SHALL also retain explicitly specified text-run and paragraph formatting plus table, row, and cell layout properties, including source values and units where present. The application SHALL keep text and image segments in source order and the native Word-compatible preview as the visual reference for effective inherited styling and page layout. In the structured table view, Word column widths SHALL be based on source grid widths within readable minimum and maximum bounds, and row heights SHALL adapt to wrapped text and inline image dimensions without unnecessary blank space.

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
