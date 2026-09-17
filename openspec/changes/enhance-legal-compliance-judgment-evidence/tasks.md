## 1. Source evidence

- [x] 1.1 Add companion metadata-file mappings and verify selected families report version/effective-date fields.
- [x] 1.2 Add stable evidence projection for source file, hash, row, match key, limit, unit, scope, and test method; verify a CAS hit exposes all available fields.

## 2. Unit-safe judgment

- [x] 2.1 Implement explicit `%`, `ppm`, and `mg/kg` parsing/conversion and verify compatible values compare numerically.
- [x] 2.2 Reject incompatible formulation/migration units with a specific `需补证` reason and verify no dimensionless comparison occurs.
- [x] 2.3 Preserve current scope exclusions and add direct tests for PU-1002 leather/plastic, toy, EEE, and packaging variants.

## 3. Report and regression coverage

- [x] 3.1 Update JSON/Markdown output to display match key, source row, limit, unit, method, and version without losing raw evidence.
- [x] 3.2 Add regression tests for metadata, CAS/EC/name/group/alias hits, no-match pass, conversion pass/fail, and opaque customer standards.
- [x] 3.3 Run the canonical 40-item smoke check against both supplied data directories and verify one result per requested item with no copied data root.

## 4. Validation and delivery

- [x] 4.1 Run targeted tests, CLI smoke, `git diff --check`, and strict OpenSpec validation.
- [x] 4.2 Review staged paths and push only the skill plus this OpenSpec change to `origin/main`; verify remote HEAD and report the commit.
