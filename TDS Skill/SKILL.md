---
name: tds-four-variant-eight-deliverable-standardizer
description: Extract, normalize, professionally translate, and overwrite TDS content into CN/EN × Guanzhi/Guocai templates, producing four DOCX and four DOCX-derived PDF deliverables with auditable judgment evidence.
metadata:
  version: 1.3.6
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
- 标准化结果是面向输出的统一 semantic model；字段要记录 provenance、判断理由、置信度和是否需要人工/Agent 判断。`normalized_values` 才是最终覆写输入。
- 英文输出必须从标准化模型进行专业技术翻译，不得把中文模板示例、另一产品事实或未经判断的逐字替换当作翻译。已有英文源文件可以作为目标语言证据和校验材料，但不改变“标准化模型 → 英文呈现”的来源链。
- 模板、强标注框架、检索要求、覆写要求和白名单是硬约束；别名表、历史案例、段落位置和模板示例只是候选线索，不是无条件规则。
- 具体抽取边界、归类、合并/拆分、单位与限定条件保留方式、术语选择和英文句法由 Agent 根据上下文、源证据和目标变体判断。若存在会改变客户含义的多种解释，保留原始证据并标记 `needs_judgment`；未解决前不得发布。

执行源文件、翻译或覆写任务前，读取 `references/agent_judgment_protocol.md`。它规定判断顺序和证据格式，不替代 Agent 对具体内容的专业判断。

## 固定边界

- 四个独立模板变体：中文/英文 × 冠志/国彩。
- 每个变体都从自己的 active `.docx` fresh clone 后原位覆写；不跨变体套模板。表格表头、列宽、合并、边框和样式来自模板；性能表数据行按源文件顺序写入，未使用的模板示例行裁剪，超出容量才克隆模板数据行追加；产品特性按原有段落样式追加。
- 一次源文件抽取形成一个包含原始证据和标准化值的 semantic model，再映射到四个变体；字段不明确、数据冲突、翻译判断未解决或模板容量不足时 fail closed。
- 模板中的产品名、性能指标、示例数值和公司事实是结构样例，不是产品事实。
- 只允许修改 `mapping/tds_mutation_whitelist.json` 声明的值槽位；表头、表格拓扑、合并、grid widths、段落/字符属性、段落/字符间距、段落编号、页眉页脚和包部件受保护。性能数据行的项目标签是源事实值槽位，标签格式受保护；不得用模板示例标签替换源标签。
- 当前四个模板的产品特性槽位保留模板自动编号，但输出统一采用紧凑悬挂式列表：编号起点与正文首行基准线对齐，编号起点固定为 400 twips、正文起点固定为 560 twips、悬挂量固定为 160 twips，编号后使用普通空格而不是远距离制表位。空白分隔段不得带 `numPr`、tab 或列表缩进；新增特性插入到原有分隔段之前。registry 按模板标题和实际特性段落动态注册槽位，覆写不得硬编码段落位置；源文本中的手工序号只去除显示性前缀。
- PDF 只能由相应的最终 DOCX 通过 `scripts/convert_docx_to_pdf.py` 派生；禁止独立排版 PDF。
- 机器审计通过只代表 `ready_for_user_proofreading`，不自动宣称客户可交付。

## 四变体与八文件

`TDS_CN_冠志模板`、`TDS_CN_国彩模板`、`TDS_EN_冠志模板`、`TDS_EN_国彩模板` 各自产出一个 DOCX 和一个同名 PDF。性能表使用模板的数据行样式，但事实以源表为准：保留源文件每一行的项目标签、限定条件、指标值、单位和测试方法；模板没有的源指标按原顺序追加，模板有但源文件没有的示例行不写入。产品特性基线有两个段落，更多特性按原有段落样式追加，超过映射容量或无法一一对应时 fail closed。

## 使用

```text
py scripts/register_tds_registry.py
py scripts/snapshot_tds_templates.py
py scripts/tds_cli.py build --source-cn <cn.doc|cn.docx> --source-en <en.doc|en.docx> --model <MODEL> --output-dir <output-dir>
```

该命令第一次运行会生成 `audit/mapping.json`（`normalized_model.status=candidate`）。Agent 完成事实整理、标准化和英文翻译后，将同一 mapping 的标准化值、decision ledger 和状态提升为 `approved`，再用 `--normalized-mapping <approved-mapping.json>` 重跑构建；这样不重复抽取，也不绕过同一套模板、白名单、PDF 和审计链路。

缺少英文源数据时英文槽位不会复制中文或模板示例；若 Agent 已从标准化模型完成专业英文翻译，应将翻译后的 `normalized_values` 作为覆写输入并保留中文标准化值与 provenance。没有完成翻译判断的输出仅可作为审计失败的诊断结果。构建后报告位于 `<output-dir>/audit/release_report.json`。
