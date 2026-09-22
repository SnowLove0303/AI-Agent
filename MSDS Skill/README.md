# MSDS Skill 3.27.11

V3.27.11 installs per-route Section 2 health-hazard de-duplication and
source-preserving extraction: only the route covered by Section 2.5 H/EUH text
is suppressed, uncovered source 2.7/2.8 routes remain complete, and 2.6
first-aid route instructions cannot leak into health-hazard rows. V3.27.10
installs the new user-approved CN/EN table-style baselines while
retaining the shared Section 6 divider enforcement and Section 11 endpoint/value
de-duplication. V3.27.9 strengthens Section 2 line structure and reviewed typo handling:
GHS classifications keep each class/H-code pair on its own line, H/P
statements are split into logical code lines, label elements retain a
title-plus-explanation shape, and the source typo `依然液体` is corrected to
`易燃液体` only when the same reviewed fact contains H226.

V3.27.4 preserves the locked labels and applies one value-write typography boundary: EN values are Times New Roman 12 pt and CN values are 宋体 12 pt; ordinary values are left-aligned and vertically centered, while the three Section 3 component data columns retain the template's centered alignment. Legitimate original sources under `覆写产出` remain allowed. The English 16-table master template (`examples/template_reference_en.docx`) uses Section 8 geometry `[9, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2]`.

V3.26.6 embeds the Jev System One Core Engine (`scripts/jev_engine.py`) and Domain Adjudicator (`scripts/jev_domain_adjudicator.py`), providing on-demand TypeSafe System One decision making, fast/slow dual-path routing, and an auditable Decision Ledger.


V3.26.5 permanently enforces 100% unified 12.0 pt value cell typography via `set_cell_value_unified`, guarantees verbatim Section 2 label elements from source files, and codifies the Independent Row and Paragraph Separation Playbook (`docs/independent_row_playbook.md`) ensuring product-level status and polymer data are cleanly separated into independent table rows.


V3.26.4 introduces the GHS code reverse-resolver (`scripts/ghs_code_resolver.py`), Jev System One dispatcher (`scripts/jev_dispatcher.py`), signal word recognition, Section 3 amine salt neutralization note intelligent routing into Section 2.3, and multi-tier toxicology reporting in Section 11.



`MSDS Skill` is the controlled MSDS/SDS standardization skill for producing synchronized Chinese and English deliverables for the Guanzhi and Guocai company profiles.

V3.25.3 makes the value typography, Section 2 route semantics, Section 8 PPE alignment and layout boundaries explicit: template-bold content
is locked label/structure content; every writable value is inherited from the
template value anchor with bold removed or explicitly disabled. A semantic
release gate blocks any non-empty bold value while ignoring locked labels,
sublabels, headers and Section 2.8 route prefixes.
The pre-clone router rejects synthesized Section 2.1 emergency overviews and
cross-target fact duplication. Output-only S8.2 topology and S11.4 vertical
alignment audits block structural drift while keeping the formal templates
byte-pinned.

V3.26.3 adds a reviewed English product-name gate, active English-template
remediation, Arial 12 pt body typography, and formal TDS separation.
- V3.25 adds fail-closed source grounding, S15/S16 one-cell de-duplication,
  Section 11 alias and short-row policies, deterministic WPS timeout cleanup,
  and per-model `WORD`/`PDF` output isolation.
- V3.24 fixes the business-stage boundary: the runtime fully extracts source
  information first, performs constrained semantic normalization second,
  overwrites a fixed cloned template third, and performs only bounded
  hide/insert/renumber fine-tuning last. The active contract is
  `openspec/efficiency_contract.md`.

## Entrypoint

Read [`SKILL.md`](SKILL.md) for the operating contract. The reusable scripts, tests, references, approved template and v2.9 inheritance assets are kept inside this directory.

## Version

Public release: `MSDS Skill 3.27.10`

Template baseline: the current user-supplied formal CN/EN templates are kept
as source records, while active baselines normalize value cells only. CN source
SHA-256 is `748f68968c2ddf1d2558d5c6e5879a7b5d76ab1be12fe70fed130f9fe9424b5f`;
CN active SHA-256 is
`8b0b633b527fad0c2311528e6e252fff73ceb8fcd1a39e91169efd0d5dd4df84`. EN source
SHA-256 is `a5fef82b43f6ad0d32350c3c715ee05f6c41eead2ff90d26efbbbd5784434f3c`;
EN active SHA-256 is
`11e3da3b1eb1b4694f891e8e94f1901f6c000b22af84cca769b268e4925af800`.
Historical template copies and versioned snapshots are intentionally excluded
from the distributable package. Rollback evidence must be stored outside the
active skill directory.

The public release contains current Skill source and validation assets only.
Version 3.25.0 adds a second source-grounding audit that rejects template-only
product values, keeps the full label-ingredient explanation separate from the
signal-word slot, de-duplicates one-cell S15/S16 payloads, sanitizes empty
source rows, records the S11.4 short-row exception, isolates final output at
`OUT/MODEL/WORD` and `OUT/MODEL/PDF`, and kills/reaps owned WPS processes on
timeout. Version 3.24.2 adds the compatibility patch on top of the locked template
boundary: source-gated Section 8 recommendations are retained, controlled
non-hazard signal words are accepted, compact Chinese model suffixes are not
duplicated, and Section 2 health-hazard composite rows survive legal numeric
renumbering. Version 3.24.1 hardens the template mutation boundary: Section
2.8 route prefixes survive clear/overwrite, Section 11 middle sublabels are
explicitly locked, and physical three-/four-column topology is registered and
audited.
Version 3.24.0 adds the four-stage overwrite contract, precomputed semantic
write plans, actionable expected/actual/diff/hint diagnostics and stage
telemetry. Version 3.23.0 adds nested-table source extraction, semantic Section 11
endpoint-skeleton alignment, safe merged-row omission, five-character Section
9 prefix spacing, source-backed NCO property splitting, source-sized pictogram
insertion and current localized revision-date stamping with the template's `P`
clipping guard. It preserves the v3.22.0 strict Section 2
label-elements/signal-word separation on top of the 3.21.0 reusable
source-evidence packet, persistent legacy-source conversion cache and a
one-shot non-mutating facts preflight on top of the
DOCX-first matrix scheduler, WPS converter preflight and cache, bounded PDF
parallelism, progress checkpoints and an optional audited DOCX preview
directory for slow Harness environments. Version 3.19.1 removed
historical templates, stale regression
outputs, generated caches and broken `_task_work`-dependent tests. Source
interpretation remains fail closed: the Agent must
complete source coverage, fact provenance, reviewed mapping and output
traceability before any template is cloned. The mutation boundary remains
exact: only label-value cells, empty/hide decisions and necessary styled
data-row changes are allowed; labels, sequence, bold formatting and document
layout are immutable.
Customer-specific generated files, temporary runs, rendered QA images and
interpreter caches are not part of the release. Stage timings are observational
and are not a fixed SLA; fast feedback never bypasses final semantic, format,
geometry, whitespace, source or render gates.

The V3.26 benchmark command writes only to a temporary private directory:

```text
python scripts/benchmark_efficiency.py --source SRC.docx --facts MODEL.json \
  --docx-only --worker-counts 1,2,3 --runs 2
```

The matrix report's additive telemetry distinguishes measured machine time
from explicitly supplied Agent/manual review and human wait time, records
source-cache decisions, bounded PDF scheduling and final artifact hashes.

For a resumable Harness run, use `scripts/run_efficiency_workflow.py` as the
single entrypoint. The first call prepares or reuses `evidence-packet.json`
and stops at the required review checkpoint. A second call with the reviewed
`--facts` JSON runs the non-mutating preflight and invokes the formal matrix
builder only after `PREFLIGHT_PASS`. This avoids repeated product-specific
fact builders, duplicate extraction, partial template builds and manual
deployment copies while preserving every approval and release gate.

## DeepSeek Harness run

Run the production entry point once for the reviewed facts model:

```text
python scripts/build_eight.py --source SRC.docx --facts MODEL.json --out OUT \
  --pdf-workers 2 --progress-file OUT/matrix-progress.json \
  --docx-preview-dir OUT/_docx_preview --cache-dir OUT/.msds_cache
```

The command validates the source and facts once, builds all four audited DOCX
masters first, then converts the four PDFs as a bounded batch. The
`MSDS_PROGRESS` lines and checkpoint file show whether the run is in source
validation, DOCX construction or PDF conversion. Use `--pdf-workers 1` if the
host WPS process is not concurrency-safe. `--no-pdf` is diagnostic only and
does not satisfy the eight-file release contract. No LibreOffice or
`soffice.exe` is bundled or used as a fallback.

Final files are promoted to `OUT/MODEL/WORD` (four DOCX) and
`OUT/MODEL/PDF` (four PDF); `OUT/MODEL/matrix-report.json` is the corresponding
matrix evidence. The optional `OUT/_docx_preview` directory is diagnostic only.

Run the unified release audit with:

```powershell
python scripts/audit_deliverable_package.py <package-root> <MODEL> `
  --template-cn examples/template_reference.docx `
  --template-en examples/template_reference_en.docx
```

The command writes `audit/deliverable-audit.json` and
`audit/deliverable-audit.txt`. `RELEASE_PASS` requires a complete eight-file
matrix, complete evidence, no B0/B1 blocker and a score of at least 95/100.
Read `docs/deliverable_evaluation_standard.md` and
`docs/deliverable_audit_checklist.md` for the customer-delivery gate.

Before preparing approved facts, inspect the source interpretation result with:

```powershell
python scripts/source_interpretation_contract.py <source> <facts.json> --model <MODEL>
```

The command must return `ready` before `scripts/build_eight.py` may clone or
mutate a template. A draft from `scripts/extract_source_facts.py` is expected
to return `blocked` until the Agent completes the evidence, mapping and output
traceability records.

For repeated Harness runs, prepare the source evidence once and reuse it:

```powershell
python scripts/prepare_evidence_packet.py --source SRC.docx --model MODEL `
  --out OUT/evidence-packet.json --cache-dir OUT/.msds_cache
```

The packet is review-required and is not approved facts. It must never be
passed as `--facts`; the Agent must complete source mapping, empty decisions,
traceability and execution acknowledgement in a separate approved model.
After the Agent finishes the review, run the all-errors preflight before the
production build:

```powershell
python scripts/build_eight.py --source SRC.docx --facts MODEL.json `
  --model MODEL --preflight-only --preflight-report OUT/preflight.json
```

The resumable sequence is therefore `prepare packet -> review -> preflight ->
build`. A matching packet is reported as reused, while stale source bytes,
adapter/schema changes or an invalid cache entry trigger fresh mechanical work.
