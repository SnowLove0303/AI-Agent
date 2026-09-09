---
name: msds-unified-four-format-standardizer
description: One maintained MSDS/SDS standardization skill that discovers supported source files, binds source-grounded facts to synchronized CN/EN outputs for Guangzhou Guanzhi and Yingde Guocai, preserves locked templates, and releases four DOCX plus four PDF deliverables only after semantic and render QA.
---

# Unified MSDS Eight-Deliverable Standardizer v3.18.0

## Mandatory v2.9 inheritance (release blocker)

This unified skill is an additive superset of `MSDS_Word_Standardizer_Skill_v2.9`. **All v2.9 overwrite content, programs, requirements, fixtures, and QA behavior remain binding.** Read `docs/v2_9_inheritance_contract.md`. Before release, `scripts/audit_v29_inheritance.py` MUST pass against the canonical v2.9 ZIP. Section 11 structured-toxicology handling is an enhancement layer; it must not delete unrelated v2.9 behavior.

## 0. Default deliverable
Given one source MSDS/SDS, default to **eight synchronized deliverables**: four authoritative editable DOCX files plus four publication PDF files derived from those DOCX masters:
1. `<MODEL>_MSDS_CN_冠志.docx`
2. `<MODEL>_MSDS_CN_国彩.docx`
3. `<MODEL>_MSDS_EN_冠志.docx`
4. `<MODEL>_MSDS_EN_国彩.docx`
5. `<MODEL>_MSDS_CN_冠志.pdf`
6. `<MODEL>_MSDS_CN_国彩.pdf`
7. `<MODEL>_MSDS_EN_冠志.pdf`
8. `<MODEL>_MSDS_EN_国彩.pdf`

The DOCX files are the semantic/layout masters. Each PDF MUST be converted from its corresponding final audited DOCX; never independently author or edit PDF content. If the user explicitly requests DOCX-only or PDF-only, honor that scope. Otherwise `ALL` means all eight files.

This package remains an additive superset of the Chinese v2.9 overwrite core. Maintain one semantic pipeline only.

## 1. Architecture: one truth, two language layers, two company overlays
Use this pipeline:

`source facts -> normalized semantic model -> omission/mapping -> CN/EN language layer -> Guanzhi/Guocai company overlay -> DOCX -> audits -> render QA`

Hard rules:
- **Source MSDS controls product facts.**
- **Bundled latest approved template controls Word geometry.**
- **Language layer controls professional wording, never facts.**
- **Company overlay controls only approved company-profile fields.**
- Never maintain four independent content copies.
- Never translate from the already-rendered CN output to make EN. Both CN and EN must derive from the same normalized source facts, preventing semantic drift.

## 2. Template authority
The language-specific template baselines are authoritative:

- CN: `examples/template_reference.docx`, the approved formal baseline with the row-break correction recorded in v3.15.8.
- EN source record: `examples/template_reference_en_source.docx`, an unchanged copy of the user-supplied formal `正式模板_MSDS_EN_冠志.docx`.
- EN active baseline: `examples/template_reference_en.docx`, the formal EN template plus the v3.15.1 Hand protection label correction and the v3.15.8 row-break correction.
- The v3.13 CN/EN baselines (nested 8.2 child-table design) are retained at `examples/archive/template_reference_cn_v3.13_8.2_nested_child_table.docx` and `examples/archive/template_reference_en_v3.13_8.2_nested_child_table.docx` for rollback/audit only.
- The previous v3.11 EN baseline is retained at `examples/archive/template_reference_en_v3.11_pre_field_update.docx` for rollback/audit only.
- The previous v3.12 CN/EN baselines are retained at `examples/archive/template_reference_cn_v3.12_pre_8.2_child_table_update.docx` and `examples/archive/template_reference_en_v3.12_pre_8.2_child_table_update.docx` for rollback/audit only.
- The former normalized EN baseline is retained separately at `examples/archive/template_reference_en_v3.10_normalized.docx` and is historical evidence only; it is not an active template.

Pinned SHA-256:

- CN: `3cb250303778b70ab0dbfedc4392ac628228d80146e6376f410157cb08993622`
- EN source: `59445b62c6d33b25a2e04c05778d428656f1ce0cbe7c21212721b145468c4416`
- EN active baseline: `003FF6BAC27BF3BC99F0426EA8ED596487B0399F30428C406227D8F7C1B3DD46`.

Structural baseline:
- 16 tables
- CN row counts: `[10,16,6,6,5,4,3,16,24,6,18,6,3,5,9,2]`
- EN row counts: `[9,16,6,6,5,4,3,16,24,6,18,6,3,5,9,2]`
- CN and EN are intentionally different physical templates. Shared semantic content and overwrite rules do not require identical physical row counts or label wording.
- Section 11 current multi-column/merged-cell geometry is locked.
- Section 12 current 6-row geometry is locked.
- Section 15 current 9-row geometry is locked.
- Section 2 includes the uploaded template's revised hazard-label structure.
- Section 8 includes the uploaded template's `Hand protection` and `8.2 Engineering controls` slots.
- Section 8.2 uses the formal template's top-level four-column control-parameter rows: a one-cell `工作场所组分控制参数 / Control parameters for workplace components` parent row, one locked header row (CN `物质 / 依据 / 类型 / 数值`; EN `Substance / Basis / Type / Value`), then data rows. Only source-grounded data rows may be written or cloned; the parent row, header wording/topology and grid are locked. The two template example OEL rows are illustrative structure only and MUST be cleared. With verified source records they are replaced by source data rows; with no source records the complete workplace-component block is removed, including its parent/header/data rows. Never emit a synthetic `无数据` / `No data available` row for an absent workplace-parameter block.
- Section 11 includes the uploaded template's structured rows through `11.10 Additional information`.
- The v3.6.2 template geometry update changes only approved border styling: Section 8 internal PPE boundaries use dotted borders with the adjusted boundary edges around the first exposure-control rows; Section 11 uses dotted boundary edges around its introductory/reference-data transition row. No table count, row count, grid width, merge, paragraph-property or run-property baseline changed.
- The complete structural snapshot, including paragraph/run properties and header/footer parts, is pinned in `tests/template_snapshot.json` and `tests/template_snapshot_en.json`; versioned v3.14 copies are retained in `tests/template_snapshot_v314.json`, `tests/template_snapshot_en_v314.json`, `tests/template_geometry_v314.json` and `tests/template_geometry_en_v314.json`.
- Section 3 component rule: every component occupies exactly one physical data row. Never pack multiple component names, CAS numbers or concentrations into one row separated by line breaks. If the source has more components than the template's initial slots, clone the existing styled component row in place and preserve its OOXML geometry.

A newer user-approved template immediately supersedes this one. Do not restore geometry or paragraph formatting from older outputs. Text visible in the template (including PEA-4139, example ingredients, hazards, toxicology and ecology values, and the two 8.2 example OEL rows) is illustrative structure only and MUST NOT become product facts.


## 2A. Highest-priority in-place overwrite contract
This rule overrides every language/layout convenience rule. Each CN deliverable MUST be created by cloning `examples/template_reference.docx`; each EN deliverable MUST be created by cloning the independent `examples/template_reference_en.docx`; all four are then mutated in place. Never create an EN document from a blank document, from a rebuilt table set, or from a rendered CN output. Never add a CN-only row to the EN template merely to equalize section capacity.

The template owns: table count/order, row/column geometry, grid, merges, cell properties, borders, widths, section placement, label cells, paragraph properties, character-format anchors, and page-crossing behavior. All maintained formal templates permit tables and rows to continue across pages; no active baseline row may carry `cantSplit`, and this must remain true after generation. The source owns facts only. The language layer may select an existing language-appropriate template label, but it may not generically rewrite, rebuild or normalize sequence/label cells. The only source-faithful CN Section 2 label exception is the verified source heading `标签要素` (the baseline says `GHS标签要素`) and the requested trailing colon on `其他危害`; the pipeline applies these two aliases by run-level replacement and the format audit canonicalizes only them. The shared runtime builds a slot registry from the fresh clone before clearing values: a non-empty template value object is writable, an intentionally blank object is not writable unless the semantic contract explicitly marks it as an input slot, and Section 8.2 data rows are handled only by their dedicated writer. This prevents source data from leaking into blank template slots; the Section 8 `建议 / Recommendation` value is deliberately always blank in formal output. The active CN baseline's known tabbed illustrative suffix on the `手部防护` label is removed at clone time by a run-preserving, geometry-neutral sanitizer; this is the only other label-text exception.

Deletion of an unsupported item must use the smallest safe template boundary. It may remove a whole dedicated row when that row is exactly one item; otherwise it must suppress only the unsupported item without damaging supported siblings or merge/grid integrity. After suppression, all four variants MUST have the same semantic item-presence set.

**Release blocker:** if any output cannot prove lineage from the pinned template snapshot or fails geometry equivalence after allowed row suppression, do not deliver it. The active CN, EN and EN-source template files are byte-pinned; a changed baseline hash blocks the run before any clone is made. A template is not replaceable by a prior output, a rendered PDF or an unapproved copy.

## 3. Locked-format contract
Bold template labels and table geometry are locked: wording for the selected language, punctuation, run formatting, paragraph formatting, merges, widths, borders and row structure must not be casually rebuilt.

Allowed mutation exception: after an explicitly permitted whole-row omission, numeric prefixes may be changed to restore continuous visible section numbering. Only the numeric prefix is mutable. The complete executable boundary is defined in `docs/template_mutation_whitelist.md` and enforced by `scripts/template_mutation_whitelist.py` plus `scripts/audit_template_mutation_whitelist.py`.

Avoid destructive APIs such as `paragraph.text = ...` or `cell.text = ...` on formatted template content when they would destroy runs. Prefer run-level replacement and OOXML-safe operations. Preserve the template's table-cross-page contract: tables and all surviving rows may span pages, row-level `cantSplit` is forbidden in active baselines and outputs, and repeating-header settings must remain intact. Never insert artificial page breaks to compensate for content.

The executable per-section contract is maintained in
`scripts/section_overwrite_rules.py`. Every S1-S16 table must use its declared
semantic writer, value scope, empty-value policy and structural-mutation
boundary; an unregistered or positional payload is a release blocker.

For inserted non-bold Chinese body text, retain the approved body-character-format convention from the existing baseline. For English, preserve the same template geometry and use a compatible professional body-text run format; allow natural English wrapping rather than fake alignment.

### 3A. Template mutation whitelist

The sequence column and label column are locked by default. Only the following
mutations are allowed:

- write source-grounded content to an existing field-value cell;
- maintain an existing one-cell note slot as a whole semantic slot;
- write only name/CAS/concentration to S3 component data rows, one component per row;
- write only approved source-grounded data to the S8.2 top-level four-column data rows; with no verified records remove the complete workplace-component block, including parent/header/example rows;
- insert an explicitly sourced GHS pictogram into the existing pictogram value slot;
- remove a complete pure-missing-data row only under the S2/S9 omission policy;
- change only the numeric prefix after that approved omission;
- project only the two verified CN Section 2 source-heading aliases (`标签要素：` and `其他危害：`) by run-level replacement;
- route a verified source endpoint alias to an existing standard endpoint without changing the source value.

Any mutation to locked cell formatting, an unapproved locked label's wording, table geometry,
merge topology, grid width, borders, row height, header/footer structure or
page-number fields or page-crossing settings is a release-blocking failure. In particular, generic
`set_cell_text`/paragraph reconstruction must not be used on sequence or label
cells.

## 4. Source-grounding and omission
Never invent:
- CAS/EC numbers
- concentrations
- GHS classes
- H/EUH/P codes
- toxicology/ecology results
- exposure limits
- UN/transport classifications
- regulatory conclusions
- official company English legal names

For customer-facing MSDS output, a source-supported missing value normally uses `无数据` in Chinese or `No data available` in English. Do not add provenance commentary such as `源文件未提供` or `source file not provided`. Endpoint-specific rules below override this default: source-backed Section 2 `其他危险` preserves the source wording such as `无适用资料。`; Section 11.7 writes `无数据` only when the source explicitly has that endpoint with missing data; absent Section 11.7 children are hidden. This Section 11.7 child-field matching requirement must not be generalized into a blanket Section 11 omission rule: for every Section 11 endpoint, a source-backed explicit missing-data phrase remains the endpoint value, while only a source-absent or unmatched endpoint is hidden. The shared model distinguishes `SUPPORTED`, `EXPLICIT_MISSING`, `NOT_APPLICABLE`, and `ABSENT`; only an explicit endpoint state may produce a placeholder, while an absent template-only field is suppressed.

Section 9 property exception: when a property value is only a missing-data placeholder, omit the entire dedicated property row before customer-facing write. Do not leave a blank row. Renumber the surviving visible Section 9 properties continuously in original semantic order. Preserve substantive values, including `不适用` / `Not applicable`, measured values and source-supported `其他信息` / `Other information`.

Do not treat `不适用` or substantive negative conclusions as missing data. Keep conclusions such as `非危险品`, `无危险反应`, `初沸点以下无闪点`, or `未满足分类标准` when source-supported.

Section-level explanatory sentences such as `该产品无可用的毒理学研究。` may be substantive context and must be preserved when they introduce supported component/reference data. When all Section 11 or Section 12 endpoint rows are absent or explicitly missing, retain only the source explanation row and remove the template's endpoint/example rows. They must not be followed by drafting, review, source-file, or data-request commentary.

## 5. Product identity
Current company rule:
- header/title product position = model
- Section 1 `产品名称 / Product name` value remains blank
- CN `中文名称` = Chinese product name + one ASCII space + model
- EN product display name = professional English product name + one ASCII space + model
- footer MSDS identifier = `<MODEL>-MSDS`

Do not make the English product name chemically narrower than the Chinese source supports.

## 6. Continuous numbering
Processing order is mandatory:
`source extraction -> normalized semantic model -> fresh formal-template clone -> semantic mapping -> missing/unsupported suppression -> continuous renumber/order -> approved value-cell writes -> template format-anchor audit -> geometry/semantic audits -> render QA`

Every ordinary section's visible main numbered items must be continuous `N.1, N.2, N.3...` after omission. Unnumbered child rows and H/P lines do not consume main numbers. Sections 11 and 12 retain their standard source-defined endpoint numbers after source-gated omission; their audit requires ordered, non-reappearing endpoint numbers rather than renumbering a canonical endpoint such as 11.7. Adjacent repeated numbers are allowed for subrows belonging to one main item, especially Section 11 acute-toxicity routes.

For Section 9, this continuity rule is applied after whole-row removal of pure missing-data properties; the final visible list must contain no pure `无数据` / `No data available` property row.

Preserve source semantic order within repeated subitems. Audit by unique main item number, not Python wrapper object IDs.

## 7. Chinese language layer
Chinese output retains the established professional Chinese wording from the approved template/source mapping. Do not rewrite labels casually. Ordinary body prose may use semantic line breaks after Chinese full stops/semicolons when helpful, but Section 2 H/P and Section 11 have higher-priority structural rules.

## 8. Professional English language layer
English must read like a professionally authored SDS, not literal Chinese word order.

Canonical section headings:
1. Identification
2. Hazard(s) identification
3. Composition/information on ingredients
4. First-aid measures
5. Fire-fighting measures
6. Accidental release measures
7. Handling and storage
8. Exposure controls/personal protection
9. Physical and chemical properties
10. Stability and reactivity
11. Toxicological information
12. Ecological information
13. Disposal considerations
14. Transport information
15. Regulatory information
16. Other information

Use `resources/professional_translation_glossary.tsv`, `resources/section_translation_rules.md`, and `resources/structured_toxicology_translation.md` as the canonical translation layer.

Translate meaning, not Chinese syntax. Preserve qualifiers (`approximately`, `>`, `<`, similar-product evidence), standards and uncertainty. Do not silently upgrade evidence.

## 9. Section 2
Use professional GHS terms: `GHS classification`, `Label elements`, `Pictogram(s)`, `Signal word`, `Hazard statement(s)`, `Precautionary statement(s)`, `Physical and chemical hazards`, `Health hazards`, `Environmental hazards`, `Other hazards`.

If the source contains H/EUH/P codes, keep each complete coded statement on its own logical line and use canonical English wording when supported. Never invent codes from prose.

Section 2 is customer-facing and must be self-contained:

- If the source DOCX contains a GHS pictogram image, extract and insert that image into the cloned template's existing GHS pictogram cell. Preserve the image as an image; do not replace it with `无数据`, `None`, alt text or a textual description. If no image is supplied, resolve a pictogram only from explicit verified GHS classifications and record the resolution in the audit; never infer from vague prose.
- The CN Section 2 source heading `2.2 标签要素` is projected as `2.2  标签要素：`; the source-backed other-hazards heading is projected as `2.3  其他危害：` after omission and renumbering. The English baseline keeps its approved English label. The `GHS label elements` value cell must contain explicit, line-separated label tips. For example: `必须列在标签上的有害成分：` followed by `亲水脂肪族聚异氰酸酯` on the next line. The English equivalent is `Hazardous ingredients required to be listed on the label:` followed by the ingredient on the next line. With no verified label ingredients the value stays empty and the existing missing-row suppression removes the whole row; never leave the bare heading.
- Never output `见2.4-2.6`, `See 2.4-2.6`, or any customer-facing cross-reference. Signal word, hazard statements and precautionary statements remain directly visible in their own rows.
- After Section 2 values and pictograms are written, remove a whole dedicated row whose value is only `无数据` / `No data available`, including `眼睛：无数据` / `Eyes: No data available`, and renumber surviving unique `2.x` items in original order. Keep substantive negatives such as `无刺激`, `不适用` and `无危险反应`; repeated child rows retain one shared number. The unnumbered pictogram row remains when an image is present.
- `2.3 其他危险` is a source-backed endpoint. If the source explicitly contains it with `无适用资料` (or an equivalent explicit conclusion), keep the row and include it in continuous numbering; only an absent source endpoint is hidden.

Read `resources/section2_ghs_policy.md` and use `scripts/section2_ghs_policy.py` plus `scripts/ghs_pictogram_policy.py` for this policy.

## 10. Section 8
Map source semantics to existing PPE/control labels. Professional EN terms include `Control parameters`, `Exposure controls`, `Respiratory protection`, `Hand protection`, `Eye/face protection`, `Skin and body protection`, `protective gloves`, `breakthrough time`, and `glove thickness`.

Do not create composite labels that do not exist in the template. Preserve standards such as EN 374 exactly. When a source row is formatted as `氟化橡胶 –FKM:厚度...`, `丁基橡胶 –IIR:厚度...` or `丁腈橡胶 –NBR:厚度...`, split it into the existing material label cell and its value cell; never leave the value cell empty. Keep `8.2 工程控制` separate from the workplace-component control-parameter block. An absent workplace-component block is hidden, not rendered as `无数据`.

The source `8.1 控制参数` exposure-limit/control-parameter statement maps to the existing template row `8.2 工程控制：`; the source `8.2 暴露控制` PPE rows map to the template's `8.1 暴露控制` block. This is semantic mapping, not positional copying. The template `建议：` row keeps its fixed label but its value stays blank. Synthetic spaced separators such as ` / ` become semantic line breaks before writing; compact source expressions such as `通风/排气` and `有/无` remain unchanged. A value line containing only `/` or `／` is a release blocker.

## 11. Section 11: structured toxicology is highest priority
**Never use punctuation-first splitting for Section 11.**

Parse hierarchy first:
`endpoint -> study/test block -> structured field -> value`

Structured fields include:
- Test type
- Test material/substance
- Route of exposure
- Species
- Test atmosphere
- Dose / LD50 / LC50
- Metabolic activation
- Result
- Assessment
- Classification
- Method/guideline
- Evidence qualifier / similar-product study

Rules:
- `Species: Rabbit` is one logical line. Never split `Species:` from `Rabbit`.
- Multiple studies under one endpoint remain separate blocks.
- Buehler and LLNA are separate studies.
- Ames and in-vitro chromosome aberration are separate studies.
- Do not merge oral/dermal/inhalation acute toxicity.
- Preserve source route order where the template supports it.
- A simple conclusion such as `STOT assessment - single exposure: Based on available data, the classification criteria are not met.` may remain one field:value line; do not over-split it.
- When the source explicitly supplies a missing endpoint value, retain that endpoint row and write the exact missing-data placeholder. When the source has no endpoint field at all, suppress the template-only row; if every endpoint in Section 11 or 12 is absent or explicitly missing, retain only the source explanation row.
- Section 11.7 is an exact endpoint projection: `生育力`, `致畸形` and `体外遗传毒性` may only be populated from their matching source fields. An explicit source phrase such as `无数据资料` is retained for the matching endpoint; an unmatched or blank child row is hidden. Do not move `体外遗传毒性` study data into a blank reproductive-toxicity child row.
- Section 11 is source-field projection, not a reasoning step. Write only endpoint values, species, results, classifications, methods or evidence qualifiers explicitly present in the verified source/semantic payload. Do not add a method, species, classification, “similar product” qualifier, overall assessment or additional-information conclusion merely because a neighboring field exists in the template.
- The verified alias policy maps source `主要粘膜刺激性` to the existing standard endpoint `11.3 主要眼睛刺激性`; this is controlled field classification, not a new label or an inference. Preserve the source result/value exactly and do not duplicate it into `11.10 附加信息`.
- For study results, use direct source-grounded field lines in the value cell, such as material/substance, species, result, classification, method/guideline and the supported evidence qualifier `对类似产品的研究` / `Study of a similar product`.
- For acute dermal and acute inhalation conclusions, preserve the source's direct assessment wording; do not replace it with a missing-source explanation or an invented LD50/LC50.
- Never output the labels `原发性皮肤刺激` or `Primary skin irritation` when the source provides the structured study result; use the structured study block instead.

Use `scripts/structured_toxicology_policy.py` and the resource guide. Section 11 rules override `scripts/sentence_boundary_policy.py`.

## 12. Ordinary line-break policy
For ordinary body prose outside higher-priority structured sections, Chinese `。`, Chinese `；`, and ASCII `;` can be semantic boundaries. Keep punctuation on the preceding line. Do not auto-split ASCII period because of decimals, abbreviations, units, identifiers and URLs.

Use Word line breaks inside the same logical paragraph/item; do not create blank paragraphs, tabs or repeated spaces to fake layout.

## 13. Sections 12-14
Translate/mapping endpoint-by-endpoint, not as a prose blob.
- Section 12: professional ecotoxicology terminology; preserve OECD methods and evidence qualifiers. A source `生态毒性` endpoint must populate the existing `12.1 生态毒性` row; it must never be consumed by the template's leading explanatory-note rows. Those note rows are blank unless the source contains the matching explanation.
- Section 12 explanatory rows are source-presence controlled. If a note such as `以下为类似产品的生态毒理学参考数据：` is not present in the source, remove the template-only row; do not insert explanatory prose from the template.
- Section 13: compact professional disposal wording grounded in source.
- Section 14: professional road/rail, sea, air and special-precaution wording; use ADR/RID/IMDG/IATA only where supported.
- Section 14 transport fields must be line-separated within the value cell: UN number, proper shipping name, hazard class, packing group and special precautions each occupy their own logical line. Semicolon-packed transport strings and provenance phrases such as `按源文件列示` are prohibited.
- Section 15 keeps only source-backed regulation rows and removes trailing blank rows; an empty template row is not a legal requirement.

## 14. Company overlays
Build content once per language, then apply company overlay.

### Guanzhi
Chinese legal name: `广州冠志新材料科技有限公司`
English display translation default: `Guangzhou Guanzhi New Materials Technology Co., Ltd.`
Address/telephone/fax must come from the authoritative source/template for the current task.

### Guocai
Chinese legal name: `英德市国彩精细化工有限公司`
English display translation default: `Yingde Guocai Fine Chemical Co., Ltd.`
Address: `广东省英德市白沙镇太平村更古坑凯迪工业园区`
English address display default: `Kaidi Industrial Park, Genggukeng, Taiping Village, Baisha Town, Yingde, Guangdong, China`
Telephone: `86-763-2811205`
Fax: `86-763-2811024`

English company names above are controlled display translations, not claims of registered English legal names. If the user supplies official registered English names/addresses, those supersede defaults immediately.

Within the same language, differences between Guanzhi and Guocai are allowed only for:
`supplier_name, supplier_address, telephone, fax, footer_company`.
Any product/safety-content difference is release-blocking.

## 15. Four-format synchronization contract
All four outputs must trace to one normalized fact model.

Cross-language parity means facts, numbers, qualifiers, routes, test methods, CAS, concentrations and classifications must match semantically. Translation wording may differ by language; facts may not.

Cross-company parity means content within each language must be identical except the company whitelist.

Use `scripts/output_matrix.py` and `scripts/four_variant_policy.py`.

## 16. Mandatory QA / release blockers
The QA commands are mandatory gates, not advisory checks. A non-zero exit status from any applicable audit blocks release.
Before delivery run, as applicable:
- missing-data suppression audit
- Section 9 whole-row omission and continuous-renumbering audit
- continuous numbering audit
- locked-label/geometry audit
- whitespace audit
- Section 2 H/P layout audit
- Section 11 structured-field/study audit
- English terminology audit
- CN/EN semantic parity check for all factual values
- Guanzhi/Guocai whitelist-only difference check
- footer/header/product identity audit

Then render **every produced DOCX** with `/home/oai/skills/docx/render_docx.py` and visually inspect **every page at 100%**. Fix and rerender until clean.

Release blockers include:
- visible pure missing-data placeholders
- numbering gaps
- Section 11 merged studies or broken field:value pairs
- route/order mapping errors
- literal/awkward banned English
- cross-language factual drift
- cross-company product/safety differences
- broken table geometry, clipping, overlap, excessive blank space or footer errors

## 17. Output mode
Default: `ALL` = four files.
Optional user-selected modes:
- `CN` = two Chinese company files
- `EN` = two English company files

Canonical filenames are generated by `scripts/output_matrix.py`.


## 17A. PDF publication layer (mandatory for eight-file output)
PDF is a publication derivative, not a fifth content branch. The only permitted path is:
`final audited DOCX -> deterministic conversion adapter -> PDF preflight -> full-page render QA`.

Hard rules:
- One-to-one basename parity between every DOCX and PDF.
- PDF content must not be separately translated, edited, reflowed, redrawn, or regenerated with ReportLab.
- Convert only after the corresponding DOCX passes all semantic, geometry, numbering, company, identity, header/footer, and terminology audits.
- Use the bundled `scripts/convert_docx_to_pdf.py` adapter for one-to-one DOCX-to-PDF publication. It uses the host's native WPS/Word-compatible `word2pdf` exporter, temporary output and atomic target replacement. Read `docs/pdf_converter_adoption.md` before changing the converter.
- The adapter must receive the exact final audited DOCX, write the same-basename PDF, and record source/target SHA-256, converter version, page count and elapsed time in an evidence JSON file.
- If the host has no WPS/Word-compatible CLI converter, fail closed and do not silently switch to LibreOffice, ReportLab, PDF redrawing or another unverified PDF authoring path. A different renderer requires an explicitly tested layout baseline and a separately approved Skill change.
- Render every final PDF with `/home/oai/skills/pdfs/scripts/render_pdf.py` and inspect every page.
- Release blockers: conversion failure, zero-byte PDF, broken/missing glyphs, clipping, overlap, broken tables, missing header/footer, page-number failure, or material visual divergence from the corresponding DOCX render.
- PDF page count MUST equal the rendered page count of its corresponding DOCX. Different language/company variants may naturally have different page counts.
- PDF metadata/producer differences are not semantic differences and do not authorize content drift.
- Never treat PDF extraction order as a substitute for visual QA.

Eight-file release gate:
1. four DOCX release audit passes;
2. four DOCX full-page render QA passes;
3. four PDFs are converted from those exact final DOCX files;
4. four PDFs pass preflight and full-page render QA;
5. basename matrix is complete: 4 DOCX + 4 PDF;
6. any failure blocks the entire eight-file release unless the user explicitly requested a partial format scope.

## 17B. CN exact-template layout (mandatory for CN outputs)
The bundled formal CN template is the sole Word layout authority. After
content is written, preserve its table geometry, row heights, cell properties,
paragraph properties, run properties, header/footer structure and page fields.

- Do not run `compact_cn_layout.py`, `compact_cn_document()` or any global
  font/spacing/indent normalization in the active overwrite pipeline.
- Empty or unsupported content is handled only by the documented source-
  presence policy and the smallest allowed whole-row/block suppression; do
  not compensate by changing neighboring row heights, paragraph spacing or
  page breaks.
- Footer text may be replaced in the existing footer value cells, but footer
  paragraph and table formatting remains inherited from the fresh template.
- Run the template format-anchor audit after every CN build. It must prove
  that every surviving row/cell and every header/footer cell retains the
  fresh-cloned template's formatting anchor. Any unapproved formatting change
  blocks the output before overwrite.
- Rendered-page readability remains mandatory, but a readable PDF cannot
  override a failed exact-template audit.

## 17C. EN output-layout compatibility (mandatory for EN outputs)
The supplied EN template is the sole source of the English table/section
layout. After EN content and company overlay are written, run
`scripts/normalize_en_layout.py` through its `normalize_en_document()` entry
point with the active EN template path only to re-assert value-cell paragraph
and run properties from that same template. This is a controlled format sync;
it must not normalize EN to CN, add rows, or redesign labels/geometry.

- The production pass does not rebuild tables, change row/column counts, grid
  widths, merges, borders or facts. It restores paragraph and run properties
  from the maintained EN template after text replacement. A global font/size
  reset is not permitted because it breaks template text-format parity. Keep
  Section 11 sublabels (`Oral`, `Inhalation`, `Dermal`, `Fertility`,
  `Teratogenicity` and `In vitro genotoxicity`) in their approved template
  cells. These six Section 11 route/sublabel fields are the latest EN template
  labels: `Oral:`, `Inhalation:`, `Dermal:`, `Fertility:`, `Teratogenicity:`
  and `In vitro genotoxicity:`.
- The EN locked-label audit must be run with `--language en`; it permits only
  the documented EN paragraph-layout normalization while continuing to check
  the ordered label anchors, table/cell positions and run properties.
- The EN footer intentionally uses two lines for the company name and the
  model-based MSDS identifier so a hyphenated model identifier cannot be split
  into a dangling `MSDS` token. This is a controlled footer policy, not a
  content change.
- Any EN output with duplicate automatic numbering, broken Section 11 labels,
  excessive word gaps, clipping, overlap or a material divergence from the EN
  maintained baseline is a release blocker.
- EN body value paragraphs and runs must pass a template-format parity audit;
  an output that is semantically correct but uses a different paragraph/run
  format from the active EN template is blocked.

## 18. Maintenance rule
This is the only maintained skill. When a rule changes (for example Section 11, omission, numbering, template geometry, company profile, CN layout compatibility or PDF conversion), record the user's observed failure as a regression case, update the shared semantic policy once, and add tests that cover both languages and both companies. A release is not complete until the same real input is replayed through the complete DOCX-first pipeline and the feedback case is demonstrably closed. Do not fork separate CN/EN skills again.

## 19. Deliverable evaluation and audit evidence (mandatory)

Before a customer delivery, run `scripts/audit_deliverable_package.py` against
the complete eight-file package. This audit layer is additive to every prior
release gate and does not replace the source-grounded semantic pipeline,
template geometry audit, mutation whitelist, V2.9 inheritance audit or
page-by-page QA.

- Use the fixed 100-point model in `docs/deliverable_evaluation_standard.md`.
- Apply the stable-ID checklist in `docs/deliverable_audit_checklist.md`.
- Treat `B0` and `B1` as non-overridable blockers; `B2` must remain visible in
  the evidence report even when it does not block release.
- A missing, duplicate, unparsed or untested rule is not a pass. The final
  decision must be `NOT_READY` or `RELEASE_FAIL` until evidence is complete.
- JSON and TXT audit reports are release evidence. Every record must identify
  its source of truth, method, pass condition, observed result and evidence
  path as defined in `docs/audit_evidence_schema.md`.
- A score of 95/100 is necessary but not sufficient: `RELEASE_PASS` also
  requires zero B0/B1 blockers and complete evidence.

## 20. Parameterized workflow (mechanical/agent split)

The overwrite core is extract -> standardize (CN) -> render CN -> translate
EN from the standardized model. Labor splits as follows:

- Mechanical (deterministic, no judgment): file I/O, template clone, value-cell
  writes, S2/S9 suppression and renumbering, pictogram insertion,
  header/footer stamping, PDF conversion, audit execution, S1 supplier block,
  S3 transcription, S9 ordering, verbatim standard codes. Run
  `scripts/extract_source_facts.py` for a positioned draft (every candidate
  carries table/row/cell provenance; unmapped cells block the build).
- Agent judgment (never scripted in batch): source-fact verification, S2
  classification, S11 endpoint mapping and aliases, H/P wording, EN
  professional translation (qualifiers and evidence levels preserved),
  sensitization study separation, missing-vs-`不适用`, company overlay,
  cross-language parity, visual QA. Record each call as an `AGENT_DECISION`
  with its source basis; a wrong call is traceable, never a template to
  memorize. Batch regex matching of semantics is forbidden: the extractor
  proposes candidates with provenance, the agent disposes.

One command replaces the per-model copied generators for new models:

`python scripts/build_eight.py --source SRC.[docx|doc|odt|rtf|xlsx|xls|txt] --facts MODEL.json --out DIR`

The approved facts file holds the standardized `zh` model, the reviewed EN
translation of that same model (`translation_review` must be empty),
`source_sha256`, `s8_control_parameters`, and a reviewed `source_mapping`.
`source_mapping` must bind the same model and original-source SHA, cover all
S1-S16 sections, list unique source locators and source text, and explicitly
dispose each candidate as `mapped`, `omitted` (with a reason), or
`not_applicable` (with a reason). `status=needs-review`, any unresolved item,
an unclassified target, or a missing section blocks the build. This is the
anti-omission/anti-invention evidence contract; it does not authorize an
agent to invent facts. Any gate failure raises `ReleaseBlocked` before a
formal output is promoted. Legacy `_task_work`
generators are frozen regression vehicles and are not production entry points.

## 20A. Source discovery, compatibility and non-bypassable gates

- Use `scripts/source_ingest.py` for source selection. `--source-dir` must
  resolve to exactly one supported candidate after model filtering; multiple
  candidates require an explicit `--source` path. Lock files and formal
  `*_MSDS_(CN|EN)_(冠志|国彩)` outputs are never discovery candidates, and a
  formal output cannot be passed as the source. Generated/output directories
  (`覆写产出`, `output(s)`, `artifacts`, `_task_work`) are also blocked even
  when a generated file is renamed.
- The source registry currently recognizes `.docx`, `.docm`, `.doc`, `.odt`,
  `.rtf`, `.xlsx`, `.xls` and `.txt`. Direct section extraction is approved
  for DOCX/DOCM; DOC/ODT/RTF use a temporary LibreOffice DOCX adapter.
  Spreadsheet/text sources are provenance-aware but do not guess a 16-section
  model: `extract_source_facts.py` blocks until a dedicated coordinate/semantic
  adapter is approved. PDF is publication-only and is never a source input. A
  format adapter must preserve the original path and SHA-256; temporary
  conversions never become formal sources.
- `build_matrix` validates the original source SHA-256, model, all 16 sections,
  both language layers, the canonical 15-slot Section 2 projection and the
  reviewed source-mapping manifest before cloning any template. When `--model`
  is supplied to extraction, the parsed source model must also equal it.
  Positional Section 2 payloads, missing provenance, cross-source facts,
  unresolved mapping candidates or unreviewed semantic decisions fail closed.
- The default release is exactly four canonical DOCX and four same-basename
  PDF files from one fact model. All variants are built in a temporary matrix,
  individually gated, converted DOCX-first, checked for PDF evidence/hash
  lineage, and promoted only after the complete matrix passes. `--no-pdf` is
  an explicit DOCX-only test mode, not the default release mode.
- No Agent may translate from a rendered output, use an earlier output as a
  patch base, write a second template, or bypass `scripts/msds_pipeline.py`,
  `scripts/template_mutation_whitelist.py` and the release audits. Unsupported
  formats and ambiguous sources must be reported as blocked, never silently
  approximated.

## 20B. Performance-safe execution

- A matrix run loads each maintained language template once and reuses those
  immutable documents for normalization and locked-format audits.
- After each staged DOCX is saved, the in-memory document is reused across the
  content, whitespace, numbering and cross-page checks; the saved file remains
  the conversion input and final evidence source.
- DOCX variants may share read-only template state; PDF conversion remains
  ordered so office-process locks and page layout stay deterministic.
- Performance work must remove duplicate parsing or redundant computation while
  preserving every release gate. A faster run with fewer audits is invalid.
