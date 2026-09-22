# MSDS Unified Eight-Deliverable Standardizer Skill — Changelog

## v3.27.12 — 2026-09-22

- Fixed Section 11.1 structured values that repeated the locked endpoint and
  route headings, such as `毒性：经口：` / `Toxicity: Oral:`.
- Applied the same conservative endpoint/sublabel de-duplication through the
  shared Section 11 alignment path while preserving the source result tail.
- Added Chinese and English regression coverage.

## v3.27.11 — 2026-09-22

- Changed Section 2 health-hazard de-duplication from a blanket switch to
  independent inhalation, ingestion, skin, eyes and symptoms/signs routing.
- Preserved every uncovered source 2.7/2.8 route and every additional same-route
  source line instead of taking only the first value.
- Kept route-labelled first-aid instructions from Section 2.6 in the response
  group and blocked them from being promoted into health-hazard rows.
- Added release-audit blockers and regression coverage for route-specific
  duplication, missing route values and source-line preservation.

## v3.27.10 — 2026-09-22

- Installed the user-approved CN/EN formal templates as the new active and
  source-record baselines; the verified content, 16-section structure and
  language-specific capacities remain unchanged while table styling is refreshed.
- Retained the shared Section 6 printable divider rule so the label/value split
  cannot disappear when the new table style is used.
- Retained Section 11 endpoint-aware value normalization: when the locked label
  already states `主要皮肤刺激性`/`Primary skin irritation`, the value contains
  only the source test result and never a duplicate `刺激性`/`Irritation` prefix.
- Refreshed template hashes, geometry snapshots and release metadata to
  fail closed against the new baseline.

## v3.27.9 — 2026-09-22

- Made Section 2.1 classification output line-based: every explicit GHS
  classification/H-code pair occupies one logical line while the pair itself
  stays intact.
- Split packed Section 2.5 H-statements and Section 2.6 P-statements at
  semantic code boundaries before writing values.
- Kept Section 2.3 GHS label elements as `title + explanation`; specific
  concentration limits remain attached to the explanation instead of becoming
  a standalone line.
- Added evidence-bound typo correction for the PA-4902 source typo
  `依然液体` + `H226` → `易燃液体` + `H226`; unrelated text is never passed
  through a general spell-check rewrite.

## v3.27.8 — 2026-09-21

- Split flattened Section 2.2 special-substance thresholds into logical lines
  and remove the separator comma without rewriting the source statement.
- Restored the explicit source GHS category conclusion, routing the reviewed
  Section 3 component classification/H-code fact into Section 2.1 while
  keeping Section 2.2/2.3 limited to the special-substance note; duplicate
  field prefixes are stripped only when the template already owns the label.
- Rebuilt incomplete CN/EN Section 3 facts against the maintained product-type,
  ingredient, header and component skeleton so leading components cannot be
  dropped or shifted into later rows.
- Kept Section 9 semantic property matching, Section 8 hand-protection parent
  preservation, Section 11 subject-specific notes/renumbering and Section 13
  note-plus-treatment topology under release-blocking audits.
- Replayed PA-4902 through the full four-DOCX/four-PDF pipeline: 275 tests,
  four-format audit and 100/100 deliverable audit passed.

## v3.27.7 — 2026-09-21

- Split Section 2 product-level facts from Section 3 component-level GHS
  evidence. An explicit reviewed component classification is now routed into
  Section 2.1 when the product-level field says `无`; the non-hazard fallback
  is no longer allowed to overwrite that evidence.
- Restricted Section 2.2/2.3 label-elements output to the verified
  special-substance attention note and blocked classification/H-code leakage
  into that slot.
- Made the global writable-value contract release-blocking: CN values are
  explicit 宋体 12 pt, EN values are explicit Times New Roman 12 pt, values
  are vertically centered and left aligned, and every populated S3
  name/CAS/content value is horizontally and vertically centered. Missing
  direct OOXML font/size properties now fail instead of inheriting five-point
  Normal text.
- Reasserted locked sequence-plus-label geometry for all sections and the
  three-column Section 11.1/11.2/11.7 rule that only the final value cell is
  writable.
- Added PA-4902 regression gates for the reported fallback, classification
  leakage, S3 alignment drift and Section 11 five-point inheritance defects.

## v3.27.6 — 2026-09-21

- Normalized absent/no GHS category to `根据 GHS 不属于危险物` and absent
  pictograms to `无象形图`, while preserving source attention-substance notes.
- Rendered Section 2.5 precautionary headings as separate paragraphs with
  18pt hanging detail indentation through the shared value writer.
- Enforced centered Section 3 component/CAS/content cells and prevented
  contaminated or duplicate Section 8 hand-protection values.
- Closed the legacy preflight-wrapper compatibility hole: `status=blocked`
  now exposes both `errors` and `blockers`, so a caller cannot continue into
  DOCX generation after source-evidence, routing or template gates fail.
- Reconciled all global typography contracts with the active writer: EN value
  text and locked route prefixes are Times New Roman 12 pt; CN value text is
  宋体 12 pt. Removed stale Arial wording from the normative documents.
- Added a formal pytest entry point restricted to the maintained `tests/`
  suite so historical `_task_work` fixtures cannot contaminate release QA.
- Added regression coverage and OpenSpec traceability for the local rules.

## v3.27.5 — 2026-09-21

- Added the global source-fidelity gate shared by all sixteen Sections; output
  traceability can no longer authorize a value by repeating the value itself.
- Required reviewed evidence for non-verbatim English translations and named
  rules for approved derivations.
- Split global template/value/evidence constraints from local semantic rules
  for Sections 2, 8, 9, 10, 11, 12, 13 and 14.
- Fixed Section 11.2 three-column source-presence handling so its middle bold
  sublabel is never treated as a writable value.
- Added regression coverage for paraphrase rejection, local semantic policy
  registration and Section 11.2 route protection.
- Added the Agent overwrite SOP and made its reviewed stage record mandatory
  before template cloning; cross-Section routes remain explicitly supported.

## v3.27.3 — 2026-09-21

- Adopted the supplied `正式模板_MSDS_EN_冠志(1).docx` as the EN source record
  and active 16-row Section 8 baseline.
- Enforced value-only typography at the shared write boundary: EN values use
  Times New Roman 12 pt; CN values use 宋体 12 pt; both are left-aligned and
  vertically centered. Locked labels and bold template runs remain untouched.

## v3.27.2 — 2026-09-21

- Removed the over-broad `覆写产出` path-segment source gate. Original MSDS
  files may now be read from that directory tree while formal output filenames,
  runtime output/cache directories, and PDF-as-source blocking remain intact.

## v3.27.1 — 2026-09-21

- Added the single guarded value-write boundary: existing template labels,
  bold runs, paragraph properties, table geometry, cell properties, headers,
  footers and page fields remain template-owned assets.
- Added XML-level locked-template drift repair/audit and regression coverage
  for Section 9 labels and Section 11 child labels.
- Normalized full-width/half-width source text, escaped line breaks, legacy
  line endings and visual wraps before semantic field mapping.
- Preserved the V3.27.0 CN/EN template baselines and source hashes; no new
  template copy or parallel skill branch was introduced.

## v3.26.2 — 2026-09-18

- Added a fail-closed English product identity contract: the reviewed English
  product name must populate the existing EN Section 1.1 value cell and retain
  the model suffix; blank, model-only, Chinese or untraceable names block
  preflight and the rendered identity gate.
- Promoted the maintained EN template to a reviewed active baseline while
  preserving the supplied source record and all table geometry. Corrected the
  English header, canonical Section 6.1 wording, hand-protection contamination,
  punctuation and health-hazard route prefixes.
- Fixed the EN value typography path to use Arial 12 pt. Health-hazard prefixes
  are locked bold Arial 12 pt and their descriptions are regular Arial 12 pt;
  direct unstyled or 10.5 pt value writes are release-blocked.
- Added regression coverage and recorded the external TDS EN Times New Roman
  12 pt requirement without adding a TDS production mapper to this repository.

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

## [3.27.0] - 2026-09-20

### Added
- **User-Tuned Standard EN Master Template Integration (`examples/template_reference_en.docx`)**:
  - Adopted user-standardized 16-table EN template ("D:\应用缓存\Edge\模板_MSDS_EN_冠志 - 副本.docx") as the official master baseline (SHA-256: 38565de4ce59f2e34146d03ed3eefa692df4f42cc4d212d8e4fb7b098f924eef).
  - Standardized 16-table row geometry to [9, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2], adopting 12-row engineering controls architecture for Table 7 (Section 8).
- **Strict Bold Typography and Format Immutable Lock**:
  - Fully locked all 325 native bold runs across 16 tables (section headings, field labels, toxicological endpoints Oral:/Inhalation:/Fertility:, and regulatory clauses).
  - Cell value writes strictly inherit non-bold formatting from target cells without mutating labels or breaking run boundaries.
- **Table 7 Section 8.2 Hygiene & Zero-Chinese Enforcement**:
  - Cleared residual Chinese notes and tab indents from Table 7 Row 3 (Hand protection) while preserving native bold field label.
  - Enforced fail-closed zero-Chinese character gate across all English PDF outputs.
- **7-Page Exact Convergence**:
  - Optimized document trailing closure paragraph with 1pt micro line height, ensuring clean and deterministic 7-page rendering in WPS (kwpsconvert.exe), completely eliminating trailing 8th blank overflow page.
- **Full Test & Deliverable Verification**:
  - 258/258 Pytest automated test suite passing (100%).
  - Generated full 16 deliverables for benchmark model PA-3337A (4 MSDS DOCX + 4 MSDS PDF, 4 TDS DOCX + 4 TDS PDF) with zero defects.

## [3.26.6] - 2026-09-20

### Added
- **Jev System One Core Engine (`scripts/jev_engine.py`)**:
  - Integrated TypeSafe System One decision client (`JevEngine`) with official endpoint and API key (via environment variable `ZEN_API_KEY` / `JEV_API_KEY` or `~/.jev/zen.key`).
  - Implemented resilient connection pooling, exponential retry, and deterministic zero-stop fallback protection (`fallback_choice`, `fallback_noul`, `fallback_score`).
  - Added auditable `DecisionLedger` recording all decisions, prompts, confidence scores, and latencies into `jev_decision_ledger.json`.
- **Domain Decision & Gatekeeping Adjudicator (`scripts/jev_domain_adjudicator.py`)**:
  - Implemented 5 key arbitration scenarios: GHS Signal Word arbitration, Cross-Section Fact Routing, Independent Row Splitting per `independent_row_playbook.md`, TDS Technical Indicator Slot Mapping, and Pre-Release Semantic Consistency Auditing.
  - Architected dual-system fast/slow path routing: deterministic regex rules execute locally in 0ms, while ambiguous/borderline cases invoke on-demand Jev arbitration.
- **Full Unit Test Coverage (`tests/test_jev_engine.py`)**:
  - Added 9 comprehensive unit tests covering initialization, fallback on network error, signal word arbitration, cross-section routing, row splitting, TDS slot mapping, semantic consistency gate, and decision ledger export (258/258 tests passing).

## [3.26.5] - 2026-09-20

### Added
- **Permanent Unified Value Typography Enforcement (`set_cell_value_unified`)**:
  - Implemented `set_cell_value_unified` in `MSDS Skill/scripts/section2_ghs_policy.py`, guaranteeing that every table value cell across all 16 sections strictly enforces 12.0 pt (`<w:sz w:val="24"/>` / `<w:szCs w:val="24"/>`), exact fonts (Arial for English/numbers, 宋体 for Chinese), single-run-per-line run structure, explicit bold control, and elimination of dangling empty paragraphs.
  - Resolved the fundamental `cell.text = ...` style destruction defect by cleanly clearing cell paragraphs while preserving or setting explicit `<w:rPr>` properties.
- **Strict Verbatim Source Routing for Section 2 Label Elements**:
  - Enhanced `MSDS Skill/scripts/jev_dispatcher.py` (`route_s3_to_s2`) and extraction rules to strictly mirror source text verbatim without unauthorized rephrasing or omission.
  - Section 2.2 GHS Label Elements strictly outputs verbatim source: `羟基丙烯酸酯聚合物GHS危险性分类：不适用\n请注意以下物质：\nN,N-二甲基乙醇胺，中和剂，已键合为盐，质量浓度小于2.0%` (CN) and synchronized accurate English equivalent.
- **Independent Row and Paragraph Separation Playbook (`independent_row_playbook.md`)**:
  - Authored comprehensive playbook codifying the 3 core separation laws: 主客体分行律 (Subject-Object Separation Law), 分类边界律 (Categorical Boundary Separation Law), and 指标对照分行律 (Metric Pair Separation Law).
  - Enforced independent table row / paragraph splitting in Section 11 Table 10: product-level study status (`该产品无可用的毒理学研究。` / `No toxicological studies are available on the product itself.`) and polymer component data (`羟基聚丙烯酸酯分散体：\n毒性：无资料；刺激性：无资料。`) are cleanly separated into distinct independent rows instead of being congested together.
- **Fail-Closed Value Typography Release Audit Gate**:
  - Extended `MSDS Skill/scripts/audit_section2_release.py` with `audit_value_cell_typography(docx_path)`, inspecting all table value cells to verify that font size is strictly 12.0 pt (`sz=24`), bold status matches semantic specification, and empty/unformatted runs are rejected.
  - Added full test coverage in `MSDS Skill/tests/test_value_typography_enforcement.py` (3 test suites) and regression tests in `test_ghs_resolver_and_jev.py`.

## [3.26.4] - 2026-09-20

### Added
- **GHS Precautionary Code Reverse Resolver (`scripts/ghs_code_resolver.py`)**:
  - Automatically resolves natural language safety, emergency handling, storage and disposal text to canonical alphanumeric GHS P-codes (`P280`, `P264`, `P270`, `P271`, `P304+P340`, `P305+P351+P338`, `P302+P352`, `P301+P330+P331`, `P391`, `P370+P378`, `P403+P235`, `P501`).
  - Standardizes precautionary output into four distinct blocks: 预防措施 / Prevention, 事故响应 / Response, 安全储存 / Storage, 废弃处置 / Disposal.
- **Jev System One Dispatcher (`scripts/jev_dispatcher.py`)**:
  - Integrates `C:\Users\Administrator\.jev\jev.py` (`decide_choice`) for intelligent routing and signal word resolution.
  - Automatically recognizes `警告词：警告` as canonical Signal Word (`警告` in CN, `Warning` in EN).
  - Intelligently extracts Section 3 amine neutralization / SCL threshold notes and routes them into Section 2.3 GHS Label Elements.
- **Section 2 Non-Hazard & Skeleton Preservation Refinement**:
  - Corrected over-suppression policy: substantive hazard statements (`没有明显的已知作用或严重危险。`), physical/chemical hazards (`对水体、土壤可造成一定的污染。`), and environmental hazards are strictly preserved.
  - Guaranteed continuous renumbering across all visible rows without phantom row leaks.
- **Section 11 Multi-Tier Toxicology Transparency**:
  - Explicitly states polymer-tier lack of data (`羟基聚丙烯酸酯分散体：毒性：无资料；刺激性：无资料`).
  - Explicitly binds and displays toxicological reference component with CAS number (`二丙二醇丁醚，CAS 29911-28-2`).

## [3.26.3] - 2026-09-18

### Added
- **Strict Non-Hazard Section 2 Suppression**:
  - Automatically suppresses absent H-statements (2.3), P-statements (2.4), physical/chemical hazards (2.5), and health hazard route breakdowns (2.6) when a substance is explicitly classified as non-hazardous under GHS.
  - Automatically clears phantom/inherited H/P statements during fact extraction if no explicit hazard codes are present in the source text.
- **Enhanced Section 2 Non-Hazard Release Audit Gate (`audit_section2_release.py`)**:
  - Prohibits CMR/high-risk precautionary statements (`P201`, `P202`, `P405 储存处须加锁` / `Store locked up`) on non-hazardous chemicals.
  - Detects and blocks illogical health hazard route synthesis (e.g. `吸入：可能引起轻微的皮肤刺激`).
  - Audits continuous post-omission numbering continuity (`2.1` -> Pictogram -> `2.2` -> `2.3`).
  - Detects and blocks duplicated label wording (e.g. `其他危害其他危害`).
- **Synchronized CN/EN Non-Hazard Glossary**:
  - Added controlled translations in `professional_translation_glossary.tsv` for `无信号词` (`No signal word`), `无危险的象形图` (`No hazard pictogram`), `未被分类` (`Not classified`), transport non-hazard statements, and confidential trade secrets.

---
# Changelog

## v3.27.4 — 2026-09-21

- Preserved the maintained template's centered paragraph alignment for all
  Section 3 component, CAS and concentration value cells in both languages;
  the final value-typography gate no longer flattens those cells to left
  alignment.
- Classified three-column Section 11.2 rows like the existing 11.1/11.7
  endpoint rows: only the final cell is writable, while the first two cells,
  including bold sublabels, remain template-owned and excluded from value
  typography enforcement.
