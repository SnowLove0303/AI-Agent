# MSDS Skill 3.26.4

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
remediation, Arial 12 pt value prototypes, bold health-hazard route prefixes,
and fail-closed English value typography checks. TDS production remains
outside this repository and is recorded as an external follow-up.

V3.26.0 adds source/cache reuse, a read-only shared audit context and
non-publishing efficiency telemetry/benchmarking. It keeps WPS conversion
bounded and conservative, does not bundle another office engine, and does not
turn cache hits or benchmark checkpoints into approval or release gates.

## Scope

- One source-grounded semantic model.
- Four synchronized DOCX masters: Chinese/English × Guanzhi/Guocai.
- Four PDFs derived one-to-one from the final audited DOCX files.
- Fresh-clone in-place overwrite of the approved template.
- One physical row per Section 3 component.
- Structured Section 11 toxicology through 11.10.
- Section 9 omission of pure missing-data rows followed by continuous renumbering.
- Source-grounded facts only; example values embedded in the template are not product facts.
- Locked template geometry, labels, paragraph/run formatting and header/footer conventions.
- Bold labels/runs, bold EN health-hazard route prefixes, CN route prefixes
  and structured middle sublabels are all template-owned locks; S3 remains
  three physical columns
  and S8.2 remains four physical columns. Only declared final value cells,
  source-gated hide decisions and necessary styled row insertions are writable.
- Section 8.2 uses the formal template's top-level four-column control-parameter rows (`物质 / 依据 / 类型 / 数值`; EN `Substance / Basis / Type / Value`) with source-grounded data-row projection; with no verified records the complete workplace-component block is hidden and no synthetic missing-data row is emitted.
- Release-blocking audits and full-page visual QA.
- Feishu 17-section skeleton mutation whitelist: sequence/label columns and
  template-owned geometry are locked; the Agent may change only approved value
  cells, empty/hide decisions and necessary styled data rows. Pictograms,
  aliases, numbering and company/header/footer fields are runtime-controlled.
- Source `主要粘膜刺激性` is mapped to the existing `11.3 主要眼睛刺激性`
  endpoint without inventing an additional conclusion or moving it to 11.10.
- A unified deliverable evaluation layer assigns a fixed 100-point quality
  score, applies B0/B1/B2 release blockers, and emits one evidence-complete
  audit report for every eight-file package.
- Source discovery is explicit and hash-bound: DOCX/DOCM extract directly,
  DOC/ODT/RTF use a source-hash-bound LibreOffice conversion cache, and XLS/XLSX/TXT source
  files are discoverable but remain blocked from guessed 16-section extraction
  until their semantic adapters are approved. PDF is output-only.
- S1-S16 table behavior is declared in one executable overwrite-rule registry;
  payload shape, table structure and allowed omission boundaries are checked
  before writing values.
- Matrix builds reuse immutable template documents and the saved in-memory DOCX
  across audits; all four DOCX masters finish before a bounded parallel PDF
  batch starts, with Harness-visible progress checkpoints.
- Active template files are byte-pinned before cloning; a changed or
  unapproved template baseline blocks release.
- Approved facts require a source-bound, reviewed S1-S16 mapping manifest with
  an explicit disposition for every extracted candidate, so unresolved or
  silently omitted source material cannot enter a formal build.
- Approved facts also require a source-coverage inventory, stable-ID fact
  ledger and reviewed output-traceability record. Every source fact must be
  disposed, every output value must point to evidence, and unreadable,
  ambiguous or conflicting source content blocks the build before template
  cloning.
- Source interpretation,取舍 and semantic line-break rules are documented in
  `docs/source_interpretation_playbook.md` and enforced by
  `scripts/source_interpretation_contract.py`.
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

Public release: `MSDS Skill 3.26.3`

Template baseline: the current user-supplied formal CN/EN templates are adopted
byte-for-byte for the CN source and as a reviewed maintainer remediation for
the EN active baseline. CN SHA-256 is
`b6c52c3d6003d4314e578733c5066dc9541c70ee49957ab56c24dd749ade2d43`. EN source
SHA-256 is `34a259eed50d2e78b4609c66453fa9baab610a623dcc7ee531db359b1a988497`;
EN active SHA-256 is
`49a279aa8c7a50f38ee6929ca2f030cf13b01ee0d1e476d790a2352a316bfa2b`.
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
