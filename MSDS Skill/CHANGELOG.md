# MSDS Unified Eight-Deliverable Standardizer Skill — Changelog

## v3.20.0 — 2026-09-10

- Changed the production matrix scheduler to finish all four audited DOCX
  masters before starting PDF conversion, so a slow office converter no longer
  hides every completed DOCX behind a serial loop.
- Added bounded PDF batch parallelism (`--pdf-workers`, default `2`) while
  retaining one-to-one DOCX/PDF lineage and every semantic, template, source
  and render gate.
- Added one-time WPS CLI preflight/version lookup with process-local caching,
  `MSDS_PROGRESS` events, an atomic `--progress-file` checkpoint and an
  optional `--docx-preview-dir` diagnostic checkpoint.
- Added a DeepSeek Harness runbook. No LibreOffice, `soffice.exe`, ReportLab
  or PDF-only fallback was introduced.

## v3.19.1 — 2026-09-10

- Cleaned the distributable package so only current runtime code, current
  formal CN/EN templates, active OpenSpec contracts, source-reading controls
  and current validation assets are shipped.
- Removed historical template rollback copies, stale approved-output examples,
  versioned template snapshots, generated Python caches and tests that depended
  on unavailable task-local `_task_work` generators.
- Kept the v2.9 compatibility core because it remains a mandatory inheritance
  and release-blocking contract; it is compatibility input, not an active
  template or product-fact source.
- Corrected the template-baseline documentation so an absent Section 8.2
  workplace-parameter block is removed in full and never replaced by a
  synthetic missing-data row.

## v3.19.0 — 2026-09-09

- Added the `MSDS-SOURCE-INTERPRETATION-001` OpenSpec for fail-closed source
  coverage, stable-ID fact provenance, reviewed semantic mapping and output
  traceability.
- The source extractor inventories source units, detects top-level content
  outside the S1-S16 tables, emits a fact ledger and preserves evidence and
  line-break policy on every extracted candidate.
- Formal builds block before template cloning when source content is
  unreadable or unmapped, a fact has no disposition, a mapping is ambiguous or
  conflicting, or an output target has no evidence trace.

## Maintenance rule

Only the current formal templates and current active snapshots are maintained
inside the skill package. Historical evidence and rollback material must be
stored outside the distributable skill directory and must never be presented
to an Agent as an alternative template authority.
