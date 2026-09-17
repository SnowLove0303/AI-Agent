## Purpose

Provide a reusable, traceable compliance judgment workflow that turns complete MSDS/TDS facts and the maintained local restriction datasets into a report-ready result for each requested regulation or customer standard.

## ADDED Requirements

### Requirement: Complete-facts judgment mode

The skill SHALL use an explicit complete-facts assumption in which the supplied MSDS/TDS composition, product use, market, substrate, environment, and special requirements are treated as exhaustive facts. A substance or use omitted from those facts SHALL NOT be emitted as an indeterminate missing fact.

#### Scenario: Omitted substance in a complete composition

- **WHEN** a complete MSDS/TDS composition contains only polyurethane dispersion and deionized water and a maintained restriction list does not match either component
- **THEN** the skill SHALL return `符合（基于完整资料假设）` for that substance-list check and SHALL record the complete-facts assumption in the result

#### Scenario: Omitted downstream use

- **WHEN** the complete TDS use is leather or plastic surface coating and no toy, EEE, packaging, architectural, or wood-coating use is supplied
- **THEN** the skill SHALL evaluate downstream-only requirements as `不适用` for the current product use instead of `不能判断`

### Requirement: Canonical restriction-source ingestion

The skill SHALL read the configured canonical data root and support the existing REACH SVHC, REACH Annex XVII, EU RoHS, HSF-001, BSBL, and AfPS GS 2019:01 PAK CSV exports. It SHALL preserve each matched record's source file, source row or identifier, version metadata, scope, limit, unit, and test-method fields when present.

#### Scenario: Six restriction families are available

- **WHEN** the configured data root contains the supplied CSV export directory
- **THEN** the skill SHALL load the six restriction families, report their row counts and source versions, and make them available to the judgment engine

#### Scenario: Canonical data root is missing

- **WHEN** the configured data root cannot be found or a required family file is missing
- **THEN** the skill SHALL fail with a specific data-source error naming the missing path and SHALL NOT silently use a second dataset

### Requirement: Deterministic substance matching

The skill SHALL match product components in this order: normalized CAS, EC number, normalized Chinese name, normalized English name, group/member relationship, and controlled aliases. A match SHALL retain the source record and the matching key used.

#### Scenario: Exact CAS match

- **WHEN** a component CAS matches a restriction record CAS
- **THEN** the result SHALL identify the regulation, substance, matching CAS, source row, and applicable limit

#### Scenario: Group-level restriction without a single CAS

- **WHEN** a restriction record is a legal group entry and has no single substance CAS
- **THEN** the skill SHALL evaluate the group name and member records and SHALL not treat the blank CAS as an automatic no-match

#### Scenario: No match under complete facts

- **WHEN** all complete component identities fail the configured match sequence for a restriction family
- **THEN** the family result SHALL be `符合（基于完整资料假设）` rather than `需补证`

### Requirement: Applicability resolution

The skill SHALL resolve applicability from target market, final use, environment, substrate or finished product, and special requirements before evaluating a restriction family. It SHALL distinguish direct material restrictions from downstream finished-product requirements.

#### Scenario: Current PU-1002 leather coating

- **WHEN** the product is identified as a waterborne polyurethane coating for leather or plastic surface finishing
- **THEN** the skill SHALL apply substance-list checks to the material and mark toy-only, EEE-only, packaging-only, architectural-wall, and wood-coating-only checks as `不适用` unless the input explicitly includes that downstream use

#### Scenario: Toy use explicitly supplied

- **WHEN** the input explicitly states that the material is used in a toy or children's product
- **THEN** the skill SHALL activate the EU Toy reference set and toy-related migration or restricted-substance checks instead of applying the leather-coating exclusion

### Requirement: Report-shaped output

The skill SHALL produce a Chinese report-ready matrix modeled on the approved PU-1002 PDF report with product facts, assumptions, per-regulation result, rationale, evidence, source version, and follow-up requirements.

#### Scenario: Matrix contains all requested items

- **WHEN** a user supplies a list of regulations or standards
- **THEN** the output SHALL contain one row per requested item, preserve the original item name, and include one of the four defined result labels

#### Scenario: Customer code is not identifiable

- **WHEN** an item such as a customer specification has no resolvable source text, issuer, version, or rule set
- **THEN** the result SHALL be `需补证` with the exact missing identity fields and SHALL not be upgraded to `符合`

### Requirement: Traceability and validation

Every result SHALL include the complete-facts assumption state, data-root identity, source file or source family, matching evidence, and the rule path used. The skill SHALL provide a runnable validation command covering the core matching and applicability behaviors.

#### Scenario: Reproducible result

- **WHEN** the same facts, source data, and requested standards are supplied twice
- **THEN** the result status, matched identifiers, and evidence paths SHALL be stable

#### Scenario: Core regression check

- **WHEN** the skill test command is run from the repository
- **THEN** tests SHALL cover an exact match, no-match pass, scope exclusion, group restriction, and unidentified customer specification
