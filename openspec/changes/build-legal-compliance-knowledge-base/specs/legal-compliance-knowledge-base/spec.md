## Purpose

为法律法规判断提供一个可刷新、可追溯、可扩展的本地知识库，统一保存法规身份、条件、参考源、限制规则、判断运行和经过批准的反馈，而不把法规范围固定在最初的 40 项。

## ADDED Requirements

### Requirement: Regulation knowledge database

The system SHALL provide a local database containing regulation identity, aliases, jurisdiction, scope mode, reference sources, version/effective-date metadata, source hashes, structured restriction rules, and audit timestamps. The database SHALL be rebuildable from the configured canonical data root.

#### Scenario: Initial database build

- **WHEN** the user initializes the database with the condition-driven regulation catalog and canonical legal-data root
- **THEN** the database SHALL contain the seeded regulations, their reference sources and applicability metadata, and the six available CSV restriction families with source hashes and row counts

#### Scenario: Refresh after source update

- **WHEN** a canonical CSV or metadata file changes and the user runs refresh
- **THEN** the database SHALL replace the derived restriction rows, update source hashes/version fields, and retain the catalog and historical judgment records

#### Scenario: Missing canonical source

- **WHEN** a required source file is absent
- **THEN** refresh SHALL fail with the exact missing path and SHALL not silently use a second data root or stale replacement file

### Requirement: Condition-driven regulation selection

The system SHALL select applicable regulations from the condition-sheet fields: target market, final use, environment, substrate/finished product, composition identities, measured content or migration, and special requirements. The initial 40 regulations SHALL be seed data only; additional registered regulations SHALL participate in selection without code changes.

#### Scenario: PU-1002 leather/plastic coating

- **WHEN** complete facts identify a waterborne coating for leather/plastic, industrial use, with no toy, EEE, packaging, architectural, wood, or customer requirement
- **THEN** the selector SHALL choose direct material regulations and applicable China coating rules, exclude toy/EEE/packaging/architectural/wood-only rules as `不适用`, and return the selection reason for every candidate

#### Scenario: Explicit downstream use

- **WHEN** the condition sheet adds toy, children's product, EEE, packaging, building, or wood use
- **THEN** the selector SHALL activate the corresponding registered regulation set and SHALL not apply the previous downstream exclusion

#### Scenario: New regulation registration

- **WHEN** a user registers a new regulation with a name, source, scope condition and optional restriction family
- **THEN** the next automatic selection SHALL be able to return that regulation without editing the fixed 40-item list

### Requirement: Judgment run persistence

The system SHALL record each automatic or explicit judgment run with a facts hash, complete-facts mode, selected regulations, selection reasons, result status, evidence references, source versions and creation time. Re-running the same facts against unchanged sources SHALL preserve selected regulation identity and result status.

#### Scenario: Auto-selected report

- **WHEN** a judgment is run without an explicit standards list and a populated database is supplied
- **THEN** the report SHALL contain the database-selected regulations and the database SHALL persist the selection and result rows under a run identifier

#### Scenario: Explicit compatibility mode

- **WHEN** a caller supplies an explicit standards list
- **THEN** the engine SHALL preserve that list for compatibility while still recording the run and source evidence in the database when a database is supplied

### Requirement: Audited feedback loop

The system SHALL accept feedback or correction records linked to a judgment run and regulation, including rationale and evidence. Feedback SHALL default to unapproved and SHALL not alter automatic selection or result rules until explicitly approved.

#### Scenario: Unapproved correction

- **WHEN** a reviewer records that a regulation was incorrectly selected or omitted
- **THEN** the database SHALL store the feedback with its evidence and leave automatic selection unchanged

#### Scenario: Approved rule enhancement

- **WHEN** a reviewer explicitly approves a feedback record as a new scope alias, source mapping, or condition rule
- **THEN** subsequent database refresh/selection SHALL expose the approved rule with an audit link to the feedback record
