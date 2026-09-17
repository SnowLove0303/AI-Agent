# 化学物质法律法规合规性判断技能与 MCP 服务 (Judg MCP Skill)

本目录为冠志通法律法规判断技能包与 MCP 服务的归档交付目录，赋予 AI Agent 通过 MCP 协议实时审查化学物质（及多组分配方）法规合规性的全流程能力。

---

## 1. 核心架构设计

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AI Agent / Antigravity                          │
│                                   │                                    │
│                    substance-compliance-query Skill                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (MCP Stdio Protocol)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     substance-compliance-mcp                           │
│  FastMCP 服务: check_substance_compliance / batch_check / search...    │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
         (1) Primary Engine               (2) Direct Fallback Engine
                    ▼                                ▼
       ┌─────────────────────────┐       ┌───────────────────────────────┐
       │ Docker Web API Endpoint │       │ 本地 SQLite 法规数据库清单    │
       │  http://127.0.0.1:18765 │       │ 涵盖 6 大法规 4,000+ 受限条目 │
       └─────────────────────────┘       └───────────────────────────────┘
```

1. **主引擎 (Primary Engine)**：实时调用冠志通 Docker Web API (`http://127.0.0.1:18765/api/compliance/check?identifier=<cas>`)，提供毫秒级响应。
2. **容灾回退引擎 (Direct Fallback Engine)**：在 Docker 服务未拉起或重启时，自动直连本地 SQLite 6 大法规库（`03_数据库/法规数据库/物质限制清单/`），保障 100% 服务可用率。
3. **中文/英文名与 CAS 智能映射**：内置常用高频受限化学品中英文名称索引库，并支持数据库模糊联想，用户输入“双酚A”、“铅”、“DEHP”等名称即可自动消歧映射为标准 CAS 开展审查。
4. **浓度限量定量动态比对**：自动支持 `% (w/w)` 与 `ppm (mg/kg)` 双向换算，精准对照 RoHS（铅 1000 ppm / 镉 100 ppm）、SVHC 0.1% 强制通报线等输出定量超标判定。

---

## 2. 覆盖的六大法规清单范围

| 序号 | 法规简称 | 官方依据 / 标准全称 | 核心管控基线 |
| :---: | :--- | :--- | :--- |
| 1 | **EU RoHS 2.0** | 2011/65/EU 及其修订指令 (EU) 2015/863 | 镉 100 ppm (0.01%)，铅/汞/六价铬/PBB/PBDE/4项邻苯 1000 ppm (0.1%) |
| 2 | **REACH SVHC** | 欧盟 REACH 高度关注物质候选清单 (253项 / 545条细分) | 物品或配方中含有 >0.1% (w/w) 即触发供应链信息传递及 SCIP 通报 |
| 3 | **REACH Annex XVII** | 欧盟 REACH 附录 XVII 限制物质清单 (86大类条目) | 制造、投放市场及特定消费/工业用途强制性限制或全面禁用 |
| 4 | **BSBL v8.0** | BSBL 限制物质清单 (51大类，1726条细分物质) | 鞋服、高分子涂层与材料制造严苛化学品限制标准 |
| 5 | **HSF-001** | 企业 HSF-001 有害物质控制清单 (172条) | 企业绿色产品设计与材料准入限制规范 |
| 6 | **AfPS GS 2019:01 PAK** | 德国 GS 认证多环芳烃限制标准 (15单项+2合计) | 消费品及人体接触材料中多环芳烃迁移/含量分级限量 (0.2~50 mg/kg) |

---

## 3. MCP 工具说明

- **`check_substance_compliance`**：单物质合规性查询。参数：`substance` (CAS/EC/名称), `concentration_pct`, `concentration_ppm`, `regulations`, `material_type`。
- **`batch_check_compliance`**：多组分配方批量合规审查。参数：`components` (组分对象列表), `regulations`。
- **`search_regulatory_substances`**：法规限制清单关键词检索。参数：`keyword`, `regulation`, `limit`。
- **`get_regulation_info`**：查询指定法规的官方依据、版本与核心限量。参数：`regulation`。

---

## 4. 目录文件结构

- `SKILL.md`：Antigravity 技能规范文件，定义提示词模板、工具调用协议与专业研判报告模板。
- `server.py`：基于 FastMCP 的标准 MCP 服务端源码，支持 stdio 传输。
- `mcp_config.json`：MCP 客户端注册配置片段。
- `verify_server.py`：端到端独立自动化测试脚本。
