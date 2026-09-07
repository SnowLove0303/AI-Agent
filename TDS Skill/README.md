# MSDS Skill / TDS Skill

仓库同时收纳两个独立 Skill：`MSDS Skill/` 处理 MSDS；`TDS Skill/` 处理 TDS。TDS 不复用 MSDS 业务代码，只有相同的工程质量要求：源事实保真、证据保留、语义标准化、Agent 判断、专业英文翻译、模板几何锁定、受控覆写、DOCX 派生 PDF、八文件包审计和用户校对门槛。

TDS 当前正式基线为四个用户提供的中英文/冠志国彩模板，版本 `1.3.10`。模板来源、active DOCX、注册表和结构快照均在本目录内留有证据。性能表数据行按源文件顺序保真写入，模板数据行只提供锁定样式；不足时裁剪未使用示例行，超出时按白名单克隆扩展。产品特性段落保留模板自动编号，输出统一采用紧凑悬挂式布局，编号和正文基准线由代码固定校正，空编号段不参与列表布局；英文输出统一使用标准技术章节标题和受控术语；每次产出将 Word 文件放入 `WORD`、PDF 文件放入 `PDF`，生成元数据和执行日志分别归档到 `audit/generation` 与 `audit/execution_logs`，并由 generation record 回链；产品 `output-dir` 必须位于技能仓库之外，产品 Word/PDF、审计资料、mapping 和日志不得加入、提交或推送到 Git；应用正文多行布局与序号清理的已验收参考实践见 `references/overwrite_practice_application_layout.md`；槽位和分隔段由注册表按 active 模板动态识别，扩展项插入原有分隔段之前。

TDS 的内容链路是“原始文档 → 证据账本 → 标准化 semantic model → 英文专业翻译/呈现判断 → 模板覆写”。程序提供可审计的候选归类和保守默认值，但不会把别名、历史案例或模板示例当成自动真相；客户含义相关的判断由 Agent 结合源文上下文完成，并在 decision ledger 中留下依据。
