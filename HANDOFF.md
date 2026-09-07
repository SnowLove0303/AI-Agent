# Handoff

## Project Identity
- Project name: MSDS Unified Eight-Deliverable Standardizer Skill
- Project root: `F:\APP Location\Guanzhi Tong\Skill\覆写技能\AI-Agent`
- MSDS root: `MSDS Skill/`
- Active MSDS version: `3.14.2`
- Branch: `feature/msds-tds-eight-format`
- MSDS v3.14.2 functional baseline: `fbcdd958547b090ce74c5c5bb39298842062bc53` — `Release MSDS Skill v3.14.2 with formal top-level 8.2 rows and parameterized pipeline`
- Code HEAD audited for this handoff: `037e57214861983f76bee6ce821a57a8b28102e0` — later TDS-only commit; do not use it as evidence of a new MSDS behavior change. The handoff state files are committed separately after this audit.
- Remote: `origin https://github.com/SnowLove0303/AI-Agent.git`
- Worktree: clean at final verification; TDS remains an independent Skill and is outside this MSDS handoff.
- Runtime / entry point: `py "MSDS Skill/scripts/build_eight.py" --source SRC.docx --facts MODEL.json --out OUTPUT_DIR`
- Feishu handoff: `https://xcnch7esppuf.feishu.cn/wiki/BCuhwr1GviyJubkYWcscvFIynaf`
- Feishu title/revision at handoff: `MSDS 项目交接文档 v3.14.2`, revision `7`
- State files: `TASK_STATE.md`, `HANDOFF.md`, `DECISIONS.md`, `EVIDENCE_LOG.md`

## Resume In <30 Seconds
1. Read `TASK_STATE.md` → active MSDS goal, evidence, risks and current `[~]` replay step.
2. Read this file → MSDS-only boundary, version baseline and immediate next action.
3. Read `DECISIONS.md` → fixed separation, semantic pipeline, template and PDF decisions.
4. Skim the latest entries in `EVIDENCE_LOG.md` → tests, template audits and Feishu write proof.
5. Read `MSDS Skill/SKILL.md` and `MSDS Skill/docs/` before touching any source or template.

## Context The Next Agent Must Know

本页只交接 MSDS。仓库中虽然存在独立的 TDS Skill，但其代码、模板、事实、产物和交接规则均不属于本项目；交接复核时工作区为 clean，TDS 不能作为 MSDS 证据，也不能进入 `MSDS Skill/`。

MSDS v3.14.2 已把用户模板、哈希、几何快照、受控覆写白名单、语义模型、Section 2/3/8/9/11/14 规则、独立 CN/EN 语言层、DOCX-first PDF、release blockers 和八文件审计固化在 Skill 文档与脚本中。所有客户产品仍需按当前源文档重新抽取、判断、生成和逐页验收。

## Immediate Next Step
针对一个真实 MSDS 源文档，以 `MSDS Skill` v3.14.2 重新执行完整 DOCX-first 八格式回放：先生成/审核 approved semantic model，再运行 `build_eight.py` 生成四个独立模板 DOCX，执行 locked skeleton、whitelist、geometry、Section 2/3/8/9/11/14、semantic/company parity 和逐页 DOCX QA；所有 gates 通过后，才用唯一转换器从这四个最终 DOCX 派生四个 PDF，并逐页核对 DOCX/PDF 一致性。该事项对应 `TASK_STATE.md` 的 `[~]` 项。

## MSDS Architecture That Must Not Drift
- 单一语义链：source facts → normalized semantic model → omission/mapping → CN/EN language layer → Guanzhi/Guocai company overlay → DOCX → audits → render QA → DOCX-derived PDF。
- 四个 DOCX 以各自语言模板 fresh clone；CN 与 EN 不能互相重建，不能从 CN 输出复制生成 EN。
- PDF 只能由最终审计 DOCX 一对一派生；不能单独编写、修订或重新排版 PDF。
- Agent 负责原文语义判断、Section 2/11 归类、缺失与不适用区分、专业翻译和决策记录；程序负责机械写入、模板结构保持、审计、转换和证据生成。

## MSDS Template Baseline
- CN active: `MSDS Skill/examples/template_reference.docx`; SHA-256 `2e4f55086bb13de9caa9e933465fad55eb62efc785d595170bc65749a2de6cfc`。
- EN source: `MSDS Skill/examples/template_reference_en_source.docx`; SHA-256 `59445b62c6d33b25a2e04c05778d428656f1ce0cbe7c21212721b145468c4416`。
- EN active: `MSDS Skill/examples/template_reference_en.docx`; SHA-256 `59445b62c6d33b25a2e04c05778d428656f1ce0cbe7c21212721b145468c4416`。
- CN rows: `[10,16,6,6,5,4,3,16,24,6,18,6,3,5,9,2]`; EN rows: `[9,16,6,6,5,4,3,16,24,6,18,6,3,5,9,2]`; both have 16 tables.
- Section 8 contains Hand protection and formal 8.2 Engineering controls; Section 11 extends through 11.10 Additional information; Section 2 contains the revised pictogram/label structure.
- Archived v3.10–v3.13 templates remain rollback/audit evidence only. Template examples such as PEA-4139, example ingredients, hazards, toxicology/ecology and OEL rows are not product facts.

## MSDS Content and Mutation Contract
- Default locked: sequence column, label column, table/row/column topology, merges, grid widths, borders, row heights, headers/footers, page fields, paragraph properties and run properties.
- Allowed mutations: verified source value cells; whole semantic note slots; one component per Section 3 physical row; source-grounded Section 8.2 data rows; source pictogram in the existing slot; whole pure-missing rows under approved Section 2/9 rules; continuous renumbering after permitted omission.
- Section 3: exactly one component per physical row. Never pack multiple names/CAS/concentrations into one row.
- Missing data: customer-facing exact values are `无数据` or `No data available`; never `无数据资料`, `源文件未提供`, `源文件记载` or equivalent provenance commentary.
- Section 2: show source-grounded pictograms; label elements use a line-separated required-hazardous-ingredients tip; no `见2.4-2.6`/`See 2.4-2.6`; pure missing rows are removed and visible numbers are continuous.
- Section 8.2: preserve parent/header geometry; CN header `物质 / 依据 / 类型 / 数值`, EN header `Substance / Basis / Type / Value`; example OEL rows must be replaced or reduced to the exact missing-value policy.
- Section 9: omit pure missing property rows and renumber; retain substantive negative results, `不适用`/`Not applicable`, measured values and substantive Other information.
- Section 11: preserve endpoint → study block → structured field → value hierarchy; do not infer method/species/classification/overall assessment/similar-product study; map verified source alias `主要粘膜刺激性` to existing `11.3 主要眼睛刺激性` without inventing a new conclusion or duplicating into 11.10.
- Section 14: UN number, proper shipping name, hazard class, packing group and special precautions appear on separate logical lines.

## QA and Release Decision
- Audit order: identity/eight-file → source/semantic → template hash/geometry/whitelist → special sections → CN/EN and company parity → DOCX visual → PDF lineage/preflight/page QA → v2.9/manifest/ZIP/evidence → score/blockers.
- B0 blocks immediately: missing/duplicate matrix files, no template lineage, locked skeleton/geometry mutation, PDF not derived from final DOCX.
- B1 blocks: wrong facts or mapping, example leakage, Section 2/3/8/9/11/14 violation, parity or visual error, v2.9/manifest/release audit failure.
- B2 is a recorded minor issue and never overrides B0/B1.
- `RELEASE_PASS` requires no B0/B1, complete required evidence and score ≥95/100. Otherwise use `RELEASE_FAIL` or `NOT_READY`.

## Verified Evidence at Handoff
- 65 MSDS pytest tests passed; UTF-8 Skill quick validation passed.
- v2.9 inheritance audit passed: 37 legacy files checked; only approved wrapper/enhancement differences.
- CN and EN v3.14 geometry audits passed with the pinned hashes and row baselines above.
- Existing OS-9015 and PU-2345 replay directories each contain 4 DOCX + 4 PDF and their historical matrix/deliverable audit reports show score 100 and `RELEASE_PASS`. Treat them as historical replay evidence until a current v3.14.2 end-to-end replay and manual page QA is completed.
- AIharness is 1.0.0, but `AIharness validate --json` reports `UNKNOWN_DOCUMENT` for pre-existing non-managed repository docs; this was recorded, not silently changed.

## Do NOT
- Do not add TDS content, TDS templates, TDS facts or TDS mappings to `MSDS Skill/`.
- Do not modify user source templates to probe a fix; create active baselines only through the documented provenance process.
- Do not use an illustrative template fact, another product, another language or an unapproved candidate model to fill a missing value.
- Do not mix TDS code, templates, facts or outputs into MSDS; re-check the clean worktree before future MSDS changes.
- Do not declare a customer deliverable from an unreviewed candidate model, stale replay, failed audit or a PDF that was not derived from the final DOCX.

## Handoff From / To
From: Codex · 2026-09-07 · MSDS handoff session
To: Project maintainer / next MSDS Agent
