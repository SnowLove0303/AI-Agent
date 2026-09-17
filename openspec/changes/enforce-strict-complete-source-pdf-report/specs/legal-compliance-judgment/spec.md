# Strict complete-source evaluation

## MODIFIED Requirements

### Requirement: complete facts are authoritative

The evaluator MUST treat `facts.assume_complete=true` as the complete information boundary. A substance, use, substrate, measurement, or other fact not present in that input MUST NOT create a request for a supplementary report.

#### Scenario: Omitted substance

- **GIVEN** the complete facts contain no entry for a restricted substance
- **WHEN** a selected regulation is evaluated
- **THEN** the substance is treated as absent and the result is `符合（基于完整资料假设）`, with no request for another substance report

### Requirement: default outcomes avoid uncertainty

With no uncertainty opt-in, each applicable regulation MUST resolve to `符合（基于完整资料假设）` or `不符合`; scope exclusions MUST resolve to `不适用`. A component that does not match a restriction row is absent from that rule path and MUST resolve to `符合（基于完整资料假设）`.

#### Scenario: No matching restriction

- **GIVEN** a selected regulation has no row matching any supplied component
- **WHEN** the evaluator runs in strict closed-world mode
- **THEN** it returns `符合（基于完整资料假设）`

### Requirement: unresolved rule details are closed-world passes

With no uncertainty opt-in, a matched row with a missing measurement, missing/unparseable limit, or incompatible units MUST resolve to `符合（基于完整资料假设）` and include a traceable detail explaining the closed-world assumption. If a comparable numeric value exceeds a limit, it MUST still resolve to `不符合`.

#### Scenario: Missing measurement

- **GIVEN** a supplied component matches a row but has no comparable measurement
- **WHEN** strict closed-world mode is active
- **THEN** the result is `符合（基于完整资料假设）` and the detail path records closed-world resolution

#### Scenario: Numeric exceedance

- **GIVEN** a supplied measurement is comparable and exceeds the source limit
- **WHEN** the regulation is evaluated
- **THEN** the result is `不符合`

### Requirement: uncertainty is explicit

`需补证` MAY be emitted only when `allow_uncertainty=true` is present in facts or passed by CLI, or when a user explicitly names an opaque standard in explicit-standard mode. The report MUST expose the active uncertainty policy.

#### Scenario: Explicit uncertainty mode

- **GIVEN** an otherwise unresolved matched rule and `allow_uncertainty=true`
- **WHEN** the evaluator runs
- **THEN** it returns `需补证` and exposes `explicit_uncertainty`

### Requirement: broad condition-driven coverage

An automatic run MUST evaluate every enabled regulation selected by jurisdiction and the condition-sheet fields, including newly registered regulations; it MUST NOT be capped at the original 40-item list.

#### Scenario: Registered regulation is selected

- **GIVEN** a newly registered enabled regulation matches the market and condition-sheet facts
- **WHEN** automatic selection runs
- **THEN** the regulation is included in the selected standards and evaluated
