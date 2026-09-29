# Spec Delta

## MODIFIED Requirements

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
