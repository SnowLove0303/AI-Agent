# MSDS/TDS Batch Overwrite Specification

## Purpose

Define the deliverables and completion conditions for workbook sequence numbers 2–5 in the current MSDS/TDS batch.

## Requirements

### Requirement: Exact model and source selection

The batch SHALL process only sequence numbers 2, 3, 4, and 5 from `型号数据库.xlsx`. It SHALL resolve each sequence to the exact model name and use only that model folder's identified MSDS and TDS source files. Similar names SHALL NOT be matched by substring.

#### Scenario: Select the four requested products

- **WHEN** the workbook's sequence values 2–5 are read
- **THEN** the batch selects AMP-95, BEK-100L, BEK-200, and BEK-200L
- **AND** it excludes all other sequence values

### Requirement: Preserve source files

The batch SHALL treat all original MSDS and TDS sources as read-only. Any legacy-format adaptation SHALL be written only under the corresponding model's audit output folder. The SHA-256 of each original source SHALL match its recorded pre-processing hash at completion.

#### Scenario: Adapt a legacy TDS source

- **WHEN** a TDS source is a legacy `.doc`
- **THEN** any extraction adapter writes a temporary copy under that model's audit folder
- **AND** the original `.doc` remains byte-for-byte unchanged

### Requirement: Produce separate eight-format MSDS and TDS matrices

For each selected model, the batch SHALL produce four DOCX variants and four same-basename derived PDF variants for MSDS, and the same eight-file matrix for TDS. MSDS and TDS SHALL use their separate installed skills, active templates, source mappings, and release audits. Product facts SHALL be grounded in that model's source evidence; English variants SHALL be translated from reviewed source-grounded facts.

#### Scenario: Generate the requested outputs

- **WHEN** the model's sources have been reviewed and mapped
- **THEN** byte-identical copies of the two source files and all 16 deliverables are placed together in that model's `覆写输出` root
- **AND** each DOCX sits beside its same-basename PDF, without separate Word and PDF folders
- **AND** MSDS and TDS audit evidence remains in their respective subfolders
- **AND** original and historical deliverables remain untouched

### Requirement: Gate workbook completion status

The batch SHALL mark a model's final workbook column as `已覆写` only after all 16 non-empty deliverables for that model pass the applicable content, template, conversion, page-count availability, and visual audits. The actual page count SHALL be recorded for every PDF; more than one page is permitted. If any required evidence or gate other than page count alone is missing or fails, that model's status SHALL remain unchanged.

#### Scenario: A model fails a release gate

- **WHEN** any required output is missing, unreadable, visually defective, or its content, template, conversion, or other required audit fails
- **THEN** the workbook status for that model remains unchanged
- **AND** the failed gate and report path are recorded

#### Scenario: A PDF spans multiple pages

- **WHEN** a PDF has more than one page
- **AND** every page is present, readable, visually reviewed, and passes the applicable content and conversion audits
- **THEN** its page count is recorded and the page count alone does not block completion

#### Scenario: Complete a model

- **WHEN** all 16 outputs and required audit evidence pass
- **THEN** only that model's final-column status cell is set to `已覆写`
- **AND** the saved workbook is reopened and rows outside sequence numbers 2–5 are verified unchanged
