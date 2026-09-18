# MSDS Unified Eight-Deliverable Standardizer Skill — Changelog

## v3.26.1 — 2026-09-18

- Added `scripts/run_efficiency_workflow.py` as the single resumable Harness
  entrypoint: source evidence extraction and cache reuse happen once, then the
  workflow pauses for reviewed facts before preflight and formal matrix build.
- Added persisted `workflow-state.json`, `evidence-packet.json`, and
  `preflight.json` checkpoints so interrupted runs resume without repeating
  extraction or semantic preparation.
- Kept the reviewed-facts gate, source-grounding gates, locked-template rules,
  and formal-output blocking behavior unchanged. The workflow never approves
  facts, bypasses preflight, or mutates a template.
- Added focused tests and Harness performance guidance for the new entrypoint.

## v3.26.0 — 2026-09-17

- Added an explicit source/cache root to the formal build path. Legacy source
  conversions now report whether a source-hash-bound adapter result was reused;
  direct DOCX behavior remains unchanged.
- Added reviewed-only product-family candidate profiles. Candidates can validate
  or suggest a mapping, but absent/conflicting candidates never auto-fill facts
  or DOCX value cells.
- Added one read-only `AuditContext` per saved staged DOCX and routed compatible
  value, whitespace, numbering and locked-structure observations through it.
  Persisted package, terminology, PDF-lineage and final matrix checks remain
  independent release gates.
- Added additive timing telemetry for cache decisions, per-variant wall time,
  PDF batch workers/failures, external review/wait labels and final artifact
  hashes. Added `scripts/benchmark_efficiency.py`, which measures cold/warm
  evidence reuse and optional worker counts entirely in temporary directories.
- Kept bounded threaded WPS conversion as the default (`2` workers), with
  `--pdf-workers 1` as the conservative serial fallback. No ProcessPool,
  resident COM/WPS daemon or alternate PDF authoring engine was enabled.

## v3.25.3 — 2026-09-17

- Added explicit Section 2.8 health-route facts for inhalation, ingestion,
  skin, eyes and symptoms/signs. Overall GHS conclusions such as `Not
  classified` can no longer be reused as a route-specific value.
- Added semantic Section 8 PPE extraction and sparse-row alignment. Tabs,
  inline label/value tails and irregular source order are recovered without
  cascading values into neighboring template rows; unknown PPE rows fail
  closed for review.
- Locked the two bold Section 15 structural headings in CN and EN across slot
  discovery, clearing, writing, non-bold-value auditing and English layout
  normalization.
- Added PU-1002 regression fixtures and kept the formal templates and all
  prior release packages unchanged and recoverable.

## v3.25.2 — 2026-09-16

- Added a fail-closed Section 2 semantic fact router with exclusive-by-default
  source-fact ownership, explicit reviewed shared exceptions and target-specific
  CN/EN output trace checks.
- Blocked synthesized Section 2.1 emergency overviews and cross-target reuse of
  facts between hazard statements, physical/chemical hazards, health hazards and
  other hazards before template cloning.
- Added dedicated S8.2 topology checks for the five-column grid, four logical
  data cells, `gridSpan`, widths, parent/header structure and complete-block
  hiding; formal templates remain byte-pinned.
- Added a dedicated S11.4 vertical-alignment audit; only the existing bounded
  short-value row-height exception remains allowed.
- Added focused routing/layout regressions and kept v3.25.1 as the recoverable
  package baseline.

## v3.25.1 — 2026-09-16

- Enforced the clarified template ownership rule: pre-existing bold content
  remains locked label/structure content, while every writable value is
  non-bold and inherits all other approved value typography.
- Added direct-run and paragraph-inherited bold overrides to the shared value
  writer, including Section 2.8 value tails; the controlled S9 insertion path
  keeps its newly seeded label formatting explicitly separate.
- Added a semantic non-bold value audit and release gate that covers ordinary
  values, S3/S8.2 data cells, S11 final endpoint cells and one-cell notes while
  excluding locked labels, sublabels, headers and route prefixes.
- Added CN/EN regression coverage for bold stripping, inherited bold, manual
  bold-value blocking and format comparison that permits only bold removal.

## v3.25.0 — 2026-09-15

- Added a second fail-closed `source_grounding` gate and matrix evidence record
  that rejects template-only product values and unreviewed source anchors.
- Added a mandatory source-grounding policy to the Agent's OpenSpec reading
  set, including explicit source reconciliation and template-example isolation.
- Preserved complete Section 2.2 label-ingredient explanations separately from
  the controlled signal-word slot, including the explicit non-hazard fallback.
- Prevented S15/S16 one-cell labels from duplicating into their own values and
  removed empty S5/S13 capacity rows before positional validation.
- Added Section 11 acute-toxicity aliases, an auditable S11.4 short-row output
  exception, and multi-run Section 2.8 prefix regression coverage.
- Isolated promoted output under `OUT/MODEL/WORD` and `OUT/MODEL/PDF` and
  added a post-promotion matrix gate.
- Replaced WPS `subprocess.run(timeout=...)` calls with owned process
  kill/reap cleanup so timeout failures release handles before temp cleanup;
  no LibreOffice/`soffice.exe` PDF fallback was added.

## v3.24.2 — 2026-09-15

- Restored source-gated Section 8 `建议 / Recommendation` values while
  keeping the template label and value-cell formatting locked; absent source
  recommendations remain empty.
- Extended the controlled Section 2 signal-word vocabulary for non-hazard
  products (`无信号词` / `No signal word`, `无` / `None`, and `Not applicable`)
  without permitting label-ingredient prose or arbitrary free text.
- Made Chinese product identity suffix matching whitespace-tolerant and
  case-insensitive so compact names such as `脂肪族水性聚氨酯接着树脂PU-1001`
  do not receive a duplicate model suffix.
- Made Section 2.8 composite health-hazard detection follow the semantic
  `健康危害 / Health Hazards` label after authorized numeric renumbering,
  including the `2.7` case.
- Added extraction, semantic, identity, recommendation and post-renumbering
  regression tests.

## v3.24.1 — 2026-09-14

- Locked template-owned content by semantic role, not only by boldness:
  Section 2.8 route prefixes and Section 11.1/11.7 middle sublabels cannot be
  rewritten or cleared as ordinary values.
- Added deterministic registry metadata for writable cells, locked cells,
  field keys, merge identity and special topology policies. S3 three-column
  and S8.2 four-column data structures remain explicit and auditable.
- Added a prefix-preserving Section 2.8 writer. Empty source values leave only
  the original route prefix until the complete row is suppressed; populated
  values are appended after a semantic line break without changing the
  template run tree.
- Extended locked-skeleton and OpenSpec empty-value audits plus CN/EN
  regression coverage for composite values, structured sublabels and topology
  drift.

## v3.24.0 — 2026-09-14

- Added the active `MSDS-EFFICIENCY-001` OpenSpec. The business workflow is
  now explicit and ordered as full source extraction, constrained information
  normalization, fixed-template overwrite and post-overwrite fine-tuning.
- Added a semantic `SectionWritePlan`: all S1-S16 payloads, Section 11/12
  alignment and S9/S15 insertion capacity are resolved before value cells are
  cleared or XML rows are changed. This removes stale physical-index decisions
  from the overwrite hot path while preserving the exact mutation whitelist.
- Separated the runtime's post-overwrite fine-tuning entry point for source
  absence, Section 2/9 omission and numbering, and the Section 8.2 empty-block
  policy. The default `write_body` API remains backwards-compatible.
- Added bounded expected/actual/diff/hint diagnostics to locked-label,
  locked-format and EN body-format blockers, making Harness repair loops
  actionable without weakening fail-closed behavior.
- Added low-overhead stage telemetry to matrix reports for the business stages,
  DOCX checkpoints, release audits and PDF batch conversion. Existing
  `--preflight-only`, `--no-pdf` and audited DOCX preview controls remain
  diagnostic checkpoints and cannot replace final QA.
- Explicitly prohibited whole-table rebuilds, blanket soft-hide strategies,
  knowledge-base auto-fill and fixed-duration performance promises.

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
