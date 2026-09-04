# Changelog

## 1.1.0 — 2026-09-04

- 增加性能指标行和产品特性段落的受控延展：只克隆维护模板样式，既有骨架不移动。
- 未知性能指标按各语言源文件的出现顺序配对；源表超过四列、数量不一致或容量超限时 fail closed。

## 1.0.0 — 2026-09-04

- 新增独立 TDS Skill，与 MSDS Skill 分目录、分映射、分程序和分测试。
- 内化四个用户维护模板：CN/EN × 冠志/国彩；建立来源 hash、active DOCX、registry 和 geometry/package snapshot。
- 建立一次抽取、统一 semantic model、四变体一一映射、fresh-clone 原位覆写和 fail-closed 约束。
- 建立四 DOCX + 四 DOCX-derived PDF 的八格式构建和发布审计入口。
