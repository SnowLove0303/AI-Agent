# MSDS Skill 3.20.0

`MSDS Skill` is the controlled MSDS/SDS standardization skill for producing synchronized Chinese and English deliverables for the Guanzhi and Guocai company profiles.

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
  DOC/ODT/RTF use a temporary LibreOffice conversion, and XLS/XLSX/TXT source
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

## Entrypoint

Read [`SKILL.md`](SKILL.md) for the operating contract. The reusable scripts, tests, references, approved template and v2.9 inheritance assets are kept inside this directory.

## Version

Public release: `MSDS Skill 3.20.0`

Template baseline: the current user-supplied formal CN/EN templates are adopted
byte-for-byte. CN SHA-256 is
`b6c52c3d6003d4314e578733c5066dc9541c70ee49957ab56c24dd749ade2d43`. EN source
and active SHA-256 are both
`34a259eed50d2e78b4609c66453fa9baab610a623dcc7ee531db359b1a988497`.
Historical template copies and versioned snapshots are intentionally excluded
from the distributable package. Rollback evidence must be stored outside the
active skill directory.

The public release contains current Skill source and validation assets only.
Version 3.20.0 adds a DOCX-first matrix scheduler, WPS converter preflight and
cache, bounded PDF parallelism, progress checkpoints and an optional audited
DOCX preview directory for slow Harness environments. Version 3.19.1 removed
historical templates, stale regression
outputs, generated caches and broken `_task_work`-dependent tests. Source
interpretation remains fail closed: the Agent must
complete source coverage, fact provenance, reviewed mapping and output
traceability before any template is cloned. The mutation boundary remains
exact: only label-value cells, empty/hide decisions and necessary styled
data-row changes are allowed; labels, sequence, bold formatting and document
layout are immutable.
Customer-specific generated files, temporary runs, rendered QA images and
interpreter caches are not part of the release.

## DeepSeek Harness run

Run the production entry point once for the reviewed facts model:

```text
python scripts/build_eight.py --source SRC.docx --facts MODEL.json --out OUT \
  --pdf-workers 2 --progress-file OUT/matrix-progress.json \
  --docx-preview-dir OUT/_docx_preview
```

The command validates the source and facts once, builds all four audited DOCX
masters first, then converts the four PDFs as a bounded batch. The
`MSDS_PROGRESS` lines and checkpoint file show whether the run is in source
validation, DOCX construction or PDF conversion. Use `--pdf-workers 1` if the
host WPS process is not concurrency-safe. `--no-pdf` is diagnostic only and
does not satisfy the eight-file release contract. No LibreOffice or
`soffice.exe` is bundled or used as a fallback.

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
