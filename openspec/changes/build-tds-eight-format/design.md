# Design: Independent TDS mapping and eight-format build

## Repository boundary

唯一代码根为 `F:\APP Location\Guanzhi Tong\Skill\覆写技能\AI-Agent`。新增内容仅在 `TDS Skill\`；`MSDS Skill\` 作为既有独立模块保持不变。四个 `.doc` 来源文件从用户指定资料目录复制为只读模板来源，转换后的 `.docx` 只作为 TDS active baseline。

## Data flow

```text
source DOC/DOCX
  -> one extraction
  -> normalized TDS semantic model
  -> four variant mappings (CN/EN x Guanzhi/Guocai)
  -> fresh clone of each active DOCX template
  -> whitelist-controlled in-place value overwrite
  -> template/semantic audit
  -> DOCX-derived PDF
  -> pair audit + eight-file package audit
```

模板负责页面几何、列结构、样式、页眉页脚、语言和公司骨架；源文件负责产品事实。性能表的数据行区域是受控可变区域：输出必须保留源文件的行顺序、项目原文、限定条件、指标值、单位和测试方法；模板示例项目只用于提供行样式，不得作为产品事实。字段无法唯一匹配、语义限定条件不一致、模板容量不足或出现未授权结构变化时立即失败，不猜测、不擅自改名。

### Source-led performance table

性能表表头、列宽、边框、字体、对齐和合并关系来自对应模板并保持锁定；数据行按源文件顺序写入。源行数量少于模板基线时，删除未被源文件使用的模板示例数据行；源行数量超过基线时，深拷贝最后一个数据行追加。既有和追加数据行的项目标签均来自源文件，标签单元格只允许受控事实写入，格式不得变化。模板存在而源文件不存在的指标不生成“无数据”产品行。

语义归类仅在项目含义和限定条件一致时成立。例如 `PH值（1:10稀释在水中）` 不能归入 `PH值（25℃）`；若模板无同语义槽位，则保留为源标签的扩展行。

### Controlled capacity extension

五个基线性能行和两个基线产品特性段落是最小容量，不是硬上限。更多性能指标只能深拷贝模板最后一个数据行后追加，并允许仅在新行的标签单元格写入源字段名；更多产品特性只能深拷贝特性段落后追加。既有行、标签、序号、格式和后续章节不得移动或改写。每个扩展项都必须保留原文、语言值和源位置，无法配对或超过显式上限时阻断。

## Variant identity

每个变体使用独立 `variant_id`、源文件 hash、active DOCX hash、snapshot 和 field registry：

- `TDS_CN_Guanzhi`
- `TDS_CN_Guocai`
- `TDS_EN_Guanzhi`
- `TDS_EN_Guocai`

CN/EN 的翻译由受控字段规则生成；公司差异来自各自模板和 company overlay。四变体不得维护四份独立产品事实。

## Mutation and release rules

- 只允许修改 registry 明确的值槽位；表头、列宽、合并、grid width、段落/字符格式和页眉页脚均受保护。数据行项目标签是源事实值槽位，格式受保护；不得使用模板标签替换源标签。
- 缺失的源性能行不显示模板示例行；缺失语言事实继续以 `无数据` / `No data available` 形成诊断输出，但正式审计必须阻断，不得复制模板示例值或用另一语言冒充。
- 只在 DOCX 完成内容和结构审计后转换 PDF；PDF 不接受独立内容编辑。
- 发布包必须恰好包含八个矩阵文件及机器可读审计证据，阻断项优先于分数。
