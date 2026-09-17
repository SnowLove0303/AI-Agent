# 法律法规合格性检查报告

## 1. 报告信息

- 产品：`{{product_name}}`
- 报告日期：`{{generated_at}}`
- 判断模式：完整事实、闭世界
- 数据根目录：`{{data_root}}`

## 2. 输入事实与假设

| 字段 | 内容 |
|---|---|
| 销售国家/地区 | {{target_market}} |
| 最终用途 | {{final_use}} |
| 使用环境 | {{environment}} |
| 基材/成品 | {{substrates}} |
| 特殊要求 | {{special_requirements}} |

配方、CAS/EC、含量/迁移量以附件或输入 JSON 为准。未声明进入配方事实的物质，在闭世界假设下视为不存在；该假设不替代成品检测、供应链声明或法律意见。

## 3. 逐项判断

| 法律法规/标准 | 结果 | 适用性理由 | 命中物质/检测值 | 限值/单位/方法 | 证据 |
|---|---|---|---|---|---|
| {{standard}} | {{status}} | {{scope_reason}} | {{matches}} | {{limits}} | {{evidence}} |

## 4. 汇总

- 符合：`{{pass_count}}`
- 不符合：`{{fail_count}}`
- 不适用：`{{na_count}}`
- 需补证：`{{evidence_count}}`

## 5. 数据可复现信息

列出每个 CSV 的文件名、SHA-256、读取行数、数据版本字段以及脚本版本。
