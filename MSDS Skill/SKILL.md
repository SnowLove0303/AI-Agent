---
name: msds-unified-four-format-standardizer
description: One maintained MSDS/SDS standardization skill that discovers supported source files, binds source-grounded facts to synchronized CN/EN outputs for Guangzhou Guanzhi and Yingde Guocai, preserves locked templates, and releases four DOCX plus four PDF deliverables only after semantic and render QA.
---

# Unified MSDS Eight-Deliverable Standardizer v3.27.5

## Global Source Fidelity and Layered Section Rules (v3.27.5)

1. The global source-grounding gate is shared by S1-S16. `output_traceability`
   records output decisions but never becomes evidence by itself.
2. Chinese values are source-verbatim by default after semantic field routing
   and line-break/structure normalization. English values may be translated
   only with a bound source fact and explicit reviewed-translation evidence.
3. Local Section rules refine matching and omission only; they cannot weaken
   template immutability, value typography, source evidence or the single
   guarded writer.
4. Flexible source handling normalizes section names, numbering, labels,
   tables, nested tables and line breaks without paraphrasing source facts.

## Mandatory EN Master Template & Format/Bold Immutable Lock (v3.27.4)

1. The user-tuned 16-table English master template (examples/template_reference_en.docx) is the immutable baseline for all English MSDS generation.
2. Section 8 (Table 7) standard geometry is 16 rows ([9, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2]).
3. Bold runs (325 runs across 16 tables) and paragraph formatting are strictly locked. Value cells inherit typography without mutating labels or modifying bold status.
4. Output must strictly converge to 7 pages without 8th blank overflow page, and enforce a 0 Chinese characters gate.


## Mandatory Jev System One Adjudication and Decision Ledger (v3.26.6)

1. `MSDS Skill/scripts/jev_engine.py` and `jev_domain_adjudicator.py` must be used for all ambiguous GHS classifications, cross-section fact routing, independent row necessity, TDS parameter slot mapping, and semantic consistency pre-release audits.
2. Fast-path deterministic rules handle explicit, unambiguous text in 0ms; Jev System One is invoked on-demand when ambiguity or cross-section conflicts arise.
3. All Jev decisions must be recorded in `GLOBAL_LEDGER` and exported to `jev_decision_ledger.json` for full auditability.


## Mandatory Verbatim Section 2, Unified Value Typography, and Independent Row Playbook (v3.26.5)

1. `set_cell_value_unified` and the shared value writer must enforce 12.0 pt (`<w:sz w:val="24"/>`), Times New Roman for EN values, 宋体 for CN values, left paragraph alignment, centered cell vertical alignment, single run per line where the writer owns the full value cell, and zero dangling empty paragraphs.
2. Section 2.2 GHS Label Elements must preserve verbatim source text (e.g. `羟基丙烯酸酯聚合物GHS危险性分类：不适用\n请注意以下物质：\nN,N-二甲基乙醇胺，中和剂，已键合为盐，质量浓度小于2.0%`).
3. Follow `docs/independent_row_playbook.md` strictly: product-level study conclusions and polymer component data must NEVER be congested together; they must occupy distinct independent rows/paragraphs.


## Mandatory GHS code reverse-resolution and Jev dispatcher routing (v3.26.4)

When source MSDS assets contain natural language hazard, precautionary, storage or disposal statements without alphanumeric codes, agents must NOT delete them or leave rows blank.
1. `scripts/ghs_code_resolver.py` reverse-resolves statements against canonical GHS rules into standard P-codes (`P280`, `P264`, `P270`, `P271`, `P304+P340`, `P305+P351+P338`, `P302+P352`, `P301+P330+P331`, `P391`, `P370+P378`, `P403+P235`, `P501`) and groups them into standard 4-block headings (预防措施, 事故响应, 安全储存, 废弃处置).
2. `scripts/jev_dispatcher.py` handles intelligent GHS Signal Word mapping (e.g. `警告词：警告` -> `警告` / `Warning`) and routes Section 3 amine neutralization / SCL threshold notes into Section 2.3 GHS Label Elements.
3. Section 11 must provide transparent multi-tier toxicological reporting, explicitly declaring polymer absence of data and identifying reference components by name and CAS number.



## Mandatory v2.9 inheritance (release blocker)

This unified skill is an additive superset of `MSDS_Word_Standardizer_Skill_v2.9`. **All v2.9 overwrite content, programs, requirements, fixtures, and QA behavior remain binding.** Read `docs/v2_9_inheritance_contract.md`. Before release, `scripts/audit_v29_inheritance.py` MUST pass against the canonical v2.9 ZIP. Section 11 structured-toxicology handling is an enhancement layer; it must not delete unrelated v2.9 behavior.

## Mandatory OpenSpec agent execution gate (release blocker)

Before any source inspection, semantic decision or DOCX mutation, read the
complete `openspec/agent_overwrite_contract.md` and every file listed in its
`read_before_action` list. The approved facts JSON MUST contain a reviewed
`agent_execution` record with the active OpenSpec ID/version, full read-source
list, every acknowledgement set to `true`, the exact prescribed operation
order, the exact Agent mutation boundary and the declared
fresh-clone/value-cell-only/fail-closed execution mode.
`scripts/agent_execution_contract.py` validates this record before a template
is cloned; a missing, partial or stale record blocks the build. This record is
an execution gate, not a substitute for the DOCX audits.

The machine-readable contract is `openspec/agent_overwrite_contract.json`.
The final output gate is `scripts/audit_openspec_overwrite.py`, which combines
the existing locked-skeleton/format/cross-page audits with hard checks for
empty value rows, blank paragraphs, artificial spacing and post-omission
numbering.

## Mandatory source interpretation and traceability gate (release blocker)

The Agent must not jump directly from source prose to a template value. Read
`openspec/source_interpretation_contract.md` and use
`docs/source_interpretation_playbook.md` for the complete source-reading,
evidence, mapping,取舍 and overwrite procedure. Before a template is cloned,
the approved facts JSON must contain all five records below:

- `source_coverage`: source-unit inventory with the matching source hash,
  counts, processed images/tables and empty `unmapped`/`unreadable` lists;
- `fact_ledger`: a stable-ID record for every extracted fact with an exact
  source locator, source text, source-unit IDs and evidence type;
- `source_mapping`: a reviewed disposition for every fact and every S1-S16
  section; and
- `output_traceability`: a reviewed record connecting every written, merged,
  hidden or not-written target to source facts, an approved derivation or an
  explicit absence decision;
- `section2_routing`: a reviewed stable semantic route for every mapped Section
  2 fact, with exclusive-by-default usage and explicit shared exceptions.

`scripts/source_interpretation_contract.py` validates this gate. A source
coverage gap, unreadable source region, unresolved/ambiguous/conflicting
mapping, source fact without a disposition, or output value without evidence
blocks the build before any template clone. `source_absent` is distinct from
`source_unreadable`; only a reviewed absence/unsupported decision may trigger
an empty-row action. Meaningful source line breaks must be preserved as Word
line breaks inside existing value cells; blank paragraphs, tabs, repeated
  spaces and slash-only lines are forbidden.

The Section 2 router is a separate pre-clone blocker. It prevents an emergency
overview from being synthesized from H/P statements, physical/chemical hazards,
health hazards or other hazards; prevents one source fact from being mechanically
reused across 2.1/2.5/2.7/2.8/2.10; and checks that CN/EN output traces use the
same semantic destination as the reviewed mapping. Generic positional targets
such as `s2.row[1]` are ambiguous after omission and are rejected.

V3.25.0 adds a second, fail-closed source-grounding check after the reviewed
interpretation gate. `scripts/source_grounding.py` checks every non-empty
semantic value against the original source, reviewed output traceability or a
declared company/translation overlay, and records the result in
`matrix-report.json`. Template example values can therefore never become
  product facts merely because an Agent failed to clear them. Controlled
non-hazard GHS fallback text is permitted only when the source explicitly
classifies the product as non-hazardous. This check does not authorize new
  labels, table cells or layout changes.

V3.25.3 adds route-aware Section 2.8 extraction, semantic Section 8 PPE row
alignment and dedicated output-only layout gates. S8.2 must retain the formal
five-column grid, four logical data cells, `gridSpan`, widths and parent/header
structure when source control records are present; the complete block may be
hidden only when the source has no verified controls. S11.4 cell vertical
alignment must remain identical to the fresh template clone. These gates detect
and block drift; they never repair the formal template or perform global
formatting changes.

V3.26.2 adds the reviewed English product-name gate, active EN template
remediation, bold English health-hazard route-prefix prototypes and the
fail-closed Times New Roman 12 pt EN value-format audit. TDS production is outside this
repository and remains an external follow-up.

V3.26.0 adds a source-hash-bound cache root, reviewed-only family candidates,
one read-only `AuditContext` per saved staged DOCX and additive timing data.
The context only removes duplicate in-memory traversal; persisted package,
lineage and render checks remain independent release gates. Use
`scripts/benchmark_efficiency.py` for non-publishing cold/warm and worker
comparisons. No cache hit, benchmark checkpoint or family candidate authorizes
source-free filling, label edits, format edits or a skipped gate.

## Mandatory value typography rule (release blocker)

The template's pre-existing bold content is locked label/sequence/header/
structure content. The maintained English health-hazard route prefixes are
also bold locked template content; only their descriptions are writable.
A writable value can inherit the template value anchor's
font family, size, color, language, spacing and other non-bold properties, but
it MUST never be bold. This applies to ordinary value cells, S3 and S8.2 data
cells, Section 11 final value cells, one-cell S15/S16 note values and Section
2.8 value tails. The shared writer removes or explicitly overrides w:b and
w:bCs on value runs; the release audit classifies value cells by semantic
topology and blocks any non-empty bold value. It does not scan locked labels
as values, and it never changes the official template to achieve this rule.

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

The user-visible matrix is isolated per model: `OUT/MODEL/WORD` contains the
four final DOCX masters, `OUT/MODEL/PDF` contains their four PDF derivatives,
and `OUT/MODEL/matrix-report.json` contains the evidence. Temporary files and
optional preview files are never part of the formal matrix.

This package remains an additive superset of the Chinese v2.9 overwrite core. Maintain one semantic pipeline only.

## 1. Architecture: one truth, two language layers, two company overlays
Use this pipeline:

`全量抽取源文件信息 -> 基于约束的信息归纳 -> 基于固定结构的模板覆写 -> 微调（不显示/重排序等） -> audits -> render QA`

The four stages are a hard business contract, not merely an implementation
description. The active machine-readable and explanatory rules are in
[`openspec/efficiency_contract.json`](openspec/efficiency_contract.json) and
[`openspec/efficiency_contract.md`](openspec/efficiency_contract.md):

1. Extract every source unit, nested table and image into a source-bound
   inventory and fact ledger. Do not mutate a template.
2. Normalize, map, take/omit and derive only under the source and section
   contracts. Review provenance and CN/EN traceability before any DOCX write.
3. Clone the pinned template, resolve a semantic write plan, and overwrite
   approved value cells while preserving all template-owned labels, sequence,
   boldness, formatting and geometry.
4. Apply only authorized empty-row suppression, source-backed styled-row
   insertion, merge repair and prefix-only renumbering; then run all audits.

`scripts/efficiency_contract.py` validates this contract and records low-cost
stage timings. A fast checkpoint or timing record is diagnostic evidence only;
it cannot replace the final release gates.

Hard rules:
- **Source MSDS controls product facts.**
- **Bundled latest approved template controls Word geometry.**
- **Language layer controls professional wording, never facts.**
- **Company overlay controls only approved company-profile fields.**
- Never maintain four independent content copies.
- Never translate from the already-rendered CN output to make EN. Both CN and EN must derive from the same normalized source facts, preventing semantic drift.

## 2. Template authority
The language-specific template baselines are authoritative:

- CN source record: `examples/template_reference_cn_source.docx`, an unchanged copy of the user-supplied formal `正式模板_MSDS_CN_冠志.docx`.
- CN active baseline: `examples/template_reference.docx`, the current user-approved formal CN template installed byte-for-byte.
- EN source record: `examples/template_reference_en_source.docx`, an unchanged copy of the user-supplied formal `正式模板_MSDS_EN_冠志(1).docx`.
- EN active baseline: `examples/template_reference_en.docx`, a value-cell-only normalization of the supplied EN source; labels, bold runs and table geometry remain unchanged.
- Historical template copies are deliberately not shipped. Only the current
  user-approved CN/EN baselines and their unchanged source records are part of
  the active package; rollback copies belong outside the distributable skill.

Pinned SHA-256:

- CN active baseline: `a69a447f7f39599b10c30c7f92c4d5101d94fd85bfdcc4d89de429d1c796af1c`
- EN source: `0c7f3bfd74a85955a32fd691a392077f79c0acc74d2c7765947e02cf7c226c3f`
- EN active baseline: `dca8a1a5940f4410003b032d9ec914291c1e961383305af271ba3cd6b32e495f`.

Structural baseline:
- 16 tables
- CN row counts: `[10,16,6,6,5,4,3,16,24,6,18,6,3,5,9,2]`
- EN row counts: `[9,16,6,6,5,4,3,16,24,6,18,6,3,5,9,2]`
- CN and EN are intentionally different physical templates. Shared semantic content and overwrite rules do not require identical physical row counts or label wording.
- Section 11 current multi-column/merged-cell geometry is locked.
- Section 2.8 health-hazard route prefixes are English, bold, and locked
  template content; their value tails are ordinary Times New Roman 12 pt. Section
  11.1/11.7 middle sublabels and every other bold template label/run are also
  locked template content. The physical three-cell
  Section 3 rows and four-cell Section 8.2 rows are also locked topology; only
  their declared data cells may receive source values.
- Section 12 current 6-row geometry is locked.
- Section 15 current 9-row geometry is locked.
- Section 2 includes the uploaded template's revised hazard-label structure.
- Section 8 includes the uploaded template's `Hand protection` and `8.2 Engineering controls` slots.
- Section 8.2 uses the formal template's top-level four-column control-parameter rows: a one-cell `工作场所组分控制参数 / Control parameters for workplace components` parent row, one locked header row (CN `物质 / 依据 / 类型 / 数值`; EN `Substance / Basis / Type / Value`), then data rows. Only source-grounded data rows may be written or cloned; the parent row, header wording/topology and grid are locked. The two template example OEL rows are illustrative structure only and MUST be cleared. With verified source records they are replaced by source data rows; with no source records the complete workplace-component block is removed, including its parent/header/data rows. Nested source tables are part of the source inventory and must be extracted before the block is judged absent. Never emit a synthetic `无数据` / `No data available` row for an absent workplace-parameter block.
- Section 11 includes the uploaded template's structured rows through `11.10 Additional information`.
- The v3.6.2 template geometry update changes only approved border styling: Section 8 internal PPE boundaries use dotted borders with the adjusted boundary edges around the first exposure-control rows; Section 11 uses dotted boundary edges around its introductory/reference-data transition row. No table count, row count, grid width, merge, paragraph-property or run-property baseline changed.
- The complete structural snapshot, including paragraph/run properties and
  header/footer parts, is pinned only in `tests/template_snapshot.json` and
  `tests/template_snapshot_en.json`. Historical versioned snapshots are not
  shipped and must not be used as template authorities.
- Section 3 component rule: every component occupies exactly one physical data row. Never pack multiple component names, CAS numbers or concentrations into one row separated by line breaks. If the source has more components than the template's initial slots, clone the existing styled component row in place and preserve its OOXML geometry.
- Sections 9 and 15 may be expanded only when verified source rows exceed the
  pinned template capacity. Clone the last styled data/note row in place and
  write the source-backed new row through the dedicated insertion boundary;
  never rebuild the table or alter any existing label.

A newer user-approved template immediately supersedes this one. Do not restore geometry or paragraph formatting from older outputs. Text visible in the template (including PEA-4139, example ingredients, hazards, toxicology and ecology values, and the two 8.2 example OEL rows) is illustrative structure only and MUST NOT become product facts.


## 2A. Highest-priority in-place overwrite contract
This rule overrides every language/layout convenience rule. Each CN deliverable MUST be created by cloning `examples/template_reference.docx`; each EN deliverable MUST be created by cloning the independent `examples/template_reference_en.docx`; all four are then mutated in place. Never create an EN document from a blank document, from a rebuilt table set, or from a rendered CN output. Never add a CN-only row to the EN template merely to equalize section capacity.

The maintained EN health-hazard route prefixes are bold template-owned content
(`Inhalation:`, `Ingestion:`, `Skin:`, `Eyes:`, `Signs and symptoms:`).
Only the descriptive tail after such a prefix is a writable regular Times New Roman 12
pt value. Runtime Agents may not translate, restyle or replace these prefixes.

The template owns: table count/order, row/column geometry, grid, merges, cell properties, borders, widths, section placement, label cells, paragraph properties, character-format anchors, and page-crossing behavior. All maintained formal templates permit their tables to continue across pages; each active baseline's row-level `cantSplit` settings are also template-owned and must be preserved exactly on surviving output rows. The source owns facts only. Agent mutation is restricted to writing or clearing label-associated value cells, deciding whether a value is source-absent/unsupported and therefore hidden, and requesting only necessary complete styled-row insertion or deletion under the section rule. Labels, sequence text, boldness, fonts, paragraph properties, cell properties, tables and page layout are never Agent-editable. A bold label/run is a hard lock, but non-bold template-owned prefixes and sublabels are hard locks as well. In particular, S2.8 route prefixes (`吸入：`, `食入：`, `皮肤：`, `眼睛：`, `症状和体征：`, or the exact maintained EN equivalent) remain in the same template run tree; the value tail is appended after the prefix without rewriting it. The previous Section 2 label-alias path is retired; source headings select semantic slots but never rewrite template labels.

The shared runtime builds a slot registry from the fresh clone before clearing values: a non-empty template value object is writable, an intentionally blank object is not writable unless the semantic contract explicitly marks it as an input slot, and Section 8.2 data rows are handled only by their dedicated writer. Section 8 `建议 / Recommendation` is an explicitly source-gated ordinary value slot: substantive source text is retained in the non-bold value cell, while an absent source value remains empty under the source-presence policy. Section 11.1 route sublabels and Section 11.7 child sublabels are locked and are never cleared as value cells. Before any Section 11 write, the runtime maps facts to the fixed endpoint skeleton by endpoint and sublabel, pads absent slots, and only then applies source-presence row omission. This prevents source data from leaking into blank template slots or shifting into a neighboring toxicology label. Any necessary company/header/footer overlay, pictogram insertion or post-omission numeric-prefix renumbering is runtime-controlled and is not an Agent permission.

Deletion of an unsupported item must use the smallest safe template boundary. It may remove a whole dedicated row when that row is exactly one item; otherwise it must suppress only the unsupported item without damaging supported siblings or merge/grid integrity. After suppression, all four variants MUST have the same semantic item-presence set.

**Release blocker:** if any output cannot prove lineage from the pinned template snapshot or fails geometry equivalence after allowed row suppression, do not deliver it. The active CN, EN and EN-source template files are byte-pinned; a changed baseline hash blocks the run before any clone is made. A template is not replaceable by a prior output, a rendered PDF or an unapproved copy.

## 3. Locked-format contract
Bold template labels and table geometry are locked: wording for the selected language, punctuation, run formatting, paragraph formatting, merges, widths, borders and row structure must not be casually rebuilt.

Allowed mutation exception: after an explicitly permitted whole-row omission, numeric prefixes may be changed to restore continuous visible section numbering. Only the numeric prefix is mutable. The complete executable boundary is defined in `docs/template_mutation_whitelist.md` and enforced by `scripts/template_mutation_whitelist.py` plus `scripts/audit_template_mutation_whitelist.py`.

Avoid destructive APIs such as `paragraph.text = ...` or `cell.text = ...` on formatted template content when they would destroy runs. Preserve the template's table-cross-page contract: tables may span pages, and all surviving rows must retain the active template's exact row-level `cantSplit` and repeating-header settings. Never insert artificial page breaks to compensate for content. Preserve the formal footer's leading `P` clipping guard when stamping the revision date; if no date is provided, use the build date and format CN as `YYYY年M月D日` and EN as `Month D, YYYY`, never a stale test date.

The executable per-section contract is maintained in
`scripts/section_overwrite_rules.py`. Every S1-S16 table must use its declared
semantic writer, value scope, empty-value policy and structural-mutation
boundary; an unregistered or positional payload is a release blocker.

Do not infer a field match from row position alone. The approved source mapping
must identify the target section and target slot for every mapped source item;
an absent, duplicate or ambiguous target slot blocks the build before any value
is written.

For inserted non-bold Chinese body text, retain the approved body-character-format convention from the existing baseline. For English, preserve the same template geometry and use a compatible professional body-text run format; allow natural English wrapping rather than fake alignment.

### 3A. Agent mutation whitelist

The sequence column and label column are immutable. The Agent may request only
the following semantic operations; the runtime performs them through the
approved write boundary:

- write source-grounded content to an existing label-associated value cell;
- clear a value cell when the source value is absent or unsupported;
- suppress a complete empty/unsupported dedicated row before numbering;
- insert a complete source-backed styled data row only where the section rule permits it (S3 components, S8.2 control records, S9 properties or S15 regulations).

For composite or multi-column rows, the writable target is the final value
cell only. The S2.8 route prefix (Chinese in CN; the maintained English
equivalent in EN) and the S11.1/S11.7 middle sublabel are
template-owned text, even when they are physically adjacent to or share a
row with the value. A two-column S2.8 cell is therefore split semantically as
`locked route prefix + writable value tail`; clearing it removes only the tail
and leaves the prefix. A three-column row is never collapsed into two columns,
and a four-column S8.2 data row is never collapsed into a prose field.

The Agent must not directly insert pictograms, rewrite aliases, renumber labels,
edit headers/footers or apply company overlays. Those are deterministic
runtime-controlled operations and remain independently audited.

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

Section 9 property exception: when a property value is only a missing-data placeholder, omit the entire dedicated property row before customer-facing write. Do not leave a blank row. Renumber the surviving visible Section 9 properties continuously in original semantic order. The runtime preserves the template's five-character `9.n` prefix slot, so a moved two-digit row receives two separator spaces when it becomes a one-digit item. A source-backed `NCO含量 / NCO content` is an independent Section 9 property row, never text buried in `其他信息 / Other information`. Preserve substantive values, including `不适用` / `Not applicable`, measured values and source-supported `其他信息` / `Other information`.

Do not treat `不适用` or substantive negative conclusions as missing data. Keep conclusions such as `非危险品`, `无危险反应`, `初沸点以下无闪点`, or `未满足分类标准` when source-supported.

Section-level explanatory sentences such as `该产品无可用的毒理学研究。` may be substantive context and must be preserved when they introduce supported component/reference data. When all Section 11 or Section 12 endpoint rows are absent or explicitly missing, retain only the source explanation row and remove the template's endpoint/example rows. They must not be followed by drafting, review, source-file, or data-request commentary.

## 5. Product identity
Current company rule:
- header/title product position = model
- CN Section 1 `产品名称` value remains blank by company convention
- CN `中文名称` = Chinese product name + one ASCII space + model
- EN Section 1 `Product name` value = reviewed professional English product name + one ASCII space + model; it is required and cannot be derived from the model, template example or an unreviewed dictionary
- footer MSDS identifier = `<MODEL>-MSDS`

Do not make the English product name chemically narrower than the Chinese source supports.

## 6. Continuous numbering
Processing order is mandatory:
`全量抽取源文件信息 -> 基于约束的信息归纳 -> 基于固定结构的模板覆写 -> 微调（不显示/重排序等） -> template/semantic audits -> render QA`

Semantic mapping,取舍, CN/EN projection and traceability belong to the second
stage. The fixed-template stage first resolves the complete semantic write plan
and then writes approved value cells. Empty-row suppression, authorized row
insertion and prefix-only renumbering belong to the fourth stage, after fixed
writes and before the final audits. This order is also enforced by
`openspec/efficiency_contract.json`; a fast checkpoint must never replace a
final release gate.

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

For precautionary statements, the source group headings `预防措施：` / `事故响应：` /
`安全储存：` / `废弃处置：` and their English equivalents are semantic structure,
not writable template labels. Extract them into ordered groups before projection;
keep each non-empty group heading on its own logical line inside the existing
Section 2.6 value cell, followed by that group's P statements. A group with no
source P statement is an orphan heading and is suppressed together with its
empty content. A source-present group with valid statements must never be
flattened into an ungrouped P list, routed to `other`, marked `duplicate`, or
silently omitted. Inline headings must be split at a verified heading boundary
so a heading is never appended to the preceding P statement. The final audit
checks source order, group presence and CN/EN heading preservation.

Section 2 is customer-facing and must be self-contained:

- If the source DOCX contains a GHS pictogram image, extract and insert that image into the cloned template's existing GHS pictogram cell. Preserve the image as an image; do not replace it with `无数据`, `None`, alt text or a textual description. If no image is supplied, resolve a pictogram only from explicit verified GHS classifications and record the resolution in the audit; never infer from vague prose.
- CN source Section 2 headings select the existing fixed CN semantic slots without rewriting their labels. The English baseline keeps its approved English label. The source `2.2 标签要素` maps to the maintained template's `2.3 GHS标签要素` slot; it is not the signal-word slot. Its value must contain the verified label-ingredient explanation as explicit, line-separated text, for example `必须列在标签上的有害成分：` followed by `基于HDI的亲水脂肪族聚异氰酸酯` on the next line. The English equivalent is `Hazardous ingredients required to be listed on the label:` followed by the ingredient on the next line. The template `2.4 信号词` slot accepts the controlled source vocabulary `危险` / `警告`, `无信号词` / `No signal word`, `无` / `None`, or `Not applicable`; label-ingredient prose and other unresolved free text must never be placed there. With no verified label ingredients the label-elements value stays empty and the existing missing-row suppression removes the whole row; never leave the bare heading. If preceding Section 2 rows are omitted, health-hazard rows may be renumbered from `2.8` to `2.7`; route-prefix handling remains semantic and must preserve the five template-owned prefixes.
- Never output `见2.4-2.6`, `See 2.4-2.6`, or any customer-facing cross-reference. Signal word, hazard statements and precautionary statements remain directly visible in their own rows.
- After Section 2 values and pictograms are written, remove a whole dedicated row whose value is only `无数据` / `No data available`, including `眼睛：无数据` / `Eyes: No data available`, and renumber surviving unique `2.x` items in original order. Keep substantive negatives such as `无刺激`, `不适用` and `无危险反应`; repeated child rows retain one shared number. The unnumbered pictogram row remains when an image is present.
- `2.3 其他危险` is a source-backed endpoint. If the source explicitly contains it with `无适用资料` (or an equivalent explicit conclusion), keep the row and include it in continuous numbering; only an absent source endpoint is hidden.

Each populated Section 2.8 health route is an independent source fact. Map
`inhalation`, `ingestion`, `skin`, `eyes` and `symptoms/signs` by explicit
source meaning and preserve each route's provenance. Never copy an overall
GHS conclusion such as `未被分类` / `Not classified` into a route row. If a
route is absent or contains only a missing-data sentinel, leave that route's
value empty so the complete row is removed before visible renumbering; later
route values must never move into the empty route's label.

Read `resources/section2_ghs_policy.md` and use `scripts/section2_ghs_policy.py` plus `scripts/ghs_pictogram_policy.py` for this policy.

## 10. Section 8
Map source semantics to existing PPE/control labels. Professional EN terms include `Control parameters`, `Exposure controls`, `Respiratory protection`, `Hand protection`, `Eye/face protection`, `Skin and body protection`, `protective gloves`, `breakthrough time`, and `glove thickness`.

Do not create composite labels that do not exist in the template. Preserve standards such as EN 374 exactly. When a source row is formatted as `氟化橡胶 –FKM:厚度...`, `丁基橡胶 –IIR:厚度...` or `丁腈橡胶 –NBR:厚度...`, split it into the existing material label cell and its value cell; never leave the value cell empty. Keep `8.2 工程控制` separate from the workplace-component control-parameter block. An absent workplace-component block is hidden, not rendered as `无数据`.

The source `8.1 控制参数` exposure-limit/control-parameter statement maps to the existing template row `8.2 工程控制：`; the source `8.2 暴露控制` PPE rows map to the template's `8.1 暴露控制` block. This is semantic mapping, not positional copying. First recover each PPE label/value boundary from separate cells, tabs, inline values and meaningful line breaks; then map by the approved labels for respiratory, hand, glove material, FKM, IIR, NBR, recommendation, eye and body protection. A tail accidentally left after a label is reported as contamination and cannot replace the authoritative value cell. An unknown or ambiguous PPE label enters review and blocks formal projection; it is never assigned by row position. If the source stores `工作场所组分控制参数` in a nested table, extract the four columns `物质 / 依据 / 类型 / 数值` and map each verified record to the dedicated writer. The template `建议：` row keeps its fixed label; if the source supplies a substantive recommendation, write it only to the non-bold value cell, otherwise leave the value empty. Synthetic spaced separators such as ` / ` become semantic line breaks before writing; compact source expressions such as `通风/排气` and `有/无` remain unchanged. A value line containing only `/` or `／` is a release blocker.

Source-side label/value contamination is reviewed during extraction and the
independent value cell remains authoritative. Output labels are never
rewritten; the persisted DOCX is compared with the fresh template skeleton so
only a label change relative to that baseline blocks release. The output audit
must not inspect a template baseline in isolation and declare its existing
example text to be an overwrite defect. Unknown or ambiguous PPE labels
likewise enter review and block formal projection; they are never assigned by
row position.

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
- The runtime must align the approved facts to the template's complete physical
  Section 11 skeleton before any row can be hidden. A pre-compacted list is not
  a valid positional payload. `11.1` route rows and `11.7` child rows are matched
  by their sublabels; an unmatched endpoint blocks instead of guessing.
- For `11.1` and `11.7`, the middle sublabel is not a value. Only the final
  value cell determines source presence. If the source never mentions an acute
  route, its empty row is hidden; an explicit source missing phrase remains in
  that route row.
- Preserve source route order where the template supports it.
- A simple conclusion such as `STOT assessment - single exposure: Based on available data, the classification criteria are not met.` may remain one field:value line; do not over-split it.
- When the source explicitly supplies a missing endpoint value, retain that endpoint row and write the exact missing-data placeholder. When the source has no endpoint field at all, suppress the template-only row; if every endpoint in Section 11 or 12 is absent or explicitly missing, retain only the source explanation row.
- Section 11.7 is an exact endpoint projection: `生育力`, `致畸形` and `体外遗传毒性` may only be populated from their matching source fields. An explicit source phrase such as `无数据资料` is retained for the matching endpoint; an unmatched or blank child row is hidden. Do not move `体外遗传毒性` study data into a blank reproductive-toxicity child row.
- Section 11 is source-field projection, not a reasoning step. Write only endpoint values, species, results, classifications, methods or evidence qualifiers explicitly present in the verified source/semantic payload. Do not add a method, species, classification, “similar product” qualifier, overall assessment or additional-information conclusion merely because a neighboring field exists in the template.
- The verified source field `主要粘膜刺激性` is classified into the existing semantic endpoint slot `11.3 主要眼睛刺激性`; this changes neither the locked label nor the source result/value, and the value must not be duplicated into `11.10 附加信息`.
- For study results, use direct source-grounded field lines in the value cell, such as material/substance, species, result, classification, method/guideline and the supported evidence qualifier `对类似产品的研究` / `Study of a similar product`.
- For acute dermal and acute inhalation conclusions, preserve the source's direct assessment wording; do not replace it with a missing-source explanation or an invented LD50/LC50.
- Never output the labels `原发性皮肤刺激` or `Primary skin irritation` when the source provides the structured study result; use the structured study block instead.

Use `scripts/structured_toxicology_policy.py`, `scripts/section11_alignment.py`
and the resource guide. Section 11 rules override `scripts/sentence_boundary_policy.py`.

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
- OpenSpec execution-record and empty-value-row audit
- Section 9 whole-row omission and continuous-renumbering audit
- continuous numbering audit
- locked-label/geometry audit
- whitespace audit
- Section 2 H/P layout audit
- Section 11 structured-field/study audit
- source coverage, fact-ledger and output-traceability audit
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

- Do not run any global font/spacing/indent normalization in the active
  overwrite pipeline.
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
- All inserted non-bold EN value text uses one approved Times New Roman 12-point body
  `w:rPr` exemplar selected from the active EN template. This is a character-
  format rule only: destination paragraph properties, labels, sublabels,
  table geometry, row heights, merges, borders and cross-page behavior remain
  template-owned. A blank template value slot must not cause a new value run
  to fall back to paragraph-level or mixed legacy formatting.
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
  classification, S11 endpoint slot mapping (including source aliases), H/P wording, EN
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
`source_sha256`, `s8_control_parameters`, a reviewed `source_mapping`, a
`source_coverage` record, a complete `fact_ledger`, a reviewed
`output_traceability` record, and a reviewed `agent_execution` record whose
`agent_mutation_boundary` exactly matches the active OpenSpec.
`source_mapping` must bind the same model and original-source SHA, cover all
S1-S16 sections, list unique source locators and source text, and explicitly
dispose each fact as `mapped`, `omitted`, `not_applicable`, `source_only` or
`duplicate`, with a reason where applicable. `conflict` and `unresolved` are
blocking decisions. `status=needs-review`, any unresolved item,
an unclassified target, a fact without source provenance, an output target
without traceability, or a missing section blocks the build. This is the
anti-omission/anti-invention evidence contract; it does not authorize an
agent to invent facts. Any gate failure raises `ReleaseBlocked` before a
formal output is promoted. Legacy `_task_work`
generators are frozen regression vehicles and are not production entry points.

## 20A. Source discovery, compatibility and non-bypassable gates

- Use `scripts/source_ingest.py` for source selection. `--source-dir` must
  resolve to exactly one supported candidate after model filtering; multiple
  candidates require an explicit `--source` path. Lock files and formal
  `*_MSDS_(CN|EN)_(冠志|国彩)` outputs are never discovery candidates, and a
  formal output cannot be passed as the source. Runtime output/cache directories
  (`output(s)`, `artifacts`, `_task_work`, `_docx_preview`, `.msds_cache`) are
  blocked as source locations; `覆写产出` is not intrinsically blocked because
  it may contain legitimate original MSDS files.
- The source registry currently recognizes `.docx`, `.docm`, `.doc`, `.odt`,
  `.rtf`, `.xlsx`, `.xls` and `.txt`. Direct section extraction is approved
  for DOCX/DOCM; DOC/ODT/RTF use a LibreOffice DOCX adapter whose result may
  be reused from a source-hash-bound persistent cache. The original source is
  still the only formal provenance source; cached conversions never become
  formal sources.
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
- DOCX variants may share read-only template state; PDF conversion is a
  bounded parallel batch by default (`--pdf-workers 2`). Use
  `--pdf-workers 1` for a conservative serial WPS environment. Each PDF
  remains one-to-one with its final audited DOCX and is independently gated.
- Performance work must remove duplicate parsing or redundant computation while
  preserving every release gate. A faster run with fewer audits is invalid.
- The formal command accepts `--cache-dir`, `--agent-review-seconds`,
  `--human-wait-seconds` and `--retry-count`; these are explicit cache and
  telemetry inputs, not semantic overwrite permissions. The report records
  machine time separately from caller-supplied review/wait time.

## 20D. Reusable evidence packet and one-shot preflight

Before asking the Agent to complete the semantic review, run the mechanical
source stage once:

```powershell
python scripts/prepare_evidence_packet.py --source SRC.docx --model MODEL `
  --out OUT/evidence-packet.json --cache-dir OUT/.msds_cache
```

The command creates a source-hash-bound packet containing the source-unit
inventory, fact-ledger scaffold, extraction review queue and the exact next
OpenSpec stage. A matching packet is reused on the next invocation; a legacy
`.doc/.odt/.rtf` conversion is reused from the same cache. The packet is
always `needs-review` with `build_allowed: false`. The Agent must copy its
`facts_draft` into the approved model and complete mapping, traceability and
the full execution acknowledgement before building.

Run the cheap facts gate before any template or PDF work:

```powershell
python scripts/build_eight.py --source SRC.docx --facts MODEL.json `
  --model MODEL --preflight-only --preflight-report OUT/preflight.json
```

The preflight lists all current blockers together. Only after it returns
`PREFLIGHT_PASS` should the Agent run the production command. This avoids
spending time on repeated partial builds while retaining the same fail-closed
checks used by `build_matrix`.

The recursive release audit requires one canonical copy of each final file.
If a stale `WORD/`, `PDF/` or deployment subtree creates duplicate basenames,
the audit reports the duplicate slot and skips the expensive DOCX text scan;
remove the stale copy before rerunning the audit.

## 20E. Resumable efficiency workflow (mandatory Harness entrypoint)

For repeated or slow Harness runs, use the single resumable coordinator instead
of writing a product-specific `build_*_facts.py`, manually invoking four
document writers, or copying a completed matrix into a second deployment tree:

```powershell
python scripts/run_efficiency_workflow.py `
  --source SRC.docx --model MODEL --workspace OUT
```

The first invocation performs source selection, evidence extraction and
source/cache reuse, then stops with `awaiting_review`. It writes:

- `OUT/evidence-packet.json` — mechanical, source-hash-bound evidence;
- `OUT/workflow-state.json` — resumable stage checkpoint;
- `OUT/.msds_cache/` — legacy conversion and packet cache.

After the Agent completes the reviewed facts JSON, resume the same workflow
with `--facts MODEL.json`. The coordinator writes `OUT/preflight.json` and
will not clone a template or start PDF conversion unless the complete facts
preflight passes. Only then does it invoke the formal four-DOCX/four-PDF
matrix builder once, under `OUT/output/MODEL/WORD` and `OUT/output/MODEL/PDF`.

```powershell
python scripts/run_efficiency_workflow.py `
  --source SRC.docx --model MODEL --workspace OUT `
  --facts MODEL.json --pdf-workers 2
```

The workflow is a scheduling and checkpoint boundary, not an approval
shortcut. A packet remains `build_allowed: false`; a cached conversion never
supplies facts; a blocked preflight prevents all template/PDF work; and the
four business stages, locked template rules and final-file audits remain
unchanged. If the run stops at `preflight_blocked`, fix the complete reported
list and rerun with the same workspace so extraction and cache work are not
repeated.

## 20C. DeepSeek Harness performance profile

The production entry point is one invocation of `scripts/build_eight.py` for
one reviewed facts model. The Agent must not manually open, translate, render
or independently rebuild four documents; that multiplies context and parsing
work and makes a Harness run appear stalled.

- Source selection, facts validation and template loading happen once. The
  pipeline then builds all four audited DOCX masters first, so the Harness can
  observe a complete intermediate checkpoint before PDF conversion begins.
- The WPS converter is resolved and version-checked once before DOCX work.
  Missing or unusable WPS CLI fails fast. The approved LibreOffice adapter is
  allowed only for legacy source conversion; LibreOffice/`soffice.exe`,
  ReportLab and any PDF-only authoring fallback must never author or replace
  the WPS-derived PDFs.
- PDFs are converted in one bounded batch. The default is two workers; use
  `--pdf-workers 1` when WPS or the host office process is unstable. Do not
  increase the worker count merely to hide a slow or blocked converter.
- Progress is emitted as `MSDS_PROGRESS` JSON lines. Add `--progress-file` for
  a durable last-event checkpoint. Add `--docx-preview-dir` when the Harness
  needs the four audited DOCX files before the PDF batch finishes. Preview
  files are diagnostic checkpoints and are never the formal release output.
- WPS calls use an owned process handle and deterministic kill/reap cleanup on
  timeout before temporary output is removed. This bounds hung-office and
  WinError 32 failures without killing unrelated Word/WPS sessions.
- `--no-pdf` is a fast DOCX-only diagnostic/smoke mode. It must not be used to
  claim the default eight-file release.
- V3.24 writes `timing.stage_events` and `timing.stage_totals` into
  `matrix-report.json`, covering source/semantic preparation, fixed-template
  writes, post-overwrite fine-tuning, release audits and PDF conversion. Use
  these observations to locate a bottleneck; do not turn the rough historical
  percentages into a time guarantee.
- V3.26 additionally writes `timing.cache`, `timing.pdf`,
  `timing.time_categories`, per-variant artifact hashes and the telemetry
  schema version. Run `python scripts/benchmark_efficiency.py --source SRC`
  to measure packet cold/warm reuse; add `--facts FACTS.json` and explicit
  worker counts for a temporary matrix comparison. Benchmark results are not
  a fixed SLA and benchmark output is not a formal deliverable.

Recommended Harness invocation:

```text
python scripts/build_eight.py --source SRC.docx --facts MODEL.json --out OUT \
  --pdf-workers 2 --progress-file OUT/matrix-progress.json \
  --docx-preview-dir OUT/_docx_preview --cache-dir OUT/.msds_cache
```

The performance profile changes scheduling and observability only. It never
weakens source interpretation, Agent mutation limits, template geometry,
empty-value hiding, numbering, semantic, or render gates; formal promotion
still requires four DOCX plus four corresponding PDFs.
