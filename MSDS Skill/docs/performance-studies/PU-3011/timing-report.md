# PU-3011 MSDS 全流程计时试跑报告

## 状态

**部分完成，阻塞在正式 preflight。** 已完成冷启动抽取、事实审阅、模板映射、双语翻译和 150 条双语 trace。通用 workflow 最终有 2 个 preflight blockers，故未克隆模板、未启动 PDF 转换，本次没有产出 4 DOCX + 4 PDF。

源文件及试跑目录中的只读并排副本 SHA-256 均为 `074ee9974b23984b3f089223541a4dfe78ff9c952772c7dd8afe0adb10814808`；未修改原件，也未写产品登记表。

## 时间核算

起点 `2026-09-28T07:46:43Z`，终点 `2026-09-28T08:28:38Z`，总墙钟 **2,515 秒（41 分 55 秒）**。

| 类别 | 秒 | 口径 |
|---|---:|---|
| Machine / 明确计时调用 | 15.107 | 抽取器、preflight/workflow、计时事实/追溯 JSON 与哈希/文件核验等已计时工具调用 |
| Agent review | 未单独计量 | 没有 active-time telemetry；不能当作 0 |
| Wait | 0 | 没有显式等待 |
| Retry | 67.142 | 初次 Python 路由至 LibreOffice 内嵌 Python，缺 Tk 后改 `py -3.12`；恢复调用另计 machine 0.858s |
| Unknown / 未归属 | 2,432.751 | 总墙钟减已计 machine、retry、wait；含无法分离的审阅、决策、工具间隔及时间空档 |
| **核对** | **2,515.000** | `15.1068313 + 67.142 + 0 + 2432.7511687 = 2515` |

`Agent review` 未测量，属于 unknown 的潜在组成部分，不能另加一次。OpenSpec 规范检查和源清点有 35 秒重叠，已按任务墙钟只算一次。`08:09:09–08:14:54 UTC` 的 345 秒明确计入 unknown；所有推断不到的时段均未算作活跃审阅时间。

### 关键阶段

| 阶段 | UTC 墙钟窗口 | 结果与已量时间 |
|---|---|---|
| 源清点、hash、副本 | 07:46:43–07:47:18 | 35s；机时未单独测 |
| OpenSpec/技能规范检查 | 07:46:43–07:50:20 | 217.025s；与源清点重叠 |
| 错误 Python 路由恢复 | 07:47:18–07:48:26 | 68s（machine 0.858 + retry 67.142） |
| 冷启动 GUI 抽取 | 07:50:20.025–07:50:20.874 | machine 0.849s；268/268 units、16 张正文表、2 图、201 facts、unmapped=0 |
| 初审 + 首次 preflight | 07:50:20.874–08:00:47.684 | 626.809s；281 blockers；active review 未量 |
| 映射修复及 EN 草稿 | 08:00:47.684–08:03:58 | 190.317s；blockers 281→223→215 |
| EN S1–S4 | 08:05:11–08:07:15 | 124s elapsed；34行，translation review 131→108；活跃/机时无法拆分 |
| EN S5–S9 | 08:07:15–08:08:33 | ≤78s文件时间上界；translation review 108→65 |
| EN S10–S16 | 08:08:33–08:09:09 | 36s；translation review 65→0；S16单行双单元格 |
| 双语 trace S1–S16 | 08:14:54–08:21:20.786 | 386.786s；150 mapped facts ↔ 150 trace，S9另有8项纯无数据隐藏决定；machine 3.7s |
| 完整 trace 后 preflight 第1轮 | 08:22:49–08:23:02.035 | 7 blockers |
| trace/mapping 修复 | 08:23:02.035–08:23:54.435 | 52.400s；7→3 |
| line-break policy 修复 | 08:23:54.435–08:24:37.821 | 43.386s；3→2 |
| 最终 workflow preflight | 08:24:40–08:24:52.856 | 2 blockers；build 未启动 |
| source hash/输出状态核对 | 08:24:52.856–08:28:38 | 225.144s；副本 hash 一致、无 output 文件夹 |

## Preflight blockers 和修复历程

正式报告依次为：`preflight-first.json` 281；`preflight-mapping-repair.json` 223；`preflight-mapping-repair-2.json` 215；`preflight-bilingual-first.json` 333；完整 trace 的 generic workflow 首轮 7；修复后 3；最终 2。333 个问题当时包含 151 mapped 无 trace、117 EN 源依据失败、38 Agent execution 记录、14 S2 router trace、13 其他项。追溯补齐后，这些内容/映射问题均通过，仅剩以下两项。

## 不能继续生成 DOCX/PDF 的实际限制

活动校验器 [agent_execution_contract.py](C:/Users/Administrator/.codex/skills/MSDS%20Skill/scripts/agent_execution_contract.py#L100) 第 100–108 行要求 `overwrite_sop.status == reviewed`，stage 清单须匹配完整的 10 阶段并且**每阶段状态均为 completed**；其中含 `clone_template_and_write_values`、`suppress_empty_rows_and_renumber`、`audit_and_render_qa`。

通用工作流 [run_efficiency_workflow.py](C:/Users/Administrator/.codex/skills/MSDS%20Skill/scripts/run_efficiency_workflow.py#L159) 第 159–160 行先跑 preflight，第 171–184 行未通过即返回 `PREFLIGHT_BLOCKED` / `build.not_started`，第 186–190 行才会启动 builder。因此它要求 clone/write/QA 完成后才能通过 clone 前的门禁。当前只能如实记录前 6 阶段完成、后 4 阶段未启动；填成 completed 会是虚报。

**影响：** 不虚报阶段、不绕 preflight、不修改 validator 时，通用流程无法克隆模板，因此本次没有 DOCX/PDF 成品或渲染 QA。最终 blocker 原文为 `overwrite_sop status must be reviewed` 和 `overwrite_sop every required stage must be completed`。

## 文件与核验

- `evidence-packet.json`：本次冷启动抽取；268/268 units，未映射0，201条初始事实；未借用旧 facts/输出做内容来源。
- `facts-model-reviewed-bilingual.json`：150/150 mapped facts 有唯一 trace；EN trace 均标记 `approved_translation` 和 `translation_reviewed=true`；Section 2 分路完整；Section 9 pH 1%条件已追溯、表面张力未加原文不存在的 10% 条件，离子性/水溶性/粘度/其他信息保持分行；8个纯无数据行有隐藏决定。
- `preflight.json`：blocked，2 errors；`workflow-state.json`：`preflight_blocked`，build `not_started`。
- 原件和 `source/PU-3011 msds_CN 冠志.docx` 只读副本 hash 相同。根目录无 `output`，递归仅发现只读源副本 DOCX 1份、PDF 0份。
- 时间明细、阶段 event、未归属区间和 blocker 计数见同目录 `timing-ledger.json`。
