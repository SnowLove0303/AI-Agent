# MSDS Skill / TDS Skill

当前 TDS Skill 发布版本为 `1.3.24`；本版本新增中文源事实忠实度哈希与生成后阻断门禁。

仓库同时收纳两个独立 Skill：`MSDS Skill/` 处理 MSDS；`TDS Skill/` 处理 TDS。TDS 不复用 MSDS 业务代码，只有相同的工程质量要求：源事实保真、证据保留、语义标准化、Agent 判断、专业英文翻译、模板几何锁定、受控覆写、DOCX 派生 PDF、八文件包审计和用户校对门槛。

TDS 当前正式基线为四个用户提供的中英文/冠志国彩模板，版本 `1.3.24`。模板来源、active DOCX、注册表和结构快照均在本目录内留有证据。严格模板模式下，所有内容只能写入 registry 已注册的值槽；标题、段落/字符格式、缩进、间距、编号、制表位和表格框架均以 active 模板为唯一权威。正文中间空段只按 registry 的 `body_blank_trim` 规则收束，章节末行到下一标题的垂直过渡由 `inter_section_spacing` 规则统一；英文正文仅在内容超过垂直预算时按 `english_vertical_budget` 规则压缩行距；这些规则均不得改变字体、字号、首行缩进、编号、制表位或表格框架。文本覆写只替换现有 Run 的文字节点，保留模板的 Run 与属性结构，不使用 `p.text` 或强制字体/字号注入；内容超出既有槽位时，只能深拷贝 registry 指定的模板段落或表格行完整格式，再替换文字，禁止自动重设版式。性能表格允许按源数据声明的 2-col、3-col、4-col 合法拓扑收敛，但列宽与结构必须由 registry 授权，不能自由设计；英文正文恢复模板规定的首字双空，产品特性继续使用模板编号和悬挂缩进。英文输出统一使用标准技术章节标题和受控术语；每次产出先写入最终 Word，再由内置 WPS/Word-compatible `word2pdf` 转换器派生 PDF，严禁独立制作 PDF；Word 文件放入 `WORD`、PDF 文件放入 `PDF`，生成元数据、执行日志和 PDF 转换证据分别归档到 `audit/generation`、`audit/execution_logs` 和 `audit/pdf_conversion`；产品 `output-dir` 必须位于技能仓库之外，产品 Word/PDF、审计资料、mapping 和日志不得加入、提交或推送到 Git；PDF 发布契约见 `docs/pdf_publication_contract.md`。

TDS 的内容链路是“原始文档 → 证据账本 → 标准化 semantic model → 英文专业翻译/呈现判断 → 模板覆写”。程序提供可审计的候选归类和保守默认值，但不会把别名、历史案例或模板示例当成自动真相；客户含义相关的判断由 Agent 结合源文上下文完成，并在 decision ledger 中留下依据。
中文源事实属于只读内容：映射会保存源事实文件、字段和性能行哈希；中文覆写直接继承 `source_values`，禁止用 `normalized_values` 改写中文。DOCX 生成后会逐字段、逐章节行和逐性能行回读核验，发现词序、术语、数值、单位、测试条件或免责声明变化即阻断 PDF 转换和交付包发布。仅允许登记的列表序号剥离、外层空白收束和段落拆分。
