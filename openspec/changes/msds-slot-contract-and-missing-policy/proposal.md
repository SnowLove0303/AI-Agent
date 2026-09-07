## Why

The current MSDS overwrite path can preserve the document geometry while still writing facts into the wrong template cells, leaking template examples, dropping source values, or displaying fields that the source never supplied. The PU-1001 comparison and the Feishu 3.14.3 review show that positional row projection is not a safe contract; the behavior must be corrected before more products are processed.

## What Changes

- **BREAKING** Replace implicit positional value projection with an explicit template-slot contract that distinguishes locked labels, writable value objects, intentionally blank slots, whole-note slots, and the special Section 8.2 data table.
- **BREAKING** Make source fidelity authoritative for writable slots: preserve source values verbatim unless an approved semantic normalization is recorded; do not invent, summarize, relocate, or rewrite facts into a different section.
- Add a source-field state model distinguishing supported data, explicit missing data, not-applicable conclusions, and absent source fields.
- **BREAKING** Apply section-specific missing-data behavior: remove and renumber pure-missing Section 9 rows; reduce fully missing Sections 11 and 12 to their source explanation rows; preserve explicit missing values only where the source field exists and the section policy allows it; suppress template-only fields.
- Keep Section 8.2 as the only table-data exception: preserve its parent/header geometry, clear illustrative rows, and write only verified source control-parameter records or the exact approved empty-table treatment.
- Add PU-1001 regression coverage for address fidelity, Section 2 verbatim content, Section 8 glove parameters, Section 8 recommendation blankness, Section 8.2 no-invention behavior, Section 10 absent fields, Section 11/12 note-only output, and fixed template header text.
- Reuse one approved semantic model across the four language/company variants so semantic decisions are made once and variant generation remains lightweight and deterministic.

## Capabilities

### New Capabilities

- `msds-overwrite-contract`: Explicit template-slot authorization, source-fidelity mapping, section-specific missing-data behavior, and shared semantic-model generation for MSDS outputs.

### Modified Capabilities

- `deliverable-audit-framework`: Extend source-fidelity, controlled-mutation, and section-specific audits to fail on template-only field leakage, source-value loss or drift, invalid blank-slot writes, and incorrect Section 9/11/12 missing-data handling.

## Impact

- Affects the existing shared MSDS pipeline and mutation whitelist under `MSDS Skill/scripts/`, the semantic projection helpers under `MSDS Skill/_task_work/`, and the MSDS regression tests.
- Uses the existing CN/EN template snapshots and current audit framework; it does not modify the user source `.doc`, active formal templates, TDS Skill, or PDF converter.
- Adds OpenSpec artifacts and regression fixtures/tests inside the existing repository root. No new project root, parallel Skill, or replacement template is introduced.
