## 1. Audit contract and documentation

- [x] 1.1 Define the versioned 100-point scoring model, score bands, outcome names, B0/B1/B2 precedence, and non-overridable release blockers in `docs/deliverable_evaluation_standard.md`; verify every threshold and outcome has a documented test case.
- [x] 1.2 Define the complete release checklist with stable rule IDs for identity, source fidelity, semantic classification, template geometry, whitelist, Sections 2/3/8/9/11/14, four-format parity, PDF derivation, visual QA, packaging, and legacy inheritance in `docs/deliverable_audit_checklist.md`; verify checklist IDs are unique and cover every normative spec requirement.
- [x] 1.3 Define the B0/B1/B2 catalog, release-gate behavior, and remediation language in `docs/release_blocker_catalog.md`; verify every blocker referenced by the checklist has one severity and one release effect.
- [x] 1.4 Define the versioned machine-readable evidence schema and human-readable report contract in `docs/audit_evidence_schema.md`; verify required fields and allowed statuses are explicit.
- [x] 1.5 Update `SKILL.md`, `README.md`, `CHANGELOG.md`, `VERSION.txt`, and `manifest.txt` for the new audit layer and V3.10 release metadata; verify existing V2.9/V3.8/V3.9 preservation statements and no product example facts are promoted into rules.

## 2. Deterministic audit model

- [x] 2.1 Implement a checklist registry containing stable rule IDs, categories, weights, severity, source-of-truth references, pass conditions, and evidence kinds; verify registry uniqueness and complete metadata with unit tests.
- [x] 2.2 Implement score aggregation, score bands, outcome selection, and B0/B1 precedence; verify boundary scores, incomplete checks, observation mode, and high-score blocker cases with unit tests.
- [x] 2.3 Implement evidence record validation and report serialization for JSON and human-readable output; verify every required field, allowed status, deterministic ordering, and explicit `NOT_CHECKED`/`ERROR` handling.
- [x] 2.4 Implement deterministic eight-file package discovery and DOCX/PDF matrix pairing; verify missing, duplicate, ambiguous, wrong-language, and wrong-company inputs fail without selecting arbitrary files.

## 3. Existing audit integration

- [x] 3.1 Adapt existing V3.9 audits for template geometry, mutation whitelist, locked labels, Section 2, whitespace, terminology, four-format, eight-file, and V2.9 inheritance into the unified evidence contract; verify adapter errors become explicit failed or error records.
- [x] 3.2 Add source-fidelity and semantic-model checks for example-fact leakage, unsupported explanatory inference, correct Section 11 alias classification, and required “无数据” wording; verify PU-2345 and OS-9015 fixtures preserve source facts and reject injected template examples.
- [x] 3.3 Add Section 2/3/8/9/11/14 special-case adapters covering pictograms, label line breaks, ingredient row cardinality, locked Section 8.1 behavior, Section 9 omission/reordering, Section 11.10 coverage, and Section 14 line breaks; verify each rule with focused fixtures.
- [x] 3.4 Add four-format semantic/company parity checks and final-DOCX-to-PDF traceability checks; verify four variants remain equivalent except for allowed company/language fields and PDFs are paired to final DOCX outputs.
- [x] 3.5 Add automatic PDF structural checks and visual-QA evidence ingestion for page count, page size, text extraction, blank/zero-byte pages, clipping/overflow signals, pictograms, and critical Section pages; verify an intentional visual failure blocks release.

## 4. Orchestration and reports

- [x] 4.1 Implement the unified deliverable audit command with explicit input/output paths and observation-mode handling; verify a complete PU-2345 or OS-9015 package produces one JSON report and one human-readable report.
- [x] 4.2 Make the orchestrator fail closed when any required rule is missing, not checked, errors, or lacks evidence; verify the final report cannot claim `RELEASE_PASS` under incomplete execution.
- [x] 4.3 Add checklist-to-implementation-to-test coverage auditing; verify a missing registry entry, undocumented rule, or untested required rule causes a release blocker.

## 5. Regression, replay, and release validation

- [x] 5.1 Add unit tests for scoring, blockers, evidence schema, package discovery, and checklist coverage; verify the full new test group passes.
- [x] 5.2 Add controlled replay tests for PU-2345 and OS-9015 CN/EN × 冠志/国彩 eight-file packages without copying their product facts into maintained templates; verify all required audit records are emitted.
- [x] 5.3 Run the complete existing V3.9 test suite plus V2.9 inheritance, template geometry, semantic/company parity, four-format, eight-file, PDF, whitespace, terminology, whitelist, locked-label, Section 2, and ZIP integrity audits; verify no historical version directory is modified.
- [x] 5.4 Build the V3.10 ZIP from a clean staging tree with one `MSDS Skill/` root, no duplicate entries, no caches or task artifacts, and an exact manifest; verify ZIP contents and manifest counts match.
- [ ] 5.5 Sync the verified audit-layer changes to the user-designated local release folder and the formal GitHub repository folder, record Git status/commit/remote evidence, and report any push authorization failure without claiming remote publication; verify local package, repository folder, and ZIP are byte/content consistent.
