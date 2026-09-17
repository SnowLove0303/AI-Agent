---
name: legal-compliance-judgment
description: "根据完整且确定的 MSDS/TDS 产品事实，对 REACH、RoHS、HSF、BSBL、AfPS 及玩具/中国标准等法律法规和客户限制清单做可追溯合格性检查，并生成报告矩阵。用户提到法规合规、物质限制清单、MSDS/TDS 法律法规判断或合格性报告时使用。"
compatibility: "Python 3.10+；法规数据根目录默认为 F:\\APP Location\\Guanzhi Tong\\法律法规物质清单，可用 --data-root 或 GUANZHI_TONG_LEGAL_DATA_ROOT 覆盖。"
---

# 法律法规判断技能

本技能把 MSDS/TDS 中已经确认的事实转换为可复现的法规判断。默认使用“完整事实、闭世界”模式：未出现在已知配方事实中的物质不作为未知物质；法规范围由产品市场、最终用途、使用环境、基材/成品和特殊要求判定。该假设必须在报告中明确列出。

## 工作方式

1. 从 MSDS/TDS 提取条件单字段：销售市场、最终用途、使用环境、基材/成品、配方及 CAS/EC、成品含量或迁移量、特殊客户要求。
2. 将事实写成 JSON，运行 `scripts/legal_compliance_judge.py`。
3. 对用户给出的全部法规逐项输出四种结果之一：`符合（基于完整资料假设）`、`不符合`、`不适用`、`需补证`。
4. 报告必须包含每项法规的适用性理由、命中的物质、限值/单位/测试方法、源文件及行号、数据版本和闭世界假设。

## 示例

```powershell
python scripts/legal_compliance_judge.py `
  --facts facts.json `
  --standards standards.json `
  --data-root "F:\APP Location\Guanzhi Tong\法律法规物质清单" `
  --format markdown `
  --output PU-1002_法律法规合格性检查报告.md
```

`facts.json` 至少应包含 `product_name`、`target_market`、`final_use`、`environment`、`substrates`、`components`、`special_requirements` 和 `assume_complete: true`。每个配方组分应尽量包含 `name`、`cas`、`ec`、`concentration`；如有成品检测数据，放入 `measurements`。

## 数据边界

数据只从外部规范目录读取，不复制到技能仓库：

- `法律法规物质限制清单_CSV导出`：REACH SVHC、REACH Annex XVII、RoHS、HSF 001、BSBL、AfPS GS 2019:01 PAK。
- `欧盟玩具`：2009/48/EC、玩具化学修订及解释指南的来源登记。当前 PU 原料未声明玩具用途时，玩具法规为 `不适用`；声明玩具用途但尚无结构化限值时为 `需补证`，不得冒充已完成玩具检测。

标准名、适用范围和结果规则集中在脚本中；客户代号（例如 Mattel RMS2901、QSOP、SRS、QA056、SS00259、TQS）没有可执行限值时只能 `需补证`。

