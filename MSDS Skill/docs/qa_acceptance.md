# QA and Acceptance

## Automated checks
1. Snapshot/template structure baseline.
2. Locked-label audit.
3. Whitespace/height audit.
4. Structure dump for suspicious sections.
5. Table cross-page contract audit against the fresh formal template.

## Visual checks — every page
At 100% inspect:
- all bold labels align exactly like template;
- body font is consistent;
- no large blank area under short values;
- no blank label rows;
- no visible bare missing-data placeholder rows except the documented source-backed Section 2 `其他危险` wording and explicit Section 11.7 missing endpoints; Section 11 may retain a complete source-level availability sentence such as `该产品无可用的毒理学研究。`;
- Section 2 multi-H/multi-P: one complete coded statement per line, source order preserved, no code separated from its statement;
- no clipped or overlapping text;
- tables remain within page margins;
- header/footer product code/date are correct;
- page breaks are reasonable.
- tables may continue across pages as in the formal template; no artificial page break or table-level cross-page restriction is introduced;
- surviving rows retain the template's row-splitting and repeating-header settings.

## Section 2 mandatory checks
- If 2.5 contains ≥2 H/EUH statements, verify each starts on a new line.
- If 2.6 contains ≥2 P statements, verify each starts on a new line.
- Verify line breaks occur only between complete statements, not mid-statement.
- Verify no missing-data placeholder remains visible anywhere in Section 2.

## Mandatory regression hotspots
- 5.4
- 6.1
- Section 8
- 11.2 and neighboring toxicology items
- 12.2
- Sections 13 and 14

## Release rule
A warning is not automatically a failure, but every warning must be resolved by inspection. The final render must be from the exact DOCX being delivered.


## Numbering continuity gate
- After all unsupported/missing-data items are omitted, inspect every section containing `N.x` labels.
- The visible sequence must be `N.1, N.2, N.3...` with no gaps or duplicates.
- Only the numeric prefix may differ from the baseline template due to this pass. Label wording and formatting must remain baseline-equivalent.
- Child labels and H/P lines must not be counted as numbered siblings.
- Any discontinuity is a release blocker.


## Product identity gate
- Header/title model is correct.
- `1.1 产品名称` value is blank.
- `中文名称` is exactly `中文产品名称 + 单个半角空格 + 型号`.
- Footer/MSDS identifier uses the same model.
- Model is not duplicated or misplaced.
- This gate must be checked proactively; user feedback is not part of the QA mechanism.


## Dual-company parity gate (v2.6)
When both variants are required, release only if:
- both DOCX files exist and render successfully;
- each is visually inspected on every page;
- Guocai supplier/contact/footer fields exactly match the approved profile;
- Guanzhi supplier/contact/footer fields remain the authoritative Guanzhi values;
- after normalizing the whitelisted company-profile fields, the two documents are textually equivalent;
- there are no differences in product identity, composition, hazards, H/P statements, section numbering, technical data, revision date, or transport/regulatory/safety prose caused by the company switch.


## v2.7 强制排序 / 编号交付门禁
- 所有“无数据显示删除”完成后，必须对每个章节的**实际可见主项目**重新按 1,2,3... 连续编号。
- 交付前必须运行 `scripts/renumber_visible_items.py <docx> --audit-only`；返回非 0 时禁止交付。
- 同一主项目允许连续重复编号用于子项，例如 11.1 急性毒性下的“经口 / 经皮 / 吸入”；这些子行不得把后续主项目推成 11.4。
- 连续重复的子项顺序应保持源 MSDS 的语义顺序；例如源文为“经口 → 经皮 → 吸入”，标准化后也保持该顺序。
- 删除项目后不得保留模板原序号造成断号，例如 Section 2 若“紧急情况概述”被删除，则原 2.2/2.3 必须重排为 2.1/2.2。
- QA 不仅检查“数字是否存在”，还检查：断号、倒序、重复主项目、已结束编号再次出现。

## Sentence-boundary line-break gate (v2.9)
- 普通正文中，中文句号 `。`、中文分号 `；`、英文分号 `;` 是默认语义换行点。
- 标点保留在上一行；下一完整语句从新行开始。
- 不得通过空段落、tab、重复空格制造换行。
- ASCII `.` 不做盲目全局拆分，必须避免破坏小数、缩写、编号、单位、URL 等。
- 换行不得创建新的主编号或改变表格行列/合并结构。
- Section 2 H/EUH/P 专用逐条分行规则优先于本规则。
- Section 11、13、14 等长正文是重点人工检查区域。
- 双公司版本在公司字段归一化后，语义换行位置也必须一致。
- 任一明显应按 `。/；/;` 分行的连续正文仍挤在同一显示行，视为 release blocker。
