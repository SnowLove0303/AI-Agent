# 法律法规合格性检查报告

## 1. 报告信息

- 产品：`{{product_name}}`
- 报告日期：`{{generated_at}}`
- 判断模式：物质成分基础筛查、完整事实、闭世界
- 不确定性策略：{{uncertainty_mode}}
- 数据根目录：`{{data_root}}`
- 法规知识库：`{{database_path}}`
- 判断运行 ID：`{{run_id}}`

## 2. 输入事实与假设

| 字段 | 内容 |
|---|---|
| 销售国家/地区 | {{target_market}} |
| 最终用途 | {{final_use}} |
| 使用环境 | {{environment}} |
| 基材/成品 | {{substrates}} |
| 特殊要求 | {{special_requirements}} |

配方、CAS/EC、浓度和资料中明确提供的测量事实以给定资料或输入 JSON 为准。所有给定资料视为完整、确定且唯一的信息源；未声明进入配方事实的物质，在闭世界假设下视为不存在，不要求补充该物质报告。除非人为开启不确定性，否则缺少可比较值的规则也按完整资料假设输出符合/不符合。本报告不审查 MSDS 文件本身、包装、最终产品、迁移/均质材料、市场、用途或客户准入。

## 3. 基础物质成分法规选择

| 法律法规/标准 | 是否纳入基础筛查 | 选择理由 | 数据状态 | 参考源/版本 |
|---|---|---|---|---|
| {{candidate_standard}} | {{candidate_applicable}} | {{candidate_reason}} | {{candidate_source_status}} | {{candidate_source}} |

## 4. 逐项判断

| 法律法规/标准 | 结果 | 筛查层/数据状态 | 范围说明 | 命中物质/匹配键 | 检测值/限值/单位 | 源文件/行号/方法 | 证据 |
|---|---|---|---|---|---|---|---|
| {{standard}} | {{status}} | {{screening_tier}} / {{source_status}} | {{scope_reason}} | {{matches}} | {{measurements_and_limits}} | {{source_row_and_method}} | {{evidence}} |

## 5. 汇总

- 符合：`{{pass_count}}`
- 不符合：`{{fail_count}}`
- 不适用：`{{na_count}}`
- 需补证：`{{evidence_count}}`（仅显式不确定性或固定模式点名缺少来源的标准允许出现）

## 6. 数据可复现信息

列出每个 CSV 的文件名、SHA-256、读取行数、数据版本字段以及脚本版本。

## 7. 书面交付

本模板的最终交付物必须是已校验的 PDF。JSON/Markdown 仅作为可选机器可读中间文件；没有 PDF 时不得以口述摘要替代报告。
