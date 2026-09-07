# Evidence Log

## Entry Format
Each entry: `E-### | timestamp | action | result | status | ref`

## Entries

### E-001
- Time: 2026-09-04T08:29:28Z
- Action: `openspec context --json`; `git branch --show-current`; `git rev-parse HEAD`; `git remote -v`; `git status`
- Result: 唯一根为 `F:\APP Location\Guanzhi Tong\Skill\覆写技能\AI-Agent`；分支为 `feature/msds-tds-eight-format`；发布前工作区干净。
- Status: Verified
- Ref: `openspec/changes/build-tds-eight-format/`

### E-002
- Time: 2026-09-04T08:29:28Z
- Action: 读取四个用户模板并复制到 `TDS Skill/templates/source/`，转换为 active `.docx`，重建 registry/snapshot。
- Result: 四个来源 `.doc` 原样保留；四个 active 模板均为 1 表格、6 行、4 列；来源 hash 和 active hash 已登记。
- Status: Verified
- Ref: `TDS Skill/templates/source/`; `TDS Skill/templates/active/`; `TDS Skill/mapping/template_field_registry.json`; `TDS Skill/snapshots/template_baselines.json`

### E-003
- Time: 2026-09-04T08:29:28Z
- Action: 执行 `normalize_tds_template.py` 并运行特性格式测试。
- Result: 四套 active 模板的特性段落 21/23 均无 `numPr`；段落间距和字符间距签名一致；新增特性沿用模板段落样式。
- Status: Verified
- Ref: `TDS Skill/scripts/normalize_tds_template.py`; `TDS Skill/mapping/tds_mutation_whitelist.json`; `TDS Skill/snapshots/template_baselines.json`

### E-004
- Time: 2026-09-04T08:29:28Z
- Action: 运行 TDS 专项 pytest、全仓库 pytest、Skill quick validation、OpenSpec strict validation。
- Result: TDS `11 passed`；全仓库 `76 passed`；Skill valid；OpenSpec change valid。
- Status: Verified
- Ref: `TDS Skill/tests/`; `openspec/changes/build-tds-eight-format/`

### E-005
- Time: 2026-09-04T08:29:28Z
- Action: 按 manifest 构建 `TDS_Skill_v1.3.2-release.zip` 并执行 manifest/压缩包完整性检查。
- Result: `manifest_files=pass count=29`；`zip_integrity=pass entries=30`；旧版发布包保留。
- Status: Verified
- Ref: `TDS Skill/release/TDS_Skill_v1.3.2-release.zip`

### E-006
- Time: 2026-09-04T08:29:28Z
- Action: 用 PU-1001、PU-1002 真实 CN TDS 源执行 TDS CLI build、DOCX→PDF 和八格式审计，并渲染 PDF 进行视觉检查。
- Result: 每个样例生成 4 DOCX + 4 PDF；四变体 geometry 与 feature format 均 pass；因 CN-only、candidate model 和缺少 EN 事实，release report 正确为 `RELEASE_FAIL`。
- Status: Partial
- Ref: `TDS Skill/_work/replay-20260904/PU-1001/audit/release_report.json`; `TDS Skill/_work/replay-20260904/PU-1002/audit/release_report.json`

### E-007
- Time: 2026-09-04T08:29:28Z
- Action: fetch 远端同名分支，保留双方历史合并后执行全仓库测试并 push。
- Result: 远端分支已更新到 `54c6fee6a9ceffcfac80ba5782986346aac5e79c`；合并后全仓库 `76 passed`；工作区干净。
- Status: Verified
- Ref: `feature/msds-tds-eight-format`; remote `origin/feature/msds-tds-eight-format`

### E-008
- Time: 2026-09-04T08:29:28Z
- Action: `AIharness --version`; `AIharness validate --json`
- Result: Harness 版本为 `1.0.0`；校验仅对仓库既有非 managed 文档报告 `UNKNOWN_DOCUMENT`，未修改这些文档。
- Status: Partial
- Ref: `AGENTS.md`; `ARCHITECTURE.md`; `docs/`

### E-009
- Time: 2026-09-04T08:37:23Z
- Action: 解析指定 Wiki 节点，读取现状，使用 `docs +update --command block_replace` 写入交接正文，再更新 Wiki 标题并回读全文。
- Result: Wiki 节点 `BcpFwKXsVi6Ar9k9k2McuXshnkb` 已更新到 revision 15；标题为 `MSDS/TDS 项目交接文档 1.3.2`；正文包含项目基线、交付包、模板契约、审计结果、阻断和接手命令。
- Status: Verified
- Ref: `https://xcnch7esppuf.feishu.cn/wiki/BcpFwKXsVi6Ar9k9k2McuXshnkb`

### E-010
- Time: 2026-09-04T08:38:52Z
- Action: 回读飞书交接页后，将页面中的 HEAD 记录更新为 handoff state commit，并再次读取关键词范围。
- Result: 页面 revision 16 已更新为 revision 17；页面标题、最新 HEAD、代码基线和接手正文均可回读。
- Status: Verified
- Ref: `https://xcnch7esppuf.feishu.cn/wiki/BcpFwKXsVi6Ar9k9k2McuXshnkb`

### E-011
- Time: 2026-09-04T08:38:52Z
- Action: 修正飞书页面中的证据索引，并用 keyword fetch 验证。
- Result: 页面显示证据范围为 E-001 至 E-009，标题为 `MSDS/TDS 项目交接文档 1.3.2`，revision 17。
- Status: Verified
- Ref: `https://xcnch7esppuf.feishu.cn/wiki/BcpFwKXsVi6Ar9k9k2McuXshnkb`

### E-012
- Time: 2026-09-07T09:45:00+08:00
- Action: 在唯一根执行 `openspec context --json`，核对 Git branch/HEAD/remote/status。
- Result: OpenSpec 根为 `F:\APP Location\Guanzhi Tong\Skill\覆写技能\AI-Agent`，当前分支 `feature/msds-tds-eight-format`，MSDS v3.14.2 功能基线为 `fbcdd958547b090ce74c5c5bb39298842062bc53`；交接复核时工作区为 clean，当前 HEAD 为该基线之后的仓库历史。
- Status: Verified
- Ref: `openspec/context`; `git status --short`; `git log`; `git remote -v`

### E-013
- Time: 2026-09-07T09:50:00+08:00
- Action: 完整读取 `agent-handoff-kit/SKILL.md`、`references/state-schemas.md`、`references/workflow.md`，并按 TASK_STATE → HANDOFF → DECISIONS → 最新 EVIDENCE 顺序恢复既有状态。
- Result: 确认本次需要维护四个本地交接状态文件，并将之前的 TDS 交接历史保留为历史证据，当前交接切换为 MSDS 专属范围。
- Status: Verified
- Ref: `C:\Users\Administrator\.codex\skills\agent-handoff-kit\SKILL.md`; `TASK_STATE.md`; `HANDOFF.md`

### E-014
- Time: 2026-09-07T09:58:00+08:00
- Action: `py -m pytest -q "MSDS Skill/tests"`; `py -X utf8 ...quick_validate.py "MSDS Skill"`。
- Result: MSDS `65 passed`；Skill quick validation 输出 `Skill is valid!`。默认 quick validation 的 GBK 解码路径曾失败，使用 UTF-8 模式后通过；该问题属于外部校验器兼容性，不是 Skill 内容失败。
- Status: Verified
- Ref: `MSDS Skill/tests/`; `MSDS Skill/SKILL.md`

### E-015
- Time: 2026-09-07T10:02:00+08:00
- Action: 执行 `audit_v29_inheritance.py`、CN `audit_template_geometry.py`、EN `audit_template_geometry.py`。
- Result: v2.9 继承审计通过，检查 37 个 legacy files；CN/EN geometry 均通过，均为 16 表，且哈希与 v3.14 快照一致。
- Status: Verified
- Ref: `MSDS Skill/legacy_v2_9/`; `MSDS Skill/tests/template_geometry_v314.json`; `MSDS Skill/tests/template_geometry_en_v314.json`

### E-016
- Time: 2026-09-07T10:04:00+08:00
- Action: 核对 `MSDS Skill/_task_work/replay_v313_final/OS-9015/` 和 `PU-2345/` 的 matrix-report、deliverable-audit、八文件审计结果。
- Result: 两个历史回放均为 4 DOCX + 4 PDF、4 个 formal-ready、0 个 draft、无 shared blocker；已有报告 score=100、outcome=`RELEASE_PASS`。这些是历史回放证据，不替代当前 v3.14.2 新回放和人工逐页 QA。
- Status: Verified with scope caveat
- Ref: `MSDS Skill/_task_work/replay_v313_final/OS-9015/`; `MSDS Skill/_task_work/replay_v313_final/PU-2345/`

### E-017
- Time: 2026-09-07T10:08:00+08:00
- Action: 使用 `lark-cli wiki +node-get` 和 `lark-cli docs +fetch --doc-format xml --detail full` 读取目标 Wiki。
- Result: 节点 `BCuhwr1GviyJubkYWcscvFIynaf`、文档 token `R8VxdD0oqoRlcaxu0cecT7Pdn1b` 已确认；原正文只有标题 `MSDS` 和空白段落，revision=3。
- Status: Verified
- Ref: `https://xcnch7esppuf.feishu.cn/wiki/BCuhwr1GviyJubkYWcscvFIynaf`

### E-018
- Time: 2026-09-07T10:18:00+08:00
- Action: 通过 `lark-cli docs +update --command block_replace --doc-format xml` 写入完整 MSDS 交接正文，使用 `drive +update-title` 更新标题，再用 `docs +fetch` 回读。
- Result: 标题为 `MSDS 项目交接文档 v3.14.2`；revision=5；正文长度约 15,171 字符；MSDS/TDS 隔离、CN/EN 哈希、Section 2/3/8/9/11/14、`build_eight.py` 和下一步均核验命中。
- Status: Verified
- Ref: `https://xcnch7esppuf.feishu.cn/wiki/BCuhwr1GviyJubkYWcscvFIynaf`

### E-019
- Time: 2026-09-07T10:19:00+08:00
- Action: `AIharness --version`; `AIharness validate --json`。
- Result: Harness=1.0.0；对仓库既有 `AGENTS.md`、`ARCHITECTURE.md` 和 `docs/` 非 managed 文档报告 `UNKNOWN_DOCUMENT`。没有为绕过该结果而改写项目级文档或建立第二套体系。
- Status: Partial / tool-layer finding
- Ref: `AGENTS.md`; `ARCHITECTURE.md`; `docs/`

### E-020
- Time: 2026-09-07T10:22:00+08:00
- Action: `py C:\Users\Administrator\.codex\skills\agent-handoff-kit\scripts\check_state.py --strict`。
- Result: state files strict check 完成，0 error、0 warning；仅提示 TASK_STATE 存在 4 项 open risks，均已明确记录 mitigation 或 unblock 条件。
- Status: Verified
- Ref: `TASK_STATE.md`; `HANDOFF.md`; `DECISIONS.md`; `EVIDENCE_LOG.md`

### E-021
- Time: 2026-09-07T10:25:00+08:00
- Action: 复核实际 `git status --short` 后，使用 Feishu `str_replace` 修正线上交接页和本地交接文件中关于 TDS 工作区状态的过时描述。
- Result: 工作区最终为 clean；线上页面保留 MSDS-only 交接边界，revision=6；不再把不存在的 TDS 未提交修改写成风险，且未修改 MSDS 代码、模板或产出规则。
- Status: Verified
- Ref: `https://xcnch7esppuf.feishu.cn/wiki/BCuhwr1GviyJubkYWcscvFIynaf`; `TASK_STATE.md`; `HANDOFF.md`

## Last Updated
2026-09-07T10:25:00+08:00 · Codex · MSDS handoff session
