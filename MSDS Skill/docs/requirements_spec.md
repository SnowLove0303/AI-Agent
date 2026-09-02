# Requirements Specification

## Functional objective
Transform a non-standard MSDS/SDS Word document into the company's standard Word template while preserving the template's approved visual system.

## Content authority
1. Source MSDS = authority for product-specific facts.
2. Template = authority for section structure, labels and formatting.
3. Approved reference = authority only for editing conventions and visual expectations.
4. External sources = forbidden unless explicitly requested/authorized.

## Display rule
- Supported source value + safe target => display.
- No supported value => do not display the item.
- Missing-data placeholders such as “无数据”“无数据资料”“暂无数据”“无可用数据”“无适用资料” => **do not display the item**. Treat them the same as no supported value for final-display purposes.
- Exception for Section 11: a complete source sentence describing product-level toxicology-study availability, e.g. `该产品无可用的毒理学研究。`, must remain as an unnumbered explanatory line. This is not equivalent to a bare `无数据` placeholder.
- “不适用” is not automatically a missing-data marker. If it is a substantive applicability conclusion from the source, it may remain.
- Substantive negative conclusions such as “无刺激”“无危险反应”“非危险品”“无闪点” remain displayable because they communicate actual findings, not data absence.
- Template sample value without source support => delete/replace; never retain.

## Label rule
All bold labels are immutable, including:
- numbered fields: `11.2 主要皮肤刺激性：`;
- unnumbered fields: `呼吸系统防护：`;
- section headings.
Their original alignment is part of the template and must survive generation.

## Layout rule
Output must be compact. Do not increase page count/row height through empty paragraphs, tabs, hard wraps, trailing whitespace or regenerated formatting.

## Body text rule
All non-bold inserted text uses the approved exemplar's character formatting. Paragraph geometry remains destination-specific.

## Omission rule
Do not leave empty labels. Remove unsupported items at the smallest safe display unit while preserving neighboring supported items and table integrity.

## High-risk sections
- Section 8: PPE/control hierarchy must remain template-defined.
- Section 11: toxicology endpoint hierarchy must remain template-defined.
- Sections 12–14: prone to hidden blank paragraphs and excessive vertical height.
- Section 5.4/6.1: also known to retain invisible extra paragraphs.

## Acceptance
A file is accepted only after automated audits and full-page rendered visual inspection.


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
7. Audit every section after renumbering for gaps, duplicates, wrong section prefixes and formatting drift.
8. Required operation order: semantic mapping -> suppress unsupported/missing-data items -> whitespace cleanup -> continuous renumber -> locked-format audit -> Section 2 H/P layout audit -> render/visual QA.

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
