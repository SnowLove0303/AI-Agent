# Proposal: Build independent TDS eight-format standardizer

## Goal

把现有四份用户维护的 TDS 模板内化为独立的 `TDS Skill`，建立一次抽取、一次语义归一、四变体逐一映射、四份 DOCX 及其派生 PDF 的可审计流水线。

## Scope

- 覆盖 TDS：中文/英文 × 冠志/国彩四个模板变体。
- 交付矩阵：四个最终 DOCX + 四个由对应最终 DOCX 转换得到的 PDF。
- 每个变体保留自己的模板几何、语言和公司骨架；映射共享同一 TDS semantic model。
- 模板示例产品、数值、成分、性能和公司事实只用于建立结构基线，禁止写入其他产品。
- TDS 源码、模板、映射、审计和测试放入独立 `TDS Skill`，不改写或导入 `MSDS Skill` 的业务实现。

## Non-goals

- 不重建表格，不把四个变体合并成一个物理模板。
- 不根据模板示例事实补全源文件缺失的数据。
- 不为 PDF 单独排版或维护独立 PDF 内容。

## Acceptance

1. 四份模板均有来源哈希、DOCX 基线和结构 snapshot/hash。
2. 一份来源数据可以经统一语义模型生成四个模板对应的 DOCX，且每个字段都有唯一目标槽位或明确的 fail-closed 结果。
3. 四个 PDF 均由审计通过的对应 DOCX 转换得到，八文件矩阵、模板几何、映射白名单和事实隔离审计通过。
4. 自动测试、OpenSpec 校验、V2.9/MSDS 继承审计和 TDS 专项审计结果被保留；任一发布阻断失败不得标记通过。

