---
name: legal-compliance-judgment
description: "仅根据完整且确定的 MSDS/TDS 物质成分事实，对 REACH、POPs、RoHS、HSF、BSBL 等物质限制清单做可追溯基础筛查并生成 PDF 报告；特殊用途法规作为后续扩展，不审查 MSDS 文件本身、包装或市场准入。"
compatibility: "Python 3.10+；法规数据根目录默认为 F:\\APP Location\\Guanzhi Tong\\法律法规物质清单，可用 --data-root 或 GUANZHI_TONG_LEGAL_DATA_ROOT 覆盖。"
---

# 法律法规判断技能

本技能只把 MSDS/TDS 和物质成分信息作为输入事实，不审查 MSDS 文件排版、标签或内容质量。资料边界是强制的“完整信息源”契约：资料未提到的物质视为不存在，不要求用户补充该物质报告，也不因为缺少市场、用途、包装或客户信息而停在不确定。默认先运行“物质成分基础筛查”，条件单仅作为后续特殊用途扩展参考。

## 工作方式

1. 从 MSDS/TDS 提取物质字段：物质名称、CAS/EC、配方浓度以及资料中明确提供的测量事实。销售市场、最终用途、包装和客户标准不属于基础筛查必需输入。
2. 初始化或刷新知识库：`scripts/legal_compliance_db.py refresh --db legal_compliance.db --data-root <root>`；技能目录中的 `legal_compliance.db` 是由当前法规资料生成的可刷新基线。
3. 将事实写成 JSON，使用 `--standards auto --db <path>`，先运行固定的物质成分基础层；如确实需要条件单扩展，再显式使用 `--standards condition-auto` 或指定标准列表。
4. 基础层固定检查 REACH SVHC、REACH Annex XVII、REACH Annex XIV 触发筛查、EU POPs 2019/1021 触发筛查、RoHS 物质筛查、HSF 001、BSBL 和 91/338/EC，不使用市场、用途、包装或客户条件排除它们。
5. 对选中的法规逐项输出 `符合（基于完整成分资料）`、`不符合` 或 `不适用`。严格模式下，缺少可比较检测值、限值文本不可解析或单位不可换算时仍按完整资料假设完成判断，并在证据栏记录闭世界处理，不向用户索要新的物质报告。
6. 只有用户明确开启 `--allow-uncertainty`、在 facts 中设置 `allow_uncertainty: true`，或在固定法规模式中明确点名一个没有可执行来源的客户标准时，才允许输出 `需补证`。
7. 每次判断必须生成并校验书面 PDF；JSON/Markdown 只是可选中间文件，不能替代 PDF，也不能只用口头摘要交付。报告必须包含命中的物质、匹配键、检测值、限值/单位、源文件及行号、数据状态、知识库运行 ID 和闭世界假设。

## 示例

```powershell
python scripts/legal_compliance_judge.py `
  --facts facts.json `
  --standards auto `
  --db legal_compliance.db `
  --data-root "F:\APP Location\Guanzhi Tong\法律法规物质清单" `
  --format markdown `
  --output PU-1002_法律法规合格性检查报告.md `
  --output-pdf PU-1002_法律法规合格性检查报告.pdf
```

若不需要中间 Markdown，可省略 `--format` 和 `--output`，但 `--output-pdf` 始终必填。PDF 由临时 DOCX 经 LibreOffice 转换后，再由脚本检查页数和可提取文本；转换或校验失败即返回失败，不会把未生成的 PDF 宣称为交付物。

首次使用先构建数据库：

```powershell
python scripts/legal_compliance_db.py init `
  --db legal_compliance.db `
  --data-root "F:\APP Location\Guanzhi Tong\法律法规物质清单"
```

数据库保存法规身份、别名、适用条件、参考源、版本、外部 CSV 派生限制规则、每次判断运行和人工反馈。法规目录位于 `references/regulation_catalog.json`；初始目录只是种子，可新增法规而不修改判断器代码。数据库中的限制规则是可重建缓存，外部法规目录仍是权威源；刷新后报告中的源文件哈希和版本随之更新。

`facts.json` 至少应包含 `product_name`、`components` 和 `assume_complete: true`。`target_market`、`final_use`、`environment`、`substrates`、`special_requirements` 在基础物质成分筛查中不是必填项。每个配方组分应尽量包含 `name`、`cas`、`ec`、`concentration`；如资料中有物质测量数据，放入 `measurements`。

## 数据边界

数据只从外部规范目录读取，不复制到技能仓库：

- `法律法规物质限制清单_CSV导出`：REACH SVHC、REACH Annex XVII、RoHS、HSF 001、BSBL、AfPS GS 2019:01 PAK。
- `欧盟玩具`：2009/48/EC、玩具化学修订及解释指南的来源登记。当前 PU 原料未声明玩具用途时，玩具法规为 `不适用`；声明玩具用途但尚无结构化限值时，严格模式按完整资料边界完成结果并记录处理路径；仅在用户开启不确定性或明确要求证据审查时才为 `需补证`。

法规名称、适用范围和参考源集中在数据库目录中。`auto` 只运行物质成分基础层；玩具、建筑、包装、BPR 和客户标准等特殊项目需使用 `condition-auto` 或显式标准列表，且不影响基础层报告。对于 Annex XIV 和 EU POPs，当前本地知识库登记了官方参考源；如果尚无结构化本地物质行，报告会标明 `catalog-only`，不会要求用户提供新的 MSDS/TDS。

脚本会先统一可比较的 `%`、`ppm`、`mg/kg` 数值，再应用限值；配方百分比不会与迁移量或面积限值直接比较。严格模式下真正不兼容的量纲会记录为闭世界处理并完成 `符合/不符合` 判定；只有显式不确定性模式才保留 `需补证`。本技能的结论是物质成分筛查，不等同于最终产品、包装或市场准入结论。

