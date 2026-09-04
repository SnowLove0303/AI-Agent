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

## Last Updated
2026-09-04T08:37:23Z · Codex · session-20260904-tds-handoff
