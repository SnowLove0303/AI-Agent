# Spec Delta

## Purpose

This capability lets users inspect and find information in complete MSDS documents while keeping section boundaries, table rows, columns, cell contents, and merged-cell relationships visible as they appeared in the source.

## ADDED Requirements

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

For Word documents, the application SHALL present every source table with its original row count, column grid, cell text, and horizontal or vertical merged-cell spans. For PDFs, it SHALL present detected tables as page-scoped row and column grids and retain cell text; when a page has no detected table, it SHALL keep that page's text accessible rather than omit it.

#### Scenario: View a varied Word table
- **WHEN** the user opens a document whose sections use different table shapes or merged cells
- **THEN** each table is rendered with its own row and column structure and merged spans
- **AND** cell content remains in its source cell

#### Scenario: View a PDF page without a detected table
- **WHEN** the PDF table extractor finds no table on a page
- **THEN** the page's extracted text remains available in the document view

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
The application SHALL search embedded image metadata and contextual GHS hazard aliases. It SHALL place structured-view images after their cell text and use a native Word/PDF page rendering as the primary visual representation to preserve source table geometry, typography, and layout.

#### Scenario: Find a contextual GHS pictogram
- **WHEN** an embedded pictogram or nearby known GHS hazard code is present
- **THEN** searches for its image metadata and supported GHS aliases find the containing section
- **AND** the native page preview shows the pictogram in its source position

#### Scenario: Inspect Word formatting
- **WHEN** the user opens a Word record in the default preview
- **THEN** the application displays a page rendered by Word-compatible software
- **AND** source table layout and text formatting are retained
