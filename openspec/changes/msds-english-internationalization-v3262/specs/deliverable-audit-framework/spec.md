## MODIFIED Requirements

### Requirement: Template geometry and controlled mutation audit

输出 MUST 由当前维护 CN/EN 模板 fresh clone 产生，表格、行列、合并、grid widths、段落/字符属性、页眉页脚和锁定骨架 MUST 符合 snapshot/hash；修改 MUST 符合 mutation whitelist。英文活动模板的 hash/snapshot MAY differ from its preserved supplied-source template only through an explicitly versioned, reviewed template-remediation migration; the source-template identity MUST remain in the audit record.

#### Scenario: Geometry matches maintained baseline

- **WHEN** 输出结构快照与对应维护模板一致，且仅存在白名单允许的内容差异
- **THEN** geometry 和 mutation audit 通过并记录活动模板与源模板证据

#### Scenario: Locked skeleton is changed

- **WHEN** 输出改变序号列、标签列或其受保护格式属性
- **THEN** 审计器标记阻断并禁止发布

#### Scenario: English baseline remediation is traceable

- **WHEN** English output is generated from a corrected active baseline whose supplied source template is retained separately
- **THEN** audit evidence records both identities, verifies the active snapshot, and does not treat the approved baseline correction as an Agent runtime label mutation

### Requirement: Evidence-complete machine-readable audit report

每条规则 MUST 生成带 `rule_id`、`category`、`severity`、`status`、`source_of_truth`、`method`、`pass_condition`、`observed`、`evidence_paths` 和 `message` 的版本化证据记录；英文交付的中文残留、全角标点、术语/单位、模板污染和英文产品身份检查 MUST 各自有可定位结果；最终报告 MUST 同时支持 JSON 和人类阅读。

#### Scenario: Successful audit has complete evidence

- **WHEN** 一次完整审计运行结束
- **THEN** JSON 报告包含每个必需规则恰好一条结果、英文质量规则结果、分数、阻断项、outcome、输入身份和证据路径

#### Scenario: Audit execution is incomplete

- **WHEN** 必需规则因缺文件、工具错误或未执行而没有结果
- **THEN** 标记 `NOT_CHECKED` 或 `ERROR`，最终不得为 `RELEASE_PASS`

#### Scenario: English residual is detected

- **WHEN** 英文 DOCX 的正文、页眉或页脚包含中文字符、全角冒号或已知模板污染
- **THEN** 产生带文档部件和文本证据的阻断记录，且任何质量分数不得覆盖 `RELEASE_FAIL`
