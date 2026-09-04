# Decisions

## Format
`D-### | decision | rationale | alternatives | date`

## Log

### D-001
- Decision: MSDS 与 TDS 维持两个独立 Skill 目录、映射、程序、模板和测试体系。
- Rationale: 两类文档的业务结构不同，但可以共享工程质量要求；混合会让模板和事实边界失控。
- Alternatives considered: 合并为一个 Skill — rejected because it violates the established project boundary and increases cross-template mutation risk.
- Date: 2026-09-04T08:29:28Z
- Supersedes: none

### D-002
- Decision: 覆写链路固定为原始文档 → 证据账本 → normalized semantic model → 专业英文翻译/呈现判断 → 模板 fresh clone 覆写。
- Rationale: 原始事实、标准化判断和最终呈现必须可追溯且可区分，英文不能绕过标准化层直接机械翻译。
- Alternatives considered: 直接把源文档文字写入模板 — rejected because it loses semantic decisions and creates language/format drift.
- Date: 2026-09-04T08:29:28Z
- Supersedes: none

### D-003
- Decision: 每个输出从对应 active 模板 fresh clone 产生，PDF 只由最终 DOCX 派生。
- Rationale: 模板决定版式，DOCX 是唯一内容主件，PDF 只能作为同一内容的派生文件。
- Alternatives considered: 独立生成或重新排版 PDF — rejected because it causes DOCX/PDF asymmetry.
- Date: 2026-09-04T08:29:28Z
- Supersedes: none

### D-004
- Decision: 最新四个模板的 active 基线仅清除特性槽位残留智能编号，保留源 `.doc` 原件和其他模板属性。
- Rationale: 用户明确取消了特性智能编号；直接保留残留 `numPr` 会导致输出显示自动序号，但修改源文件会破坏模板 provenance。
- Alternatives considered: 修改用户源 `.doc`；删除整个 numbering part；统一重设全篇间距 — rejected because each would alter provenance or unrelated layout.
- Date: 2026-09-04T08:29:28Z
- Supersedes: none

### D-005
- Decision: CN-only 或 candidate normalized model 的回放只能作为诊断/校对产物，必须阻断客户发布。
- Rationale: 缺少 EN 事实或未完成 Agent 判断时，自动补译/补事实会制造客户风险。
- Alternatives considered: 复制中文到 EN；使用模板示例值；忽略 release blocker — rejected because each violates source-fact and language parity requirements.
- Date: 2026-09-04T08:29:28Z
- Supersedes: none

## Last Updated
2026-09-04T08:37:23Z · Codex · session-20260904-tds-handoff
