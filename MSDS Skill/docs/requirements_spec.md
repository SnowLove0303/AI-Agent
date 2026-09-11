# Requirements Specification

## Functional objective
Transform one selected MSDS/SDS source into the company's standard Word template while preserving the template's approved visual system. The default release is one synchronized eight-file matrix: four DOCX masters and four PDF derivatives.

## Source selection and format boundary
- Resolve an explicit source file or use `scripts/source_ingest.py` to discover exactly one supported candidate under a directory.
- Bind the approved facts JSON to the original source SHA-256. A temporary conversion path is never the source of truth.
- The approved automatic section extractor covers DOCX/DOCM and legacy Word/ODT/RTF through a temporary DOCX adapter. XLS/XLSX and text sources may be discovered and provenance-recorded, but must not be guessed into the 16-section model until a dedicated semantic/coordinate adapter is approved. PDF is a publication-only derivative and is not a source input.
- A formal `*_MSDS_(CN|EN)_(冠志|国彩)` output and any lock file are not valid inputs. Ambiguous directory discovery is a hard stop.

## Content authority
1. Source MSDS = authority for product-specific facts.
2. Template = authority for section structure, labels and formatting.
3. Approved reference = authority only for editing conventions and visual expectations.
4. External sources = forbidden unless explicitly requested/authorized.

## Display rule
- Supported source value + safe target => display.
- No supported value => do not display the item.
- Missing-data placeholders normally suppress the item. Endpoint-specific rules have priority: source-backed Section 2 `其他危险` keeps the explicit source wording `无适用资料。`; Section 11.7 keeps `无数据` only for an explicitly present missing endpoint; absent Section 11.7 children are hidden.
- Exception for Section 11: a complete source sentence describing product-level toxicology-study availability, e.g. `该产品无可用的毒理学研究。`, must remain as an unnumbered explanatory line. This is not equivalent to a bare `无数据` placeholder.
- “不适用” is not automatically a missing-data marker. If it is a substantive applicability conclusion from the source, it may remain.
- Substantive negative conclusions such as “无刺激”“无危险反应”“非危险品”“无闪点” remain displayable because they communicate actual findings, not data absence.
- Template sample value without source support => delete/replace; never retain.

## Label rule
All labels and bold label runs are immutable, including:
- numbered fields: `11.2 主要皮肤刺激性：`;
- unnumbered fields: `呼吸系统防护：`;
- section headings.
Their original alignment is part of the template and must survive generation.

For source CN Section 2, bind the verified source headings to the existing
template semantic slots. The baseline's CN labels, punctuation and bold
formatting remain unchanged; source headings are never copied into locked
label cells. Only the corresponding value cells may be written or suppressed.
The source `2.2 标签要素` is the label-ingredient explanation slot, normally
containing `必须列在标签上的有害成分：` and the source ingredient on a
separate logical line. It is not the `2.4 信号词` slot; signal word is a
separate exact value (`危险`/`警告` or `Danger`/`Warning`). Label-ingredient
prose in the signal-word slot is a release blocker.

## Layout rule
The bundled formal template is the layout authority. Preserve its table/cell
geometry, row heights, paragraph properties, run properties, header/footer and
page fields. Remove only unsupported rows/blocks permitted by the source-
presence policy; never globally normalize fonts, spacing, indents or page
breaks to make the output look compact.

All maintained formal templates allow their tables to continue across pages.
The row-level `cantSplit` setting is template-owned: preserve whatever setting
the active baseline supplies on every surviving row, and compare it together
with table-level behavior and repeating-header settings against the fresh
template. This prevents generation from silently changing the page behavior of
the newly approved baseline.

## Body text rule
All non-bold inserted text uses the approved exemplar's character formatting.
For EN output, one Arial 12-point `w:rPr` exemplar from the active EN
template is applied to every inserted non-bold value run, including values
written into originally blank template slots. Paragraph geometry remains
destination-specific; labels, sublabels and table formatting remain locked.

## Omission rule
Do not leave empty labels. Remove unsupported items at the smallest safe display unit while preserving neighboring supported items and table integrity.

### Empty-value row suppression (mandatory)

When a source MSDS has no value that semantically matches a template label, the
complete dedicated label/value row is hidden before numbering. An empty value
cell is not customer-facing content and must not be left beside a visible
label. The only surviving blank value cells are the explicit company or
template-structure exceptions already listed in the locked-format and mutation
whitelist contracts. This rule applies to ordinary fields, component rows and
PPE rows; Section 2, Section 9, Section 11/12 and Section 8.2 keep their
endpoint-specific policies.

Row suppression is not label mutation. The label object is either preserved as
part of a surviving row or removed with its complete dedicated row. After all
suppression is complete, surviving numbered items are scanned in visible
semantic order and only their numeric prefixes may be made continuous.

## High-risk sections
- Section 8: PPE/control hierarchy must remain template-defined.
- Section 11: toxicology endpoint hierarchy must remain template-defined.
- Sections 12–14: prone to hidden blank paragraphs and excessive vertical height.
- Section 5.4/6.1: also known to retain invisible extra paragraphs.

## Acceptance
A file is accepted only after automated audits and full-page rendered visual inspection.

## Performance contract
- Load each maintained CN/EN template once per matrix and reuse it as a
  read-only audit/normalization reference.
- Reuse the saved staged DOCX object across compatible in-process audits;
  retain the saved DOCX as the only PDF conversion input.
- Use bounded PDF batch conversion for throughput; `--pdf-workers 1` remains
  available for conservative serial office-process behavior.
- Any speed improvement must preserve the complete release-gate set and the
  exact eight-file output contract.
- Prepare source coverage, fact-ledger scaffolding and the review queue once
  with `scripts/prepare_evidence_packet.py`; reuse is allowed only when the
  packet key matches the original source SHA-256, adapter/schema and active
  source-interpretation contract.
- Legacy `.doc/.odt/.rtf` conversion may use the same source-hash-bound
  persistent cache. A cache hit is an extraction optimization only and never
  changes original-source provenance or approval status.
- Run `scripts/preflight_facts.py` or `build_eight.py --preflight-only` to
  collect all facts/OpenSpec blockers before template cloning or PDF work.

## Template and provenance hard gates

- The active CN, EN and EN-source template files are byte-pinned. A changed
  hash blocks the matrix before any template is cloned or output is written.
- The approved facts file must contain a reviewed `source_mapping` bound to
  the requested model and original-source SHA-256. It must cover S1-S16 with
  unique source locators, source text, and an explicit `mapped`, `omitted` or
  `not_applicable` decision; omitted/not-applicable decisions require a
  reason. Unresolved or unreviewed items block release.
- Mapping is semantic evidence, not permission to invent content. The source
  remains authoritative for product facts; the standard template remains
  authoritative for labels, slot order and formatting.


## Section 2 H/P line-wrapping rule
For the template fields “危险性说明” and “防范说明”:
1. Detect complete hazard statements beginning with `Hxxx` or `EUHxxx`.
2. Detect complete precautionary statements beginning with `Pxxx` or a combined code such as `P301+P310`.
3. If two or more statements are present, place **one complete coded statement per line**.
4. Never split the code from its sentence.
5. Preserve source order.
6. Optional P-statement group headings such as “预防措施：”“事故响应：”“安全储存：”“废弃处置：” may stay on their own line.
7. Do not add line breaks inside one statement merely to make the cell look narrower. Natural Word wrapping handles width.
8. Single H/P statements remain unbroken except for natural Word wrapping.
9. These semantic line breaks are allowed even though visual-alignment line breaks are generally prohibited.

## Built-in latest template policy
- The skill ships with `examples/template_reference.docx` as the current approved Guanzhi template baseline.
- When no newer approved template is explicitly provided for a task, this bundled file MUST be used.
- Older templates, prior outputs, and regression examples MUST NOT be used as substitutes.
- If a user explicitly replaces the company template and requests it be built into the skill, update the bundled template, snapshot, baseline hash/structure, changelog, and version together.
- The current built-in baseline has 16 section tables; Section 15 contains 9 rows and does not contain the older standalone row `物质或混合物的相关安全、健康和环保法律法规`.


## Post-omission numbering continuity (mandatory)
1. First decide which items are displayed. Missing-data and unsupported items are removed before numbering.
2. Then, for each section independently, scan surviving numbered labels in visible document order.
3. Rewrite only the numeric prefix so the sequence is continuous from `.1`: e.g. if original `2.3` is removed, original `2.4` becomes `2.3`.
4. Preserve the remainder of each label exactly, including wording, punctuation, bold formatting, font, indentation, alignment and cell geometry.
5. Unnumbered children do not consume a number and must remain attached to their parent.
6. H/EUH/P statements do not consume `2.x` numbers. Multiple H/P lines remain inside the corresponding surviving parent item.
7. Audit ordinary sections after renumbering for gaps, duplicates, wrong section prefixes and formatting drift. Sections 11/12 retain standard source endpoint numbers after omission; audit them for order and duplicate re-entry instead of renumbering endpoints.
8. Required operation order: semantic mapping -> suppress unsupported/missing-data items -> whitespace cleanup -> continuous renumber -> locked-format audit -> Section 2 H/P layout audit -> render/visual QA.

Semantic slot mapping is mandatory. In Section 1, leave `1.1 产品名称` blank and put `中文名称 + 型号` in the existing `中文名称` value cell. In Section 8, map source `8.1 控制参数` to the template `8.2 工程控制` value and source PPE rows under the template `8.1 暴露控制` block; the fixed `建议` label has no output value. In Section 12, source `生态毒性` must populate template `12.1`, not either template-only leading explanation row. Synthetic spaced-slash separators are converted to semantic line breaks; a slash-only line blocks release.

## Product identity placement (mandatory)
For the current Guanzhi template, product identity is not duplicated across all Section 1 fields. Apply this without waiting for user correction:
1. Header/title model position: display the product model/code.
2. `1.1 产品名称：` value: leave blank by company convention. Do not place the model here.
3. `中文名称：` value: `source Chinese product name + one ASCII space + product model`. Example: `水性环氧乳液 EP-1704`.
4. Footer/MSDS identifier: use the product model according to template convention, e.g. `EP-1704-MSDS`.
5. Validate that the model occurs exactly where intended and is not duplicated in the Chinese-name value.
6. This is a proactive QA requirement: an Agent must detect and correct a wrong placement before delivery, not after user feedback.


## Dual-company release requirement (v2.6)
Default output count is two DOCX files per standardized product: `CN_冠志` and `CN_国彩`. Both must share the same source-grounded product/safety content. The Guocai variant changes only supplier name/address/telephone/fax and footer company name to the approved Guocai profile. Any other content difference is forbidden unless explicitly requested. Both outputs require full render-based QA.


## v2.7 强制排序 / 编号交付门禁
- 所有“无数据显示删除”完成后，必须对每个章节的**实际可见主项目**重新按 1,2,3... 连续编号。
- 交付前必须运行 `scripts/renumber_visible_items.py <docx> --audit-only`；返回非 0 时禁止交付。
- 同一主项目允许连续重复编号用于子项，例如 11.1 急性毒性下的“经口 / 经皮 / 吸入”；这些子行不得把后续主项目推成 11.4。
- 连续重复的子项顺序应保持源 MSDS 的语义顺序；例如源文为“经口 → 经皮 → 吸入”，标准化后也保持该顺序。
- 删除项目后不得保留模板原序号造成断号，例如 Section 2 若“紧急情况概述”被删除，则原 2.2/2.3 必须重排为 2.1/2.2。
- QA 不仅检查“数字是否存在”，还检查：断号、倒序、重复主项目、已结束编号再次出现。

## v2.9 正文语义换行
标准化正文必须以完整句子为阅读单元。默认在中文句号 `。`、中文分号 `；`、英文分号 `;` 后换行，标点留在上一行。不得机械拆分 ASCII `.`，以免破坏小数、缩写、编号、单位或 URL。换行必须发生在同一模板值区域内部，不新增表格行、不新增编号、不产生空段落。Section 2 H/P 专用规则优先。
