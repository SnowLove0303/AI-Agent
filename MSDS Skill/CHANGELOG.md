# MSDS Unified Eight-Deliverable Standardizer Skill — Changelog

## v3.23.0 — 2026-09-11

- Added recursive source inventory and extraction for nested Section 8 tables;
  verified `物质 / 依据 / 类型 / 数值` control-parameter records now reach the
  dedicated S8.2 writer instead of being misclassified as absent.
- Added a fail-closed Section 11 semantic aligner. Compressed or pre-omitted
  facts are mapped by endpoint and sublabel to the fixed template skeleton;
  unmatched endpoints block rather than shifting later toxicology values into
  the wrong locked label. Section 11.1 route and 11.7 child sublabels are now
  excluded from value-presence tests, and vertical merges are repaired safely
  when an absent child row is removed.
- Added deterministic Section 9 NCO-content splitting, five-character
  sequence-prefix spacing during renumbering, and locked-skeleton tolerance for
  the approved prefix spacing adjustment.
- Reworked GHS pictogram sizing to preserve the source drawing's physical width
  with a compact 0.9-inch fallback; removed the stale 3.25-inch enlargement.
- Replaced the stale revision-date fallback with build-date stamping and
  localized CN/EN formatting while preserving the formal footer's leading `P`
  clipping guard.
- Added regression coverage for all reported OS-9013 failure modes that are
  handled by the MSDS skill. TDS-specific production code is outside this
  package and is unchanged.

## v3.22.0 — 2026-09-11

- Corrected the high-risk Section 2 semantic boundary: source `2.2 标签要素`
  is mapped to the template `2.3 GHS标签要素` value slot and must preserve
  the explicit label-ingredient explanation, such as `必须列在标签上的有害
  成分：` followed by the source ingredient on a semantic new line.
- Added controlled signal-word validation. The template `2.4 信号词` value
  accepts only the explicit `危险` / `警告` or `Danger` / `Warning`; label-
  ingredient prose in that slot blocks release before template cloning.
- Narrowed source label parsing so structural `GHS Label Elements` headings
  are not mistaken for label-ingredient facts, and fixed continuation-line
  consumption so the ingredient is not duplicated into the generic S2 queue.
- Added Chinese and English regression coverage for correct extraction,
  reclassification and release-blocking slot swaps.

## v3.21.0 — 2026-09-11

- Added `prepare_evidence_packet.py`, which extracts source coverage, the
  stable-ID fact ledger and the review queue once into a source-hash-bound,
  reusable packet. The packet is explicitly `needs-review` and can never be
  mistaken for approved facts.
- Added a persistent DOC/ODT/RTF conversion cache keyed by original source
  bytes, source format and adapter version. A repeated Harness review/build
  loop no longer invokes LibreOffice conversion for the same source.
- Added `preflight_facts.py` and `build_eight.py --preflight-only` to report all
  facts/OpenSpec blockers without cloning templates, launching WPS or starting
  any PDF work.
- Fixed Section 2 other-hazards extraction for unnumbered source lines such as
  `其他危险：无适用资料。`; a template label alone no longer protects an
  empty row, while a source-backed explicit missing conclusion remains visible.
- Made the deliverable audit short-circuit its expensive DOCX text scan when
  recursive matrix discovery already finds a missing or duplicate output slot;
  stale copied output trees now fail fast with the decisive package error.
- Added regression coverage for cache invalidation, packet reuse, aggregated
  preflight and the empty-row/renumbering boundary.

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
