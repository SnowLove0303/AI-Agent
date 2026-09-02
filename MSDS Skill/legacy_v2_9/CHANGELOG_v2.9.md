# v2.8
- 将用户新确认的 `模板_MSDS_CN_冠志(3).docx` 纳入内置模板并设为最高结构基线。
- 更新模板 SHA-256、表格行数快照与结构回归基线。
- 修正 Section 15 基线说明：当前模板保留 `物质或混合物的相关安全、健康和环保法律法规` 行。
- 锁定新版 Section 11 的 6 行多列/合并单元格结构与 Section 2 的 16 行结构。
- 冠志/国彩双版本继续共享该新模板，仅允许公司资料白名单差异。

# v2.7
- 修复编号审计对 python-docx/lxml 段落对象使用 `id()` 导致合法行被误跳过的问题。
- 编号审计改为按“唯一主项目”连续性检查，允许 11.1 经口/经皮/吸入等连续重复子行。
- 增加源语义子项顺序门禁：同一主项目内保持源 MSDS 顺序。
- 规定 `--audit-only` 非零即禁止交付。
- 新增 HPU-7660 回归场景：Section 2 删除首项后必须为 2.1/2.2；Section 11 急性毒性顺序为经口/经皮/吸入。

# Changelog

## 2.6.0
- Added default dual-output mode: `CN_冠志` + `CN_国彩`.
- Added Guocai supplier/contact/footer profile.
- Added whitelist-only company-profile overlay rule.
- Added cross-variant parity QA and release blocking on unauthorized differences.
- Added `company_profile_policy.py` and regression tests.
- Fixed skill metadata/version to 2.6.0.

# v2.5
- Added Section 11 exception: preserve complete source-level toxicology availability statements such as “该产品无可用的毒理学研究。” while still suppressing bare missing-data placeholders and unsupported endpoints.
- Added QA/regression expectation for EP-1704 Section 11.


## 2.4.0
- Added mandatory Guanzhi product-identity placement policy.
- `1.1 产品名称` value is intentionally blank by default; product model must not be written there.
- `中文名称` now requires `中文产品名称 + single ASCII space + 产品型号` (e.g. `水性环氧乳液 EP-1704`).
- Header/title product-code and footer MSDS identifier retain the model according to template convention.
- Added proactive identity QA so Agents must catch this before delivery instead of waiting for user correction.
- Added `product_identity_policy.py` and regression tests.


## 2.3.0
- Added mandatory post-omission continuous renumbering for all surviving `N.x` items.
- Clarified that only the numeric prefix is mutable; label wording and formatting remain locked.
- Added child-item exclusions so labels such as 吸入/食入/经口/经皮 and H/P lines never consume parent numbers.
- Added numbering continuity release gate and required operation order.
- Added `renumber_visible_items.py` helper and numbering regression tests.


## 2.2.0
- Replaced the built-in Guanzhi MSDS template with the user-designated latest template `模板_MSDS_CN_冠志(2).docx`.
- Made the bundled `examples/template_reference.docx` the default authoritative template when no newer approved template is explicitly supplied.
- Pinned the new template by SHA-256 and structural baseline in `docs/template_baseline.md`.
- Updated Section 15 baseline: the latest template has 9 rows and removes the older standalone `物质或混合物的相关安全、健康和环保法律法规` row. Agents must not reintroduce it from older files.
- Required regeneration of `tests/template_snapshot.json` whenever the built-in template changes.

## 2.1.0
- Changed display policy: missing-data placeholders (“无数据”“无数据资料”“暂无数据”“无可用数据”“无适用资料”等) are omitted as complete items.
- Clarified that “不适用” and substantive negative conclusions are not automatically suppressed.
- Added Section 2 semantic line wrapping: one complete H/EUH statement per line and one complete P statement per line when multiple statements exist.
- Added parser/formatter helper and regression tests for H/P splitting and missing-data classification.

## v2.9
- 新增正文 Sentence Boundary Line-Break Policy。
- 中文 `。`、`；` 与英文 `;` 后默认语义换行，标点保留在上一行。
- 禁止机械拆分 ASCII `.`，保护小数、缩写、编号、单位、URL。
- 明确语义换行不新增编号/表格行，使用同段落 Word line break，不产生空段落。
- 新增 `scripts/sentence_boundary_policy.py` 和回归测试。
- QA 增加 Section 11/13/14 长正文换行门禁及双公司换行一致性检查。
