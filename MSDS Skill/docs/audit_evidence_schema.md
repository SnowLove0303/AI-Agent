# MSDS 审计证据 Schema v1.0

审计输出必须同时生成 JSON 和人类可读 TXT。JSON 根对象至少包含 `schema_version`、`model`、`package_root`、`score`、`score_max`、`outcome`、`blockers`、`incomplete`、`evidence_errors` 和 `records`。

## Evidence record

每个 `records` 元素必须包含：

```json
{
  "rule_id": "S11-001",
  "category": "source_semantics",
  "severity": "NONE",
  "status": "PASS",
  "source_of_truth": "structured toxicology policy",
  "method": "controlled fixture replay",
  "pass_condition": "Existing toxicology is retained as structured source-grounded fields through 11.10",
  "observed": {"endpoints": ["11.3", "11.10"]},
  "evidence_paths": [".../matrix-report.json"],
  "message": "Section 11 structured-toxicology audit passed",
  "points_awarded": 3,
  "schema_version": "1.0"
}
```

必填字段：`rule_id`、`category`、`severity`、`status`、`source_of_truth`、`method`、`pass_condition`、`observed`、`evidence_paths`、`message`、`points_awarded`、`schema_version`。

允许的 `status`：`PASS`、`FAIL`、`NOT_CHECKED`、`ERROR`、`OBSERVED`。

允许的 `severity`：`B0`、`B1`、`B2`、`NONE`。

## 证据规则

- 每个已登记的 rule ID 在一次完整审计中恰好出现一次。
- PASS、FAIL、OBSERVED 必须有来源、方法、通过条件、消息和至少一个证据路径。
- NOT_CHECKED/ERROR 必须说明缺失输入或异常原因，并使最终结果不能为 `RELEASE_PASS`。
- `observed` 保存实际观测，不得只写“已检查”。
- 记录按 `rule_id` 排序，确保同一输入重复运行时报告稳定。
- evidence path 必须指向实际输入、报告、渲染结果或 ZIP，不得使用不存在的占位路径。
