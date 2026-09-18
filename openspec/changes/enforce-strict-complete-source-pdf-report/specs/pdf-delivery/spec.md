# PDF report delivery

## ADDED Requirements

### Requirement: every CLI run creates a PDF

Every successful judgment CLI run MUST write a PDF at the caller-provided `--output-pdf` path. JSON or Markdown output MAY additionally be written as an intermediate artifact, but MUST NOT replace the PDF requirement.

#### Scenario: PDF-only delivery

- **GIVEN** valid complete facts and a database
- **WHEN** the CLI runs with `--output-pdf` and no intermediate output
- **THEN** it writes a readable PDF and exits successfully

### Requirement: PDF is verified before success

The CLI MUST fail non-zero if PDF conversion fails, the output is missing, the PDF has no pages, or its extracted text does not contain the report structure markers and at least one result status marker.

#### Scenario: Conversion or verification failure

- **GIVEN** the converter is unavailable or the generated file cannot be verified
- **WHEN** the CLI runs
- **THEN** it returns failure instead of claiming a completed report

### Requirement: PDF contains decision context

The PDF MUST contain the product, generation time, active uncertainty policy, complete-facts assumption, condition-driven selection, per-regulation status, source traceability, and summary counts.

#### Scenario: Auditable written report

- **GIVEN** a condition-driven judgment with selected and excluded regulations
- **WHEN** the PDF is rendered
- **THEN** the report contains the selection matrix, result matrix, source information, assumptions, and summary
