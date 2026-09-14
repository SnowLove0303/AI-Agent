# MSDS Skill / TDS Skill

仓库同时收纳两个独立 Skill：`MSDS Skill/` 处理 MSDS；`TDS Skill/` 处理 TDS。TDS 不复用 MSDS 业务代码，只有相同的工程质量要求：源事实保真、证据保留、语义标准化、Agent 判断、专业英文翻译、模板几何锁定、受控覆写、DOCX 派生 PDF、八文件包审计和用户校对门槛。

TDS 当前正式基线为四个用户提供的中英文/冠志国彩模板，版本 `1.3.18`。模板来源、active DOCX、注册表和结构快照均在本目录内留有证据。严格模板模式下，所有内容只能写入 registry 已注册的值槽；标题、段落/字符格式、缩进、间距、编号、制表位、空白分隔段和表格框架均以 active 模板为唯一权威。文本覆写只替换现有 Run 的文字节点，保留模板的 Run 与属性结构，不使用 `p.text` 或强制字体/字号注入；内容超出既有槽位时，只能深拷贝 registry 指定的模板段落或表格行完整格式，再替换文字，禁止自动重设版式。英文输出统一使用标准技术章节标题和受控术语；每次产出先写入最终 Word，再由内置 WPS/Word-compatible `word2pdf` 转换器派生 PDF，严禁独立制作 PDF；Word 文件放入 `WORD`、PDF 文件放入 `PDF`，生成元数据、执行日志和 PDF 转换证据分别归档到 `audit/generation`、`audit/execution_logs` 和 `audit/pdf_conversion`；产品 `output-dir` 必须位于技能仓库之外，产品 Word/PDF、审计资料、mapping 和日志不得加入、提交或推送到 Git；PDF 发布契约见 `docs/pdf_publication_contract.md`。

TDS 的内容链路是“原始文档 → 证据账本 → 标准化 semantic model → 英文专业翻译/呈现判断 → 模板覆写”。程序提供可审计的候选归类和保守默认值，但不会把别名、历史案例或模板示例当成自动真相；客户含义相关的判断由 Agent 结合源文上下文完成，并在 decision ledger 中留下依据。
