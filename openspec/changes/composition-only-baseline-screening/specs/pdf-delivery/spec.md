# Composition report delivery

## MODIFIED Requirements

### Requirement: PDF identifies the baseline layer

The mandatory PDF MUST identify a composition-only baseline run and show each baseline regulation's source status, matched substances, concentration/limit comparison, and result.

#### Scenario: Source-backed and catalog-only entries

- **GIVEN** a baseline containing both local structured lists and official catalog-only trigger entries
- **WHEN** the PDF is generated
- **THEN** it distinguishes `source-backed` from `catalog-only` rows without requesting additional user documents
