# Spec Delta

## Purpose

Provide deterministic release gates that keep TDS source facts, company templates, inherited paragraph formatting, and generated files isolated and recoverable across all four DOCX variants and their derived PDFs.

## ADDED Requirements

### Requirement: Variant template integrity

The system MUST resolve every variant to its registered active template, verify the registered SHA-256 before writing, and reject duplicate language/company identities. A generated variant MUST satisfy its company asset contract, including media presence and first-paragraph header indentation.

#### Scenario: Changed template is blocked

- **WHEN** an active template hash differs from the registry
- **THEN** generation and audit MUST fail before a deliverable is published

#### Scenario: Guocai output contains Guanzhi assets

- **WHEN** a Guocai DOCX contains a media relationship or a non-zero first-paragraph left indent
- **THEN** the variant asset gate MUST fail and PDF conversion MUST not start

### Requirement: Body layout inheritance lint

The system MUST compare every non-empty generated description, supply-form, application, storage, and expanded body paragraph with the corresponding active-template paragraph anchor, including paragraph spacing, indentation, numbering, run fonts, run size, and character properties. The linter MUST reject intra-paragraph and intra-cell line-break characters.

#### Scenario: Expanded body paragraph keeps template layout

- **WHEN** a source field expands into multiple DOCX paragraphs
- **THEN** every generated paragraph MUST retain the complete style shape of its registered template anchor

#### Scenario: Body line spacing is compressed

- **WHEN** vertical budgeting changes a body paragraph's line value or line rule
- **THEN** preflight MUST fail the DOCX

### Requirement: Source section isolation

The system MUST reject a normalized field when it contains a complete source clause from another body section that is absent from the target field's source evidence. Existing Chinese source/output fidelity checks MUST remain blocking.

#### Scenario: Application clause leaks into description

- **WHEN** a clause supported only by the application source appears in normalized product description text
- **THEN** mapping or generation MUST fail closed with a cross-section leakage error

### Requirement: Recoverable locked-output handling

The system MUST generate DOCX and PDF results through same-directory temporary files and atomic replacement. If the target is locked, it MUST preserve the generated result as a `.pending` sibling, leave the original target unchanged, and return a failure that names the retained file.

#### Scenario: Viewer locks the target PDF

- **WHEN** atomic replacement raises a permission error because the target is open
- **THEN** the converter MUST retain the new PDF beside the target, preserve the old PDF, and fail explicitly
