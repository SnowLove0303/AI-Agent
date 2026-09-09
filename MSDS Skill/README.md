# MSDS Skill 3.18.1

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
- Section 8.2 uses the formal template's top-level four-column control-parameter rows (`物质 / 依据 / 类型 / 数值`; EN `Substance / Basis / Type / Value`) with source-grounded data-row projection; with no verified records a single data row carries the exact missing-data placeholder in the value column.
- Release-blocking audits and full-page visual QA.
- Feishu 17-section skeleton mutation whitelist: sequence/label columns and
  template-owned geometry are locked; only approved value cells, structured
  S3/S8.2 rows, semantic note slots, source pictograms, S2/S9 omission and
  explicit Section 11 aliases may change.
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
  across audits; PDF conversion stays ordered for deterministic office output.
- Active template files are byte-pinned before cloning; a changed or
  unapproved template baseline blocks release.
- Approved facts require a source-bound, reviewed S1-S16 mapping manifest with
  an explicit disposition for every extracted candidate, so unresolved or
  silently omitted source material cannot enter a formal build.

## Entrypoint

Read [`SKILL.md`](SKILL.md) for the operating contract. The reusable scripts, tests, references, approved template and v2.9 inheritance assets are kept inside this directory.

## Version

Public release: `MSDS Skill 3.18.1`

Template baseline: user-supplied formal CN/EN templates, with CN SHA-256
`3cb250303778b70ab0dbfedc4392ac628228d80146e6376f410157cb08993622` and EN
active SHA-256 `003ff6bac27bf3bc99f0426ea8ed596487b0399f30428c406227d8f7c1b3dd46`
(formal template plus the v3.15.1 Hand protection label correction; the
unchanged source record `template_reference_en_source.docx` remains
`59445b62c6d33b25a2e04c05778d428656f1ce0cbe7c21212721b145468c4416`).

The public release contains Skill source and validation assets only.
Customer-specific generated files, temporary runs, rendered QA images and
interpreter caches are not part of the release.

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
