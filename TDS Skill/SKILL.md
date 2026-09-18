---
name: tds-four-variant-eight-deliverable-standardizer
description: Extract, normalize, professionally translate, and overwrite TDS content into CN/EN × Guanzhi/Guocai templates, producing four DOCX and four DOCX-derived PDF deliverables with auditable judgment evidence.
metadata:
  version: 1.3.24
  short-description: TDS Skill — evidence-led normalization, agent judgment, four refreshed templates, eight auditable files
---

# TDS Skill

本 Skill 只处理 TDS，和 `MSDS Skill` 独立：不导入、不读取、不写入 MSDS 的模板、语义模型、快照、规则或产出目录。

## 核心工作方式

覆写不是把源文件文字机械塞进固定字段，而是以下五段闭环：

```text
原始文档抽取 → 原始证据账本 → 事实整理与语义标准化 → 专业英文翻译/呈现判断 → 模板原位覆写与审计
```

- 原始抽取结果是不可丢失的证据；`source_values`、原文标签、限定条件、原始位置和原始文件 hash 必须保留。
- 标准化结果是面向输出的统一 semantic model；字段要记录 provenance、判断理由、置信度和是否需要人工/Agent 判断。英文使用 `normalized_values`；中文必须直接继承带哈希证据的 `source_values`，两者不一致时 fail closed。
- 英文输出必须从标准化模型进行专业技术翻译，不得把中文模板示例、另一产品事实或未经判断的逐字替换当作翻译。已有英文源文件可以作为目标语言证据和校验材料，但不改变“标准化模型 → 英文呈现”的来源链。
- 模板、强标注框架、检索要求、覆写要求和白名单是硬约束；别名表、历史案例、段落位置和模板示例只是候选线索，不是无条件规则。
- 模板严格性门禁：每个字段只能写入 active 模板已注册的值槽；任何标题居中、缩进/间距重置、编号/制表位重写或非模板形状的重排都属于越权格式修改，禁止自动执行。正文中间空段只允许按 registry 的 `body_blank_trim` 规则收束，英文正文空间预算只允许按 registry 的 `english_vertical_budget` 规则触发；这两项均不得改动字体、字号、首行缩进、编号、制表位或表格框架。槽位容量不足时，只能按 registry 的扩展规则深拷贝对应模板段落/表格行的完整格式，再写入新增值；不得为了“排好看”修改模板框架。
- 文本覆写只允许修改现有 Run 的文字节点；禁止使用 `p.text = ...`、强制注入字体/字号、把多 Run 内容粗暴倒入固定 Run 后丢弃其余格式，或用任何格式归一化函数重建段落。每个模块必须从对应模板的原始文字 Run 中选择格式锚点，保留全部 `pPr`/`rPr`/Run 节点结构；新增内容只能深拷贝对应模板单元后替换文字。
- active 模板本身的版式就是唯一权威。若模板示例标题看起来偏右，Skill 不得擅自删除模板缩进或强制居中；应保留原模板版式并把“模板基线需人工修订”作为独立问题提出。只有用户另行确认模板变更，才能更新 active 模板与 registry。
- 具体抽取边界、归类、合并/拆分、单位与限定条件保留方式、术语选择和英文句法由 Agent 根据上下文、源证据和目标变体判断。若存在会改变客户含义的多种解释，保留原始证据并标记 `needs_judgment`；未解决前不得发布。
- 中文内容忠实度门禁：映射记录源事实文件、文本字段和性能行 SHA-256；覆写前校验中文源值与标准化值一致并直接写入源值，生成后逐字段、逐章节行、逐性能行回读 DOCX。发现词序、术语、数值、单位、测试条件或免责声明变化时，阻断 DOCX 后的 PDF 转换和交付包发布；仅允许登记的列表序号剥离、外层空白收束和段落拆分。

执行源文件、翻译或覆写任务前，读取 `references/agent_judgment_protocol.md`。它规定判断顺序和证据格式，不替代 Agent 对具体内容的专业判断。

`references/overwrite_practice_application_layout.md` 用于诊断正文换行问题；多行普通正文可按 registry 规则深拷贝对应模板正文段落，保持完整段落/字符格式，只替换文字，不得重设缩进或间距。

## 固定边界

- 四个独立模板变体：中文/英文 × 冠志/国彩。
- 每个变体都从自己的 active `.docx` fresh clone 后原位覆写；不跨变体套模板。表格表头、列宽、合并、边框和样式来自模板；性能表数据行、产品特性和普通正文扩展只允许按 registry 已声明的规则深拷贝既有模板行/段落，新增内容只能替换文字。
- 一次源文件抽取形成一个包含原始证据和标准化值的 semantic model，再映射到四个变体；字段不明确、数据冲突、翻译判断未解决或模板容量不足时 fail closed。
- 模板中的产品名、性能指标、示例数值和公司事实是结构样例，不是产品事实。
- 只允许修改 `mapping/tds_mutation_whitelist.json` 声明的值槽位；表头、表格拓扑、合并、grid widths、段落/字符属性、段落/字符间距、段落编号、页眉页脚和包部件受保护。性能数据行的项目标签是源事实值槽位，标签格式受保护；不得用模板示例标签替换源标签。
- 产品特性优先使用 registry 已注册的现有段落槽位；超出时按 `feature_extension` 深拷贝 registry 指定的模板特性段落，保留每个 active 模板原有的自动编号、缩进、制表位、间距和空白分隔段。源文本中的手工序号只去除显示性前缀；扩展段落不得调用任何格式归一化函数。
- PDF 只能由相应的最终 DOCX 通过内置 `scripts/convert_docx_to_pdf.py` 的 WPS/Word-compatible `word2pdf` 适配器派生；严格执行“先完成 Word，再转 PDF”，禁止 LibreOffice fallback、独立排版 PDF、PDF 后编辑或任何 PDF 内容分支。转换前必须通过 DOCX preflight，转换后必须用 source/output hash、converter version、page count 和 `independent_pdf_authoring=false` 证据完成配对审计。
- 机器审计通过只代表 `ready_for_user_proofreading`，不自动宣称客户可交付。
- 机器审计必须把 active 模板与输出的段落/字符/表格形状逐项比对；允许的例外只有值槽文本替换、registry 声明的同形状段落/数据行克隆、经 decision ledger 批准的整段隐藏、registry 声明的正文空段收束，以及 registry 声明的英文垂直预算。新增段落/行的形状不是对应模板槽位的完整克隆，或标题样式、编号、缩进、字体、字号和制表位被重设时必须 `RELEASE_FAIL`；垂直预算也不得改动字体、字号和首行/悬挂缩进。
- 产品产出物与技能仓库严格隔离：Word、PDF、`audit`、mapping、generation record、覆写执行日志及其他产品级中间文件必须写入仓库外的独立 `output-dir`；不得将产品产出物执行 `git add`、提交或推送。若目标 `output-dir` 位于技能仓库内，必须先停止并改用仓库外路径；仓库只允许收录技能代码、测试、规范、文档及用户明确要求发布的技能版本包。

## 四变体与八文件

`TDS_CN_冠志模板`、`TDS_CN_国彩模板`、`TDS_EN_冠志模板`、`TDS_EN_国彩模板` 各自产出一个 DOCX 和一个同名 PDF。性能表使用模板的数据行样式，但事实以源表为准：保留源文件每一行的项目标签、限定条件、指标值、单位和测试方法；模板没有的源指标按原顺序追加，模板有但源文件没有的示例行不写入。产品特性基线有两个段落，更多特性按原有段落样式追加，超过映射容量或无法一一对应时 fail closed。

## 使用

```text
py scripts/register_tds_registry.py
py scripts/snapshot_tds_templates.py
py scripts/tds_cli.py build --source-cn <cn.doc|cn.docx> --source-en <en.doc|en.docx> --model <MODEL> --output-dir <output-dir>
```

该命令第一次运行会生成 `audit/mapping.json`（`normalized_model.status=candidate`）。Agent 完成事实整理、标准化和英文翻译后，将同一 mapping 的标准化值、decision ledger 和状态提升为 `approved`，再用 `--normalized-mapping <approved-mapping.json>` 重跑构建；这样不重复抽取，也不绕过同一套模板、白名单、PDF 和审计链路。

缺少英文源数据时英文槽位不会复制中文或模板示例；若 Agent 已从标准化模型完成专业英文翻译，应将翻译后的 `normalized_values` 作为覆写输入并保留中文标准化值与 provenance。没有完成翻译判断的输出仅可作为审计失败的诊断结果。构建顺序固定为“Word 覆写 → DOCX preflight → 内置 Word/WPS 转 PDF → PDF 证据审计 → 视觉复核”。产出固定分层：`<output-dir>/WORD/*.docx`、`<output-dir>/PDF/*.pdf`、`<output-dir>/audit/generation/*.generation.json`、`<output-dir>/audit/execution_logs/*.overwrite.log.json`、`<output-dir>/audit/pdf_conversion/*.conversion.json`，发布报告位于 `<output-dir>/audit/release_report.json`；`<output-dir>` 必须位于技能仓库之外，产品产出不得进入 Git 仓库。详细契约见 `docs/pdf_publication_contract.md` 和 `docs/pdf_converter_adoption.md`。
