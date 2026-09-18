## 1. Catalog and schema

- [x] 1.1 Add the extensible regulation catalog containing the initial 40 entries, aliases, scope modes, and reference-source records; validate catalog identifiers and required fields.
- [x] 1.2 Implement SQLite schema, indexes, schema version and rebuild-safe migrations; verify an empty database initializes cleanly.

## 2. Data ingestion and refresh

- [x] 2.1 Ingest catalog regulations, sources and generic condition predicates; verify source metadata is queryable.
- [x] 2.2 Ingest the six canonical CSV families as derived restriction rows with raw JSON, hashes, versions and source rows; verify row counts against the supplied exports.
- [x] 2.3 Implement refresh and missing-source errors; verify no fallback data root is used.
- [x] 2.4 Generate the shipped `legal_compliance.db` baseline from the supplied canonical CSV/metadata root and verify its catalog count, restriction row count, source hashes, and refresh command.

## 3. Condition-driven judgment

- [x] 3.1 Implement condition-sheet field normalization and generic scope predicate evaluation; verify PU-1002 leather/plastic facts select direct rules and exclude downstream-only rules.
- [x] 3.2 Add automatic regulation selection when `--standards auto --db` is used and preserve explicit-list compatibility; verify a newly cataloged regulation is selected without code changes.
- [x] 3.3 Persist runs, selected regulations, selection reasons, statuses and evidence; verify repeated runs preserve identity and status with unchanged sources.

## 4. Feedback and skill integration

- [x] 4.1 Add audited feedback storage and explicit approval state; verify unapproved feedback cannot affect selection.
- [x] 4.2 Update SKILL.md, CLI help and report template to make the database/condition-first workflow the default guidance.
- [x] 4.3 Add tests for catalog, refresh, auto-selection, explicit compatibility, run persistence and feedback gates.

## 5. Validation and delivery

- [x] 5.1 Run unit tests, canonical-data refresh, 40-item compatibility smoke, condition-driven PU-1002 smoke, `git diff --check`, and strict OpenSpec validation.
- [x] 5.2 Stage only the skill/database/OpenSpec files, push to `origin/main`, verify remote HEAD, and report the database initialization command.
