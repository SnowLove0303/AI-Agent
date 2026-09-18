---
name: legal-compliance-judgment
description: "严格按照《检测报告模板》格式出具法规检测报告（DOCX与校验合格PDF），固定只做六项核心法规与受限物质清单（REACH SVHC 253项、REACH Annex XVII、RoHS、HSF 001、BSBL、AfPS GS 2019:01 PAK），未经要求的其他法规不做；自动使用红黄绿状态高亮、物质明细、总结与双酚/邻苯特殊说明。"
compatibility: "Python 3.10+；法规数据根目录默认为 F:\\APP Location\\Guanzhi Tong\\法律法规物质清单；检测报告模板位于 F:\\APP Location\\Guanzhi Tong\\Skill\\法律法规判断\\检测报告模板。"
---

# 法律法规判断技能

本技能专门针对 MSDS/TDS 物质成分事实出具专业合规检测报告。**严格按照官方《检测报告模板》排版输出（包括 DOCX 和由其转换校验的 PDF），并且严格聚焦于核心六项法规与受限清单，绝不堆砌冗余未要求的法规或无关分析。**

## 核心六项检测清单（固定做这六项，其余不要求不做）

| 序号 / 监管体系 | 法规/标准全称与说明 | 权威源 CSV 数据文件 |
| :--- | :--- | :--- |
| **REACH SVHC 253项** | 欧盟REACH法规—高度关注物质候选清单（SVHC） | `01_REACH_SVHC_01_物质全量清单(含组成员_545条).csv` |
| **REACH Annex XVII** | 欧盟REACH法规附件XVII—限制物质清单 | `02_REACH_附录XVII_02_受限物质明细与组成员(1868条).csv` |
| **RoHS** | 欧盟《关于限制在电气电子设备中使用某些有害物质的指令》 | `03_EU_RoHS_01_受限物质清单(160条_含已补全类别CAS).csv` |
| **HSF 001** | HSF（Hazardous Substance Free）有害物质无害化/无有害物质管理要求 | `04_HSF-001_01_有害物质清单(172条_含已补全CAS).csv` |
| **BSBL** | bluesign® SYSTEM BLACK LIMITS（bluesign体系黑色限值清单） | `05_BSBL_01_受限物质总表(1726条_已修复日期并全量补全CAS).csv` |
| **AfPS GS 2019:01 PAK** | 德国产品安全委员会GS认证—多环芳烃（PAHs）测试与评估规范 | `06_AfPS_GS_2019_01_PAK_01_限值清单(15单项+2合计).csv` |

## 模板与排版规范

报告必须全部改用 `F:\APP Location\Guanzhi Tong\Skill\法律法规判断\检测报告模板` 规范：

1. **基本信息**：
   - 受检型号：[产品名称/型号]
   - 检测日期：YYYY/MM/DD
2. **检测项目**：
   - 表格形式列明上述六项法规体系及其全称。
3. **检测结果（六个独立表格）**：
   - 对应六项法规逐一生成明细表格。
   - **表头高亮**：
     - `检测通过`：底色浅绿 `#E3F2D9`，文字绿色 `#00B050`
     - `警告`：底色浅黄 `#FEF2CB`，文字橙色 `#C65F10`
     - `不符`：底色浅红 `#F9DBDF`，文字红色 `#FF0000`
   - **物质明细行**：列出受检物料的所有组分（序号、物质名称、CAS编号、含量%、限值/判定说明）。
     - 未受限组分一律标为 `无限值`（绿色高亮）；
     - 受限/超标组分清晰标明限值或特定要求（如 `500mg/kg`、`1000ppm(0.1%)` 等）。
4. **总结**：
   - 总结 CAS 对照粗检结论，语言简明有力，直接点名通过项与不符/警告项，不撰写与成分无关的冗长法律评论。
5. **特殊说明**：
   - 双酚类化学品系列：未添加且不含有；
   - 特殊邻苯二甲酸酯类增塑剂：未添加且不含有。

## 运行方式与示例

```powershell
python scripts/legal_compliance_judge.py `
  --facts facts.json `
  --standards auto `
  --db legal_compliance.db `
  --data-root "F:\APP Location\Guanzhi Tong\法律法规物质清单" `
  --format markdown `
  --output "PU-3011_法律法规检测报告.md" `
  --output-pdf "PU-3011_法律法规检测报告.pdf"
```

脚本将基于官方 DOCX 模板自动生成格式一致的 DOCX 文件，并通过 LibreOffice 无头模式自动导出强校验 PDF 交付件。
