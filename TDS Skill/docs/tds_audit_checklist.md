# TDS 八格式审计清单

发布结果必须同时满足以下项目；任一 B0/B1 项失败即为 `RELEASE_FAIL`，机器通过只表示待用户校对。

| 类别 | 必检项 | 证据 |
|---|---|---|
| 包身份 | CN/EN × 冠志/国彩 四 DOCX + 四 PDF，文件名唯一；Word/PDF 与审计资料分目录 | `WORD/`、`PDF/`、`audit/`、`audit/release_report.json` |
| 模板基线 | 来源 `.doc`、来源 SHA-256、active `.docx`、geometry/package snapshot | `snapshots/template_baselines.json`、`mapping/template_field_registry.json` |
| 内容分层 | 原始 evidence、normalized semantic model、presentation value 三层分离；每个判断带 provenance、reason、confidence；未决客户含义判断阻断 | mapping `normalized_model` + `decision_ledger` |
| 受控覆写 | fresh clone；只改 registry/whitelist 值槽；既有序号、标签、表格、合并、grid width、段落/字符格式、段落/字符间距、页眉页脚不变；特性槽位无智能编号；新增性能行/特性只克隆模板样式 | generation record + geometry/feature-format audit |
| 事实保真 | 源文件一次抽取；每字段唯一映射；无冲突、无容量溢出、无模板示例事实泄漏 | source facts + mapping + leak audit |
| 翻译来源 | 英文 presentation value 来自 normalized model；英文源文件仅作证据/校验；事实、单位、范围和限定条件不被翻译改变 | normalized model + translation metadata |
| 语言/公司 | CN/EN 使用各自受控值；冠志/国彩使用各自模板骨架；不以另一变体替代 | registry + four-variant audit |
| PDF 派生 | 每个 PDF 与同名最终 DOCX 配对，转换前 DOCX 已审计，PDF 非独立制作 | PDF pair evidence |
| 视觉 QA | 每个 DOCX 至少渲染一页；检查截断、溢出、空白页、表格变形和公司标识 | rendered page images |
| 客户交付 | 完成自动测试、ZIP 完整性和用户校对 | release report + package manifest |
