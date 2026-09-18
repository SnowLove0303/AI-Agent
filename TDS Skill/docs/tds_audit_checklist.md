# TDS 八格式审计清单

发布结果必须同时满足以下项目；任一 B0/B1 项失败即为 `RELEASE_FAIL`，机器通过只表示待用户校对。

| 类别 | 必检项 | 证据 |
|---|---|---|
| 包身份 | CN/EN × 冠志/国彩 四 DOCX + 四 PDF，文件名唯一；Word/PDF 与审计资料分目录 | `WORD/`、`PDF/`、`audit/`、`audit/release_report.json` |
| 模板基线 | 来源 `.doc`、来源 SHA-256、active `.docx`、geometry/package snapshot | `snapshots/template_baselines.json`、`mapping/template_field_registry.json` |
| 内容分层 | 原始 evidence、normalized semantic model、presentation value 三层分离；每个判断带 provenance、reason、confidence；未决客户含义判断阻断 | mapping `normalized_model` + `decision_ledger` |
| 受控覆写 | fresh clone；只改 registry/whitelist 值槽；既有序号、标签、表格、合并、grid width、段落/字符格式、段落/字符间距、页眉页脚不变；特性槽位无智能编号；新增性能行/特性只克隆模板样式 | generation record + geometry/feature-format audit |
| 事实保真 | 源文件一次抽取；每字段唯一映射；无冲突、无容量溢出、无模板示例事实泄漏；中文源事实文件、字段和性能行哈希一致，生成 DOCX 逐字段/逐章节行/逐性能行一致 | source facts + mapping `source_fidelity` + source-output fidelity audit |
| 翻译来源 | 英文 presentation value 来自 normalized model；英文源文件仅作证据/校验；事实、单位、范围和限定条件不被翻译改变 | normalized model + translation metadata |
| 语言/公司 | CN/EN 使用各自受控值；冠志/国彩使用各自模板骨架；不以另一变体替代 | registry + four-variant audit |
| PDF 派生 | 先完成 DOCX preflight，再由内置 WPS/Word-compatible `word2pdf` 一对一转换；无 LibreOffice fallback、无独立 PDF 制作；source/output hash 与转换标志一致 | `audit/pdf_conversion/*.conversion.json` + `audit/release_report.json` |
| 视觉 QA | 每个 DOCX 至少渲染一页；检查截断、溢出、空白页、表格变形和公司标识 | rendered page images |
| 客户交付 | 完成自动测试、ZIP 完整性和用户校对 | release report + package manifest |
| 交付报告 | 每次构建后必须向用户报告输出根目录全路径 + `WORD/`/`PDF/` 八文件清单（路径+字节数）+ release report 路径与状态；构建命令尾部自动打印，不许省略 | `deliverables_root=`/`deliverable=`/`release_report=` 日志行 |
