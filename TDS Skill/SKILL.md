---
name: tds-four-variant-eight-deliverable-standardizer
description: Independent source-grounded TDS overwriting for CN/EN × Guanzhi/Guocai, producing four DOCX and four DOCX-derived PDF deliverables.
metadata:
  version: 1.2.0
  short-description: TDS Skill — one semantic model, four maintained templates, eight auditable files
---

# TDS Skill

本 Skill 只处理 TDS，和 `MSDS Skill` 独立：不导入、不读取、不写入 MSDS 的模板、语义模型、快照、规则或产出目录。

## 固定边界

- 四个独立模板变体：中文/英文 × 冠志/国彩。
- 每个变体都从自己的 active `.docx` fresh clone 后原位覆写；不跨变体套模板。表格表头、列宽、合并、边框和样式来自模板；性能表数据行按源文件顺序写入，未使用的模板示例行裁剪，超出容量才克隆模板数据行追加；产品特性按原有段落样式追加。
- 一次源文件抽取形成一个 semantic model，再映射到四个变体；字段不明确、数据冲突或模板容量不足时 fail closed。
- 模板中的产品名、性能指标、示例数值和公司事实是结构样例，不是产品事实。
- 只允许修改 `mapping/tds_mutation_whitelist.json` 声明的值槽位；表头、表格拓扑、合并、grid widths、段落/字符属性、页眉页脚和包部件受保护。性能数据行的项目标签是源事实值槽位，标签格式受保护；不得用模板示例标签替换源标签。
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

缺少英文源数据时英文槽位不会复制中文或模板示例；输出仅可作为审计失败的诊断结果。构建后报告位于 `<output-dir>/audit/release_report.json`。
