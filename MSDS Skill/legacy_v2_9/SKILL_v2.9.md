---
name: msds-word-standardizer
version: 2.9.0
description: Convert a non-standard Chinese MSDS/SDS Word file into a fixed company DOCX template with source-only product facts, immutable template labels/formatting, omission of unsupported items, compact table layout, normalized body-text styling, and mandatory render-based QA. Use when an Agent must accurately overwrite/standardize MSDS/SDS content without disturbing the approved Word template.
---

# MSDS Word Standardizer v2.9

## 0. Goal
Produce a standardized MSDS/SDS DOCX from:
- a **non-standard source MSDS/SDS** that supplies product facts; and
- a **standard company DOCX template** that supplies the approved structure and presentation.

The output must look as though a human editor filled the approved template carefully. It must **not** look regenerated.

## 1. Governing principle
**Template controls structure and locked presentation. Source controls product facts.**

Never take the union of the template sample product and the source product. A reference/approved MSDS may teach formatting and mapping conventions, but its product-specific values are never evidence for a new product.

## 2. Non-negotiable requirements
### R1 — Source-only factual scope
Use only facts supported by the supplied source unless the user explicitly authorizes outside research or professional completion. Do not silently infer CAS, concentration, GHS category, H/P statements, toxicology, ecology, transport class, storage limits, or regulations from another product.

### R2 — Bold labels are immutable anchors
Every bold template label is locked, whether numbered or unnumbered. For every surviving label preserve exactly:
- visible label wording, punctuation and spaces; numbering is locked during mapping but may be changed only by the post-omission continuous-renumber pass defined in R12;
- run properties (font, East Asia font, size, bold, color, underline, character spacing);
- paragraph properties (alignment, indentation, tabs, line spacing, before/after spacing);
- cell geometry and alignment;
- table borders, widths, merges and surrounding layout.

Do **not** recreate labels. Reuse the original template XML.

### R3 — Never reshape a fixed section to imitate the source
Semantic mapping is allowed; structural rewriting is not. This is especially strict for Sections 8 and 11. Never merge labels, rename labels, move labels, invent composite labels, or rebuild endpoint order.

### R4 — No corresponding value means the item is not displayed
If the source does not contain a semantically corresponding value, remove/hide the **complete item**, not merely the value. Do not leave an empty label, blank row, placeholder, or template sample value.

Missing-data suppression is mandatory. If a source value is only a missing-data marker such as “无数据”“无数据资料”“暂无数据”“无可用数据”“无适用资料”等, treat the item as **unsupported for display** and omit the complete item. Do not write the marker into the final MSDS.

**Section 11 exception — preserve source section-level toxicology availability statements.** A complete explanatory sentence such as `该产品无可用的毒理学研究。` is not treated as a disposable cell placeholder. If Section 11 contains such a product-level statement and no endpoint-specific toxicology data, keep the Section 11 heading and preserve that sentence as an unnumbered explanatory line. Do not invent endpoint labels or values merely to give the sentence a number. This exception is limited to substantive section-level source statements; a bare cell value such as `无数据` remains suppressed.

Do **not** automatically suppress “不适用” or a substantive negative conclusion such as “无刺激”“无危险反应”“非危险品”“无闪点”. These are applicability/scientific conclusions, not missing-data placeholders.

### R5 — Delete at the smallest safe item boundary
A “complete item” is not always a whole table row. If one row contains several independent label/value pairs, remove only the unsupported item without damaging supported siblings. Do not delete a row simply because one cell is unsupported.

### R6 — Compact layout is mandatory
Do not create visual height with formatting artifacts. Prohibited unless semantically required:
- empty paragraphs;
- empty non-label runs;
- tabs;
- repeated half/full-width spaces;
- trailing spaces;
- manual line breaks inserted for visual alignment;
- fixed/minimum row heights that leave blank areas.

Content should wrap naturally. One semantic value should normally occupy one paragraph.

### R7 — Body text has one approved character format
All non-bold value text uses the approved body-text exemplar. In the Guanzhi regression case the exemplar is the value **“水性羟基丙烯酸乳液”**. Copy its character/run properties only. Do not copy its paragraph alignment/indentation into unrelated cells.

### R8 — Headers/footers: values may change, layout may not
Update product code/name, MSDS identifier and revision date only when supported by the source/user instruction. Preserve header/footer table geometry, alignment, font and pagination layout.

### R9 — Preserve meaning and uncertainty
Do not “improve” source claims. Keep qualifiers such as “约”“＞”“类似产品”“无可用研究”“根据现有资料”. Normalize obvious extraction artifacts, not scientific meaning.

### R10 — Section 2 multi-H / multi-P statements use semantic line wrapping
For Section 2 only, when more than one hazard statement or precautionary statement is present:
- each distinct `Hxxx`/`EUHxxx` statement must start on its own line;
- each distinct `Pxxx` or combined `Pxxx+Pxxx...` statement must start on its own line;
- keep each code attached to its full statement; never split a code from its text;
- preserve source order unless the source explicitly groups them otherwise;
- category headings such as “预防措施：”“事故响应：”“安全储存：”“废弃处置：” may occupy their own line, followed by one P-statement per line;
- a single H or P statement remains a single line/paragraph and must not gain an unnecessary break.

This is a deliberate semantic formatting exception to the general “no manual line breaks for visual alignment” rule. Use line breaks only **between complete H/P statements**, never to force a visual width.

### R11 — Rendering is a release gate
Never deliver after XML/text checks alone. Render the final DOCX to page PNGs and visually inspect **every page**. Any layout defect requires another edit/render cycle.

### R13 — Product identity placement is fixed and must be validated proactively
For the Guanzhi template, product identity has three distinct display roles and Agents must not confuse them:
- the document header/title product-code position displays the product model/code (for example `EP-1704`);
- the value area beside `1.1  产品名称：` is intentionally left blank unless the user explicitly changes this company rule; **do not write the model/code there**;
- the value beside `中文名称：` must be formatted as `中文产品名称 + 单个半角空格 + 产品型号`, for example `水性环氧乳液 EP-1704`.

Footer/MSDS identifiers may still use the product model as required by the template, e.g. `EP-1704-MSDS`. This is not a reason to populate the `产品名称` value.

This rule is a mandatory pre-release identity audit. The Agent must derive it from the skill automatically and must not wait for the user to point out the mistake. If the source provides Chinese name `X` and model `M`, the expected Section 1 display is `中文名称 = X M`, while `产品名称` remains blank.

### R12 — After omission, displayed numbered items must be continuous
Missing-data/unsupported-item suppression happens **before final numbering**. After all display decisions are final, renumber every surviving numbered item within its own section in visible order so numbering is continuous (`2.1, 2.2, 2.3...`; likewise for Sections 9, 10, 11, 12, etc.).

Rules:
- Renumber only the numeric prefix (`N.x`). Do not change the label wording, punctuation after the number, bold state, run/paragraph formatting, indentation, alignment, table geometry, or item order.
- Do not renumber unnumbered child labels such as `吸入：`, `食入：`, `皮肤：`, `眼睛：`, `经口：`, `经皮：`, `吸入：`, glove-material subitems, or H/P statements. They remain children of their surviving parent.
- Do not promote a child item into a new numbered parent merely because another item was removed.
- A section heading such as `2.危险性概述` is not part of the item counter.
- Renumbering is **section-local** and starts at `.1` for the first surviving numbered item. Never carry a counter across sections.
- Preserve any intentional section-level numbering scheme only when the user/template explicitly defines a different scheme.
- Renumber only after omission is complete; never renumber first and then delete, because that can create a second gap.
- After renumbering, audit for duplicates, gaps, wrong section prefixes, and formatting drift.

This is the sole controlled exception to the rule that locked label text is immutable: **only the numeric prefix may change, and only to close gaps created by suppression.**

### R14 — Dual-company output is the default release mode
Unless the user explicitly asks for only one company version, every standardization task must produce **two synchronized final DOCX files** from the same normalized content model:

1. `CN_冠志` — Guangzhou Guanzhi New Materials version.
2. `CN_国彩` — Yingde Guocai Fine Chemical version.

The two files must be identical in product facts, section mapping, numbering, formatting, revision date, H/P layout, composition, safety data, transport data, pagination behavior and all other non-company-specific content. **Only the approved company-profile fields may differ.**

Approved company profiles:

**冠志**
- 供应商名称：`广州冠志新材料科技有限公司`
- 供应商地址：use the Guanzhi value already defined by the authoritative template/source for the task; do not replace it from memory when a newer template/source provides a different value.
- 电话：use the Guanzhi value already defined by the authoritative template/source for the task.
- 传真：use the Guanzhi value already defined by the authoritative template/source for the task.
- 页脚公司名称：`广州冠志新材料科技有限公司`

**国彩**
- 供应商名称：`英德市国彩精细化工有限公司`
- 供应商地址：`广东省英德市白沙镇太平村更古坑凯迪工业园区`
- 电话：`86-763-2811205`
- 传真：`86-763-2811024`
- 页脚公司名称：`英德市国彩精细化工有限公司`

Implementation requirement:
- Build one source-grounded normalized MSDS first.
- Render the `CN_冠志` version from that model.
- Derive the `CN_国彩` version by changing only the approved company-profile fields above; do not remap or regenerate product/safety facts separately.
- The footer identifier keeps the same product code/MSDS suffix; only the company-name portion changes. Example: `英德市国彩精细化工有限公司 EP-1704-MSDS`.
- Output filenames must clearly distinguish the two variants, preferably `<型号>_MSDS_CN_冠志.docx` and `<型号>_MSDS_CN_国彩.docx`.
- Run structural/content parity QA between the two outputs. Any difference outside the whitelisted company-profile fields is a release-blocking defect.
- Render and inspect **both** final DOCX files page-by-page before delivery.

## 3. Input contract
Required:
- `source_msds`: `.doc` or `.docx` non-standard source.

Default template:
- Use the bundled `examples/template_reference.docx` as the **authoritative current Guanzhi standard template** when the user does not explicitly provide a newer approved template.
- Do not substitute an older template from memory, a prior output, or a regression example.
- If the user explicitly supplies a newer approved template, that newer template supersedes the bundled baseline for that task; update the skill baseline only when the user asks to make it the new built-in template.

Optional:
- `reference_docx`: previously approved standardized file. It may be used only for mapping conventions/body style/QA expectations, never as a factual source for the current product.
- user policy: explicit exceptions such as regulatory updating, external research, company boilerplate rules, or permitted professional completion.

If source is legacy `.doc`, convert a working copy to `.docx` with LibreOffice. Do not overwrite the original.

## 4. Two-pass architecture — required
### Pass A: semantic extraction and mapping
Before touching the template, create an internal record for each source fact:
`source_section | source_label | normalized_meaning | exact_value | qualifiers | target_template_label | mapping_confidence | action`

Allowed actions:
- `MAP` — clear semantic match;
- `MAP_TO_OTHER_INFO` — only if an existing generic field genuinely fits;
- `OMIT_NO_TARGET` — source fact has no safe template destination;
- `OMIT_MISSING_DATA` — value is only a missing-data placeholder and therefore must not be displayed;
- `REVIEW_AMBIGUOUS` — mapping would change meaning.

Do not edit the DOCX during this pass.

### Pass B: layout-safe overwrite
Start from a **fresh copy of the untouched template**. Never continue patching a previously damaged output.

Populate only mapped values, remove unsupported items, normalize body text, compact whitespace, audit locked labels, render, inspect, iterate.

## 5. Safe editing algorithm
1. Resolve the template authority: use the bundled `examples/template_reference.docx` unless the user explicitly supplied a newer approved template. Never use an older cached template.
2. Snapshot the untouched template (`scripts/snapshot_template.py`).
3. Identify the approved body exemplar and capture its `w:rPr`.
4. Build source-to-template mapping and classify missing-data placeholders as `OMIT_MISSING_DATA` **before any DOCX write**.
5. Resolve product identity placement before writing: header code = model; `1.1 产品名称` value = blank; `中文名称` = Chinese name + one ASCII space + model; footer identifier follows template.
6. For Section 2, tokenize multi-H/multi-P fields into complete coded statements before writing.
7. For each supported item:
   - keep original label XML untouched;
   - replace only the value area;
   - prefer editing a separate value cell;
   - if label/value share a paragraph, preserve all locked bold runs and replace only the non-bold value runs.
8. For unsupported or missing-data items, remove the smallest complete display unit.
9. Run conservative compaction.
10. Run the **post-omission continuous-renumber pass** (`scripts/renumber_visible_items.py`) after all hide/delete decisions are final.
11. Run numbering, structural and locked-format audits.
12. For Section 2, apply/audit multi-H/multi-P semantic line wrapping after the parent-item numbering is final.
13. Generate both company variants from the same normalized content state: `CN_冠志` and `CN_国彩`, unless the user explicitly requested only one. Apply only the R14 company-profile substitutions.
14. Run `scripts/company_profile_policy.py` to audit each variant and compare them for unauthorized content divergence.
15. Render all pages of **both** variants and visually inspect every page.
16. Fix from the fresh/template-safe document state if an edit damaged layout; do not accumulate destructive patches.

## 6. Critical implementation rules
### Never use these destructive patterns
- `paragraph.text = ...` on a template paragraph;
- `cell.text = ...` on a formatted template cell;
- clearing every run and placing all text into run 0;
- reconstructing bold labels from strings;
- adding spaces/tabs to make columns “look aligned”;
- copying a whole paragraph style from a body exemplar onto a label paragraph;
- deleting arbitrary rows to make the source section order fit.

### Preferred pattern
Use existing template nodes. For a separate value cell, replace only its content run(s) while retaining the cell/paragraph XML. For mixed label/value paragraphs, preserve label runs byte-for-byte where possible and replace only value runs.

See `docs/ooxml_editing_patterns.md`.

## 7. Empty-item policy
Determine support **before** formatting.

A displayed item must satisfy:
`source-supported substantive value` + `safe semantic target`.

A pure missing-data placeholder fails this test even if it literally appears in the source.

If false, omit the item. Never retain an item merely because the template contains it.

When removing an item:
- remove the row only if the row represents exactly that item;
- if a row contains multiple items, remove the unsupported cell/item at the smallest safe XML boundary;
- preserve table grid/merge integrity;
- after all removals are complete, renumber surviving numbered sibling items continuously using the controlled numeric-prefix-only rule in R12.

## 8. Whitespace/height policy
A visually tall row with short text is a defect unless the template intentionally requires it.

Inspect for:
- trailing `<w:p>` elements;
- empty `<w:r>` elements;
- `<w:br>` / `<w:tab>`;
- whitespace-only text nodes;
- `w:trHeight` with exact/minimum rules;
- paragraph `spaceBefore/spaceAfter` on body paragraphs;
- multiple paragraphs created by source hard wraps.

Known regression checkpoints: Section 5.4, 6.1, 11.2, 12.2, 13 and 14.

**Important:** do not globally strip all empty XML. Word requires at least one paragraph per cell, and some template paragraphs are intentional. Cleanup must be content-aware and label-aware.

## 9. Section mapping rules
Read `docs/section_mapping_rules.md`. Summary:
- **S1:** enforce the product identity-placement contract: header shows model; `1.1 产品名称` value stays blank; `中文名称` shows `中文产品名称 + 空格 + 型号`. Supplier/contact/footer company fields are then populated from the selected company profile (`冠志` or `国彩`) under R14. Do not rewrite template labels.
- **S2:** only source-supported GHS/classification/label data. Suppress missing-data placeholders. Multi-H and multi-P statements must be split one complete statement per line, preserving source order. No template hazard leakage.
- **S3:** source composition only; preserve “商业机密” and source ranges exactly.
- **S4–S7:** map by safety function; remove extraction hard-wraps; keep concise prose.
- **S8:** source “控制参数/暴露控制” headings are not replacement labels. Map respiratory, hand, eye, body protection to existing template items only.
- **S9:** property-by-property semantic mapping. Source-only technical parameters may use existing “其他信息” if appropriate.
- **S10:** stability/reactivity endpoints map only to equivalent template labels.
- **S11:** endpoint mapping only. Do not rebuild toxicology structure. Preserve qualifiers like “类似产品”. Unsupported endpoints disappear. However, if the source provides only a section-level toxicology availability statement (e.g. `该产品无可用的毒理学研究。`), retain it as an unnumbered explanatory line beneath the Section 11 heading.
- **S12:** ecology endpoints map individually; compact prose and no hidden blank paragraphs.
- **S13–S14:** compact continuous prose; no forced line-per-sentence formatting.
- **S15–S16:** follow source-only rule unless user explicitly defines company boilerplate/update policy.

## 10. Format normalization rules
### Locked labels
Use the untouched template as the only formatting authority. If an output label drifts, restore its original XML properties rather than approximating formatting.

### Non-bold values
Copy the approved exemplar's run properties (`w:rPr`) to non-bold value runs. Preserve the destination paragraph's layout properties unless specifically authorized.

### Spacing
Do not insert alignment spaces. Normalize accidental repeated spaces in body values, but preserve meaningful spaces inside codes/units/names.

### Units and punctuation
Do not silently alter scientific values. Cosmetic normalization is allowed only when meaning is unchanged (e.g., removing extraction line breaks). Preserve source inequalities/ranges.

## 11. Built-in template baseline
The bundled `examples/template_reference.docx` is the current approved baseline installed with this skill. Treat its XML/layout as authoritative.

Baseline invariants:
- 16 MSDS section tables are present.
- Section 15 follows the latest template structure and **includes** the row `物质或混合物的相关安全、健康和环保法律法规`; preserve it exactly.
- The current Section 11 table has 6 rows and its multi-column/merged-cell geometry is locked to the bundled template.
- The current Section 2 table has 16 rows; its row/cell geometry is locked even when unsupported items are omitted/re-numbered using safe item-boundary rules.
- All bold labels, table geometry, merged cells, paragraph alignment, and header/footer layout come from this bundled file, not from regression examples.
- `tests/template_snapshot.json` must be regenerated whenever the bundled template is intentionally replaced.

See `docs/template_baseline.md` for the pinned file identity and replacement procedure.

## 12. Validation gates
The output is releasable only when **all** gates pass.

### Gate A — content provenance
- no template/reference sample product values leaked;
- every displayed product-specific value is source-supported or explicitly authorized;
- no unsupported item remains visible;
- no missing-data placeholder remains visible as a final field value.

### Gate A2 — product identity audit
Before format QA, verify all of the following automatically:
- header/title product code equals the source model;
- `1.1 产品名称` value area is blank;
- `中文名称` equals source Chinese product name + one ASCII space + source model, with no duplicate model;
- footer/MSDS identifier contains the correct model according to template convention;
- no model was accidentally inserted into unrelated Section 1 value fields.

Use `scripts/product_identity_policy.py` as the validation reference. Any failure blocks release.

### Gate B — locked-format audit
Run `scripts/audit_locked_labels.py`. Any unexpected bold-label wording/style drift is a failure. A numeric-prefix difference is allowed only when it exactly matches the required continuous post-omission numbering.

### Gate B2 — numbering continuity audit
Run `scripts/renumber_visible_items.py --audit-only`. Every displayed numbered item within each section must be continuous, unique, and use the correct section prefix. Any gap such as `2.1, 2.2, 2.4`, duplicate, or cross-section prefix is a release failure.

### Gate C — Section 2 H/P audit
For every populated 2.5/2.6 field:
- if multiple H/EUH statements exist, each complete statement starts on a new logical line;
- if multiple P statements exist, each complete statement starts on a new logical line;
- source order is preserved;
- no code is separated from its sentence;
- no break exists merely to force visual alignment.

Use `scripts/section2_hp_policy.py` as the parsing reference.

### Gate D — whitespace audit
Run `scripts/audit_whitespace.py`. Investigate all flagged populated cells/rows.

### Gate E — structure audit
Run `scripts/inspect_docx_structure.py` or snapshot comparison for high-risk sections.

### Gate F — visual render
Render with `/home/oai/skills/docx/render_docx.py` (or equivalent). Inspect every page at 100%.

Check:
- label alignment and indentation;
- no tall blank zones below short values;
- no clipped/overlapping text;
- compact Sections 11–14;
- correct header/footer identifiers;
- sensible page breaks;
- no accidental font/style changes in body text.

## 13. Failure recovery
If labels become misaligned or a section is structurally distorted:
1. stop patching the damaged file;
2. return to a fresh copy of the template;
3. reuse the already-approved semantic mapping;
4. reapply values with safe value-only edits;
5. rerun all gates.

Do not “fix” label alignment with spaces/tabs.

## 14. Agent decision policy
Ask the user only when a choice is genuinely semantic/policy-sensitive, for example:
- source fact could map to two materially different endpoints;
- user expects current regulatory research but source is old;
- company boilerplate conflicts with source-only policy;
- removal of an unsupported item would break a complex merged-row template and no approved removal rule exists.

Do not ask about routine layout cleanup; apply this skill's rules.

## 15. Definition of done
- [ ] Started from untouched template.
- [ ] Source facts inventoried before editing.
- [ ] No product-specific template/reference leakage.
- [ ] Product identity placement passes: header model correct; `产品名称` value blank; `中文名称 = 中文产品名称 + 空格 + 型号`; footer identifier correct.
- [ ] Every visible item has a supported value.
- [ ] Unsupported items and missing-data-placeholder items are absent, not blank and not shown as “无数据/无适用资料”.
- [ ] After omission, every surviving numbered section item is renumbered continuously with no gaps/duplicates; only numeric prefixes changed.
- [ ] All surviving bold labels retain original wording and layout.
- [ ] Section 2 multi-H/multi-P statements are one complete statement per line, without code/text separation.
- [ ] Section 8 is not structurally rewritten.
- [ ] Section 11 endpoint structure is not rewritten.
- [ ] Body text matches approved exemplar formatting.
- [ ] No avoidable blank paragraphs/runs/tabs/manual breaks.
- [ ] Short values do not create tall rows.
- [ ] Header/footer product metadata is correct.
- [ ] Automated audits pass or all warnings are manually resolved.
- [ ] Every rendered page was inspected after the final edit.

## 16. Packaged resources
- `docs/requirements_spec.md` — complete user requirement contract.
- `docs/locked_format_contract.md` — exact locked-format definition.
- `docs/section_mapping_rules.md` — detailed section-by-section mapping policy.
- `docs/template_baseline.md` — pinned identity, structural baseline, and replacement procedure for the built-in latest template.
- `docs/ooxml_editing_patterns.md` — safe and unsafe python-docx/OOXML patterns.
- `docs/qa_acceptance.md` — release checklist and visual QA rubric.
- `docs/lessons_learned.md` — failure modes learned from iterative PA-4817 standardization.
- `scripts/snapshot_template.py` — capture template structural baseline.
- `scripts/audit_locked_labels.py` — detect label text/style drift.
- `scripts/audit_whitespace.py` — detect hidden height/whitespace risks.
- `scripts/compact_docx.py` — conservative cleanup; must be followed by render QA.
- `scripts/section2_hp_policy.py` — missing-data classifier and H/EUH/P semantic statement splitter for Section 2.
- `scripts/renumber_visible_items.py` — post-omission numeric-prefix-only renumber/audit helper for surviving numbered items.
- `scripts/product_identity_policy.py` — validates Guanzhi product-code/Chinese-name placement so Agents catch Section 1 identity mistakes before delivery.
- `scripts/inspect_docx_structure.py` — debug table/paragraph/run structure.
- `examples/` — template, non-standard source, and approved final regression example. Example facts must never be reused for other products.

## 17. Delivery
Unless the user asks otherwise, deliver only the final standardized `.docx`. QA PNG/PDF files are internal artifacts.


## v2.7 强制排序 / 编号交付门禁
- 所有“无数据显示删除”完成后，必须对每个章节的**实际可见主项目**重新按 1,2,3... 连续编号。
- 交付前必须运行 `scripts/renumber_visible_items.py <docx> --audit-only`；返回非 0 时禁止交付。
- 同一主项目允许连续重复编号用于子项，例如 11.1 急性毒性下的“经口 / 经皮 / 吸入”；这些子行不得把后续主项目推成 11.4。
- 连续重复的子项顺序应保持源 MSDS 的语义顺序；例如源文为“经口 → 经皮 → 吸入”，标准化后也保持该顺序。
- 删除项目后不得保留模板原序号造成断号，例如 Section 2 若“紧急情况概述”被删除，则原 2.2/2.3 必须重排为 2.1/2.2。
- QA 不仅检查“数字是否存在”，还检查：断号、倒序、重复主项目、已结束编号再次出现。


## v2.8 新模板表格基线
- `examples/template_reference.docx` 已替换为用户确认的 `模板_MSDS_CN_冠志(3).docx`。
- 新模板的表格行列、合并关系、宽度、边框、标签位置、段落格式和页眉页脚布局为最高结构权威。
- 禁止从 v2.7 或更早输出回填旧表格结构。
- 冠志/国彩继续共用同一结构模板，国彩仅应用公司资料白名单覆盖。

### R15 — 正文按句号/分号执行语义换行（Sentence Boundary Line-Break Policy）
除 Section 2 的 H/P 专用规则外，所有正文值在写入最终 DOCX 前必须执行统一的语义换行规范：
- 中文句号 `。` 后换行；句号保留在上一行。
- 中文分号 `；` 后换行；分号保留在上一行。
- 英文分号 `;` 后换行。
- ASCII 英文句点 `.` **不得机械全局拆分**，因为可能属于小数、缩写、CAS/编号、单位、URL 等。只有在能够明确判定为完整英文句子结束时才允许换行。
- 逗号 `，,`、顿号 `、`、冒号 `：:` 默认不作为换行点。
- 换行只改变同一值内部的显示行，不创建新的 `N.x` 编号、不创建新的表格行、不改变父子层级。
- 使用同一段落内的 Word line break（`w:br` / `run.add_break()`）实现，不通过新增空段落、空行、tab 或重复空格制造视觉间距。
- Section 11 中一段包含多个完整句子/分号分隔语句时同样执行；但 `经口：`、`经皮：`、`吸入：` 等既有模板子标签仍按模板结构处理，不能因本规则重建结构。
- Section 2 的 H/EUH/P 规则优先级更高：先按完整 H/P 语句逐条分行，再对语句内部禁止二次机械拆分。
- 已有合理换行保留；连续空行必须折叠，不得产生额外行高。

执行顺序更新为：`语义映射 → 缺失项删除 → 连续重编号 → H/P 专用分行 → 普通正文句号/分号语义分行 → 空白压缩 → 锁定格式审计 → 双公司一致性审计 → 双版本逐页渲染 QA`。

交付前应使用 `scripts/sentence_boundary_policy.py` 的同等逻辑检查正文；发现同一正文显示行中在 `。/；/;` 后仍紧跟另一完整语句时，应在不破坏模板结构的前提下修正后再交付。
