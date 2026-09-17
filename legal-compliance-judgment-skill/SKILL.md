---
name: legal-compliance-judgment
description: "根据完整且确定的 MSDS/TDS 产品事实，对 REACH、RoHS、HSF、BSBL、AfPS 及玩具/中国标准等法律法规和客户限制清单做可追溯合格性检查，并生成报告矩阵。用户提到法规合规、物质限制清单、MSDS/TDS 法律法规判断或合格性报告时使用。"
compatibility: "Python 3.10+；法规数据根目录默认为 F:\\APP Location\\Guanzhi Tong\\法律法规物质清单，可用 --data-root 或 GUANZHI_TONG_LEGAL_DATA_ROOT 覆盖。"
---

# 法律法规判断技能

本技能把 MSDS/TDS 中已经确认的事实转换为可复现的法规判断。默认使用“完整事实、闭世界”模式：未出现在已知配方事实中的物质不作为未知物质；法规范围由条件单中的产品市场、最终用途、使用环境、基材/成品、配方和特殊要求判定。法规不再固定为 40 项，先从本地 SQLite 法规知识库选择适用法规，再执行物质限制检查。该假设必须在报告中明确列出。

## 工作方式

1. 从 MSDS/TDS 提取条件单字段：销售市场、最终用途、使用环境、基材/成品、配方及 CAS/EC、成品含量或迁移量、特殊客户要求。
2. 初始化或刷新知识库：`scripts/legal_compliance_db.py refresh --db legal_compliance.db --data-root <root>`；技能目录中的 `legal_compliance.db` 是由当前法规资料生成的可刷新基线。
3. 将事实写成 JSON，使用 `--standards auto --db <path>`，由条件单自动选择法规；只有用户明确指定时才使用固定标准列表兼容模式。
4. 对选中的法规逐项输出四种结果之一：`符合（基于完整资料假设）`、`不符合`、`不适用`、`需补证`。
5. 报告必须包含法规选择理由、命中的物质、匹配键、检测值、限值/单位/测试方法、源文件及行号、数据版本、知识库运行 ID 和闭世界假设。

## 示例

```powershell
python scripts/legal_compliance_judge.py `
  --facts facts.json `
  --standards auto `
  --db legal_compliance.db `
  --data-root "F:\APP Location\Guanzhi Tong\法律法规物质清单" `
  --format markdown `
  --output PU-1002_法律法规合格性检查报告.md
```

首次使用先构建数据库：

```powershell
python scripts/legal_compliance_db.py init `
  --db legal_compliance.db `
  --data-root "F:\APP Location\Guanzhi Tong\法律法规物质清单"
```

数据库保存法规身份、别名、适用条件、参考源、版本、外部 CSV 派生限制规则、每次判断运行和人工反馈。法规目录位于 `references/regulation_catalog.json`；40 项只是初始种子，可新增法规而不修改判断器代码。数据库中的限制规则是可重建缓存，外部法规目录仍是权威源；刷新后报告中的源文件哈希和版本随之更新。

`facts.json` 至少应包含 `product_name`、`target_market`、`final_use`、`environment`、`substrates`、`components`、`special_requirements` 和 `assume_complete: true`。每个配方组分应尽量包含 `name`、`cas`、`ec`、`concentration`；如有成品检测数据，放入 `measurements`。

## 数据边界

数据只从外部规范目录读取，不复制到技能仓库：

- `法律法规物质限制清单_CSV导出`：REACH SVHC、REACH Annex XVII、RoHS、HSF 001、BSBL、AfPS GS 2019:01 PAK。
- `欧盟玩具`：2009/48/EC、玩具化学修订及解释指南的来源登记。当前 PU 原料未声明玩具用途时，玩具法规为 `不适用`；声明玩具用途但尚无结构化限值时为 `需补证`，不得冒充已完成玩具检测。

法规名称、适用范围和参考源集中在数据库目录中；客户代号（例如 Mattel RMS2901、QSOP、SRS、QA056、SS00259、TQS）只有在条件单的特殊要求中被引用才会被自动选中，没有可执行限值时只能 `需补证`。

脚本会先统一可比较的 `%`、`ppm`、`mg/kg` 数值，再应用限值；配方百分比不会与迁移量或面积限值直接比较。这样在完整事实已经提供检测值时，单位差异不会制造无意义的 `需补证`，而真正不兼容的量纲仍会保留为 `需补证`。

