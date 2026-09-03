## Why

The current MSDS Skill can generate and audit individual technical invariants, but it does not yet provide one customer-facing evaluation method that converts the output requirements into a complete release decision. This leaves a gap between “the files were generated” and “the eight-file package is suitable for customer delivery,” especially for source fidelity, template preservation, Section 2/3/8/9/11/14 special cases, PDF derivation, and evidence completeness.

## What Changes

- Add a single 100-point deliverable quality model with non-overridable release blockers.
- Define B0/B1/B2 failure severities and the final `RELEASE_PASS`, `RELEASE_FAIL`, `NOT_READY`, and `OBSERVATION_ONLY` outcomes.
- Add a complete audit checklist covering source identity, semantic model, template geometry, controlled mutation, special Sections 2/3/8/9/11/14, four-format parity, PDF derivation, visual QA, and packaging evidence.
- Add a versioned evidence schema so every audit result records its rule, source of truth, method, pass condition, status, failure detail, and evidence path.
- Add an orchestration audit command that runs the checklist over both DOCX and PDF outputs and emits machine-readable and human-readable release reports.
- Add regression tests for the scoring, blocker precedence, checklist coverage, evidence schema, and real PU-2345/OS-9015 eight-file replay.
- Preserve the existing V3.9 template, whitelist, generation behavior, V2.9 inheritance, four-format matrix, and historical versions.

## Capabilities

### New Capabilities

- `deliverable-audit-framework`: Defines the unified quality evaluation, release blockers, checklist entries, evidence records, and aggregate release decision for MSDS deliverable packages.

### Modified Capabilities

- None. The existing generation and template contracts remain unchanged; this change adds a release-evaluation layer around them.

## Impact

- Adds audit/evaluation documentation under `MSDS Skill/docs`.
- Adds deterministic audit and report scripts under `MSDS Skill/scripts`.
- Adds tests and evidence fixtures under `MSDS Skill/tests`.
- Adds no external API, database, service, dependency, template geometry, product fact, or output-format contract changes.
- The existing GitHub `MSDS Skill` folder becomes independently auditable from its checked-in source and test assets.
