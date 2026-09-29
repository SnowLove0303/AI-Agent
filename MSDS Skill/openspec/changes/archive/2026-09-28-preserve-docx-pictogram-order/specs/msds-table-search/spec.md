# Spec Delta

## MODIFIED Requirements

### Requirement: Search pictograms and preserve native layout
The application SHALL search embedded image metadata and contextual GHS hazard aliases. In the structured table view, DOCX cell text and images SHALL appear in their original document order, and the application SHALL NOT insert duplicate pictogram labels. The application SHALL use native Word/PDF page rendering as the primary visual representation to preserve source table geometry, typography, and layout.

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
