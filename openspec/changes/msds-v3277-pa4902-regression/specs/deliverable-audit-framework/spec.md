# Deliverable audit framework — PA-4902 regression

## MODIFIED Requirements

### Requirement: Section 2 product and component GHS scopes remain separate
The overwrite pipeline MUST preserve the source product-level Section 2 category independently from Section 3 component-level GHS evidence. When Section 3 contains an explicit reviewed component classification/H-code, the cross-section route MUST write that evidence into Section 2.1 rather than using a non-hazard fallback. Section 2.2/2.3 MUST contain only the verified special-substance attention note; a threshold clause is allowed only as part of that note and MUST remain attached to the explanation line. Classification/H-code pairs MUST be line-separated while the pair itself remains intact.

#### Scenario: component evidence with product-level 无
- **WHEN** Section 2 says `无` and Section 3 contains a component GHS classification
- **THEN** the projected Section 2.1 category contains the reviewed component classification/H-code lines
- **AND** the output MUST NOT contain `根据 GHS 不属于危险物`

#### Scenario: classification leakage into label elements
- **WHEN** a source note contains an attention substance, a classification/H-code line and a threshold line
- **THEN** Section 2.2/2.3 retains the attention substance and attached threshold in the `title + explanation` shape
- **AND** it removes the classification/H-code line

#### Scenario: packed H/P statements
- **WHEN** Section 2.5 or Section 2.6 receives multiple coded statements in one source line
- **THEN** each H/EUH or P statement is written on its own logical line
- **AND** Section 2.5/2.6 headings remain separate from their detail lines

### Requirement: Writable values have an explicit global format contract
Every non-empty writable value run in S1-S16 MUST explicitly carry the language font, 12 pt size, `w:szCs`, non-bold state and the required paragraph/cell alignment. CN values MUST use 宋体; EN values MUST use Times New Roman. All S3 name/CAS/content values MUST be horizontally and vertically centered. Missing direct properties MUST fail the release audit.

#### Scenario: inherited five-point value
- **WHEN** a Section 11 value has text but no direct `w:sz`/`w:szCs` or font mapping
- **THEN** the release audit reports a value-format blocker

#### Scenario: Section 3 alignment
- **WHEN** a populated Section 3 name, CAS or content value is written
- **THEN** its paragraph is horizontally centered and its cell is vertically centered
- **AND** left-aligned output fails the audit

### Requirement: Locked skeleton and structured child labels are immutable
The output MUST retain the fresh template's label text, boldness, sequence geometry, paragraph formatting, indentation, spacing, borders, merges, widths and table topology. In 11.1, 11.2 and 11.7 three-column rows, the first two columns MUST remain locked labels and only the final value cell may be written.

#### Scenario: Section 10 sequence-label drift
- **WHEN** an output changes a Section 10 sequence/label alignment or label formatting
- **THEN** the locked-skeleton audit blocks the output

#### Scenario: Section 11.2 middle child label
- **WHEN** a source row has an endpoint, a bold middle child label and a value
- **THEN** only the final value is written
- **AND** the middle child label is never classified as a value
