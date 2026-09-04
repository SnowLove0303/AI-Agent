# Handoff

## Project Identity
- Project name: MSDS/TDS 覆写技能统一仓库
- Project root: `F:\APP Location\Guanzhi Tong\Skill\覆写技能\AI-Agent`
- Repository root: `F:\APP Location\Guanzhi Tong\Skill\覆写技能\AI-Agent`
- Project type: Python document-processing Skills and auditable DOCX/PDF build pipelines
- Active subproject: `TDS Skill/`
- Branch: `feature/msds-tds-eight-format`
- HEAD: `54c6fee6a9ceffcfac80ba5782986346aac5e79c` — merge remote TDS/MSDS branch history
- Worktree: clean
- Runtime / entry point: `py "TDS Skill/scripts/tds_cli.py" build --source-cn <cn.doc|cn.docx> --source-en <en.doc|en.docx> --model <MODEL> --output-dir <output-dir>`
- State files: `TASK_STATE.md`, `HANDOFF.md`, `DECISIONS.md`, `EVIDENCE_LOG.md`
- Feishu handoff: `https://xcnch7esppuf.feishu.cn/wiki/BcpFwKXsVi6Ar9k9k2McuXshnkb`（revision 17）

## Resume In <30 Seconds
1. Read `TASK_STATE.md` → goal, progress and blockers.
2. Read this file → immediate next step and boundaries.
3. Read `DECISIONS.md` → fixed architecture and release choices.
4. Skim the last five entries of `EVIDENCE_LOG.md` → verification proof.

## Immediate Next Step
人工逐页检查 `TDS Skill/_work/replay-20260904/PU-1001/` 与 `PU-1002/` 下的最终 DOCX/PDF；确认内容、分页、表格、特性间距和 CN/EN 对齐后，补齐 EN 专业翻译，把同一 `audit/mapping.json` 的 `normalized_model.status` 提升为 `approved`，再运行：

```text
py "TDS Skill/scripts/tds_cli.py" build --normalized-mapping <approved-mapping.json> --model <MODEL> --output-dir <output-dir>
```

这对应 `TASK_STATE.md` 中的 `[~]` 人工校对/approved mapping 项。

## Context The Next Agent Must Know
- TDS v1.3.2 发布包位于 `TDS Skill/release/TDS_Skill_v1.3.2-release.zip`；四个 `.doc` 来源在 `TDS Skill/templates/source/`，active `.docx` 在 `TDS Skill/templates/active/`。
- 产品特性两个基线槽位为段落 21/23，当前 active 模板禁止 `numPr`；段落/字符间距由模板定义，新增特性只能克隆模板段落。
- EN 国彩模板的应用/储存内容位置与其他模板不同，registry 已按模板固定标题检索，不得恢复为跨模板硬编码位置。
- 性能行遵循 source-led 顺序；模板示例事实不能泄漏到输出。缺失语言事实必须阻断正式发布。
- 旧版本发布包保留；本次不清理、不覆盖、不改写用户原始模板。

## Do NOT
- 不把 TDS 规则、模板或事实写入 `MSDS Skill/`，反之亦然。
- 不独立重做 PDF；先完成最终 DOCX，再用唯一转换模块派生 PDF。
- 不修改 `templates/source/` 中的用户原始 `.doc`；active baseline 只允许执行已记录的特性编号归一化。
- 不把 `RELEASE_FAIL` 的 CN-only/candidate 回放产物宣称为客户可交付物。
- 不使用模板示例数据、另一产品数据或另一语言内容填补缺失事实。

## Open Risks Handed Over
- 真实回放尚未具备客户发布资格，详见 `TASK_STATE.md` blocker 和 `EVIDENCE_LOG.md` E-006。
- `AIharness validate --json` 的既有 `UNKNOWN_DOCUMENT` 记录仍存在，详见 E-008；不要未经 OpenSpec 变更擅自重构仓库文档体系。

## Handoff From / To
From: Codex @ 2026-09-04T08:38:52Z
To: 项目维护者 / 下一位 Agent
