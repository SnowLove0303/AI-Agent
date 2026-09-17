## Purpose

为完整且确定的 MSDS/TDS 事实提供带版本、限值、单位、匹配键和源行的法规判断证据，使真正可判定的物质清单结果不因证据未展开而被误报为需补证。

## ADDED Requirements

### Requirement: Versioned source evidence

The skill SHALL load the maintained metadata files for each selected CSV family when they exist and SHALL attach source file, source row, file hash, row count, version fields, scope, limit, unit, and test method to each matched rule or source summary when those fields are present.

#### Scenario: Matched record carries source evidence

- **WHEN** a complete component matches a row in RoHS, HSF 001, BSBL, AfPS, REACH SVHC, or REACH Annex XVII
- **THEN** the result SHALL include the matching CSV path, one-based source row, matching key, source hash, and all available rule fields without requiring a manual lookup

#### Scenario: Metadata is present

- **WHEN** the selected family has a companion version-and-metadata CSV
- **THEN** the report SHALL include its version and effective-date fields in the source summary and SHALL fail clearly if the required main file is missing

### Requirement: Comparable measurement units

The skill SHALL normalize comparable concentration or migration values before applying a numeric limit, including `%`, `ppm`, and `mg/kg` where equivalence is valid. It SHALL NOT compare values across incompatible units without an explicit conversion and SHALL return `需补证` with the missing unit or conversion reason when a safe comparison is impossible.

#### Scenario: Percentage converts to ppm

- **WHEN** a component measurement is `0.05%` and a rule limit is `1000 ppm`
- **THEN** the engine SHALL compare the normalized value `500 ppm` to the limit and SHALL not return `需补证` merely because the input units differ

#### Scenario: Incompatible units remain evidence-gated

- **WHEN** a rule is an area migration limit and the input only supplies a formulation percentage without a valid conversion
- **THEN** the engine SHALL return `需补证` and identify the incompatible measurement and required test quantity

### Requirement: Match-key and rule display

The skill SHALL record the actual match key used for each hit, including CAS, EC, normalized Chinese or English name, group/member name, or controlled alias, and SHALL expose the matched substance, measurement, limit, unit, and test method in the report-ready matrix.

#### Scenario: CAS hit is visible in the matrix

- **WHEN** a component CAS matches a restriction row
- **THEN** the JSON and Markdown results SHALL show the CAS match key, component identity, source row, limit, unit, and test method when available

#### Scenario: No-match complete fact remains a pass

- **WHEN** every component identity fails all configured match keys for an applicable structured family
- **THEN** the family SHALL remain `符合（基于完整资料假设）` and SHALL not be downgraded to `需补证`

### Requirement: Scope-aware reduction of indeterminate results

The skill SHALL classify the complete PU-1002 leather/plastic coating facts against downstream-only scopes before requiring evidence. It SHALL use `不适用` for omitted toy, EEE, packaging, architectural-wall, and wood-coating uses, and SHALL reserve `需补证` for an applicable rule whose source text or test evidence is genuinely unavailable.

#### Scenario: PU-1002 downstream exclusions

- **WHEN** final use and substrate are only leather/plastic coating and no downstream use is declared
- **THEN** toy-only, EEE-only, packaging-only, architectural-wall, and wood-coating-only checks SHALL be `不适用`

#### Scenario: Explicit downstream use overrides exclusion

- **WHEN** the complete facts explicitly add toy, EEE, packaging, or another downstream use
- **THEN** the corresponding scope SHALL become applicable and the engine SHALL evaluate its structured data or return a specific missing-rule evidence reason
