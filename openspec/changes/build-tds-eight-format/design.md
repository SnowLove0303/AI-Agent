# Design: Independent TDS mapping and eight-format build

## Repository boundary

唯一代码根为 `F:\APP Location\Guanzhi Tong\Skill\覆写技能\AI-Agent`。新增内容仅在 `TDS Skill\`；`MSDS Skill\` 作为既有独立模块保持不变。四个 `.doc` 来源文件从用户指定资料目录复制为只读模板来源，转换后的 `.docx` 只作为 TDS active baseline。

## Data flow

```text
source DOC/DOCX
  -> one extraction
  -> source evidence ledger
  -> agent-guided normalized TDS semantic model
  -> professional English translation / presentation decisions
  -> four variant mappings (CN/EN x Guanzhi/Guocai)
  -> fresh clone of each active DOCX template
  -> whitelist-controlled in-place value overwrite
  -> template/semantic audit
  -> DOCX-derived PDF
  -> pair audit + eight-file package audit
```

模板负责页面几何、列结构、样式、页眉页脚、语言和公司骨架；源文件负责产品事实。性能表的数据行区域是受控可变区域：输出必须保留源文件的行顺序、项目原文、限定条件、指标值、单位和测试方法；模板示例项目只用于提供行样式，不得作为产品事实。字段无法唯一匹配、语义限定条件不一致、模板容量不足或出现未授权结构变化时立即失败，不猜测、不擅自改名。

特性格式契约：四个 active 模板的两个基线特性段落不使用智能编号，段落不得携带 `numPr`；源文本已有的显示性手工序号只在写入时去除。段落行距、段前后距以及 run 的字符间距、字距和位置由对应模板定义，两个基线特性槽位必须保持一致，新增特性只深拷贝特性模板段落。注册、快照和产出审计均检查该契约，失败即阻断。

### Spacing and vertical budget contract

四个 active 模板的标准间距只约束 `w:spacing`：章节标题为首标题段前 100 twips、后续标题段前 160 twips、标题段后 80 twips；特性项为段前 0、段后 60、行距 280 twips；正文为段前 0、段后 60、行距 300 twips。字体、字号、字符间距、首行/悬挂缩进、编号、制表位和表格结构不属于间距变更面，必须从模板继承并由既有骨架审计保护。

中文 active 模板的 `product.title` 段落必须使用 Word 原生 `w:jc w:val="center"`，且不得携带历史固定左缩进；本次基线修复只移除该标题段的 `left=3020 twips` 并写入原生居中，标题字体、字号、加粗和其他模板属性继续从模板继承。该契约写入 registry 与审计，避免长产品名再次被伪居中逻辑向右挤压。

章节过渡间距以有效内容末端到下一章节标题的垂直留白为验收对象。输出正文区域不得保留模板空白占位段；正文/特性段后的段后距与下一标题段前距继续由 typography 契约提供，表格后的标题也不得通过额外空段制造局部留白。registry 的 `inter_section_spacing` 与输出审计共同保证章节过渡不出现局部断崖。

英文内容密度超过注册阈值时，按产品总内容项分两级收缩：Level 1（至 16 项）标题段前 120、段后 60，内容项段后 30、行距 280；Level 2（超过 16 项）标题段前 80、段后 40，内容项段后 20、精确行距 260。预算只修改段落间距属性，不触碰文本大小、缩进、序号或其他模板格式；生成记录必须保留实际使用的预算级别。

### Evidence and judgment layers

抽取结果是只读 evidence ledger；`normalized_model` 通过 `source_values`、`normalized_values`、`provenance`、`decision`、`reason` 和 `confidence` 将事实与判断分开。程序里的别名只生成候选，不替代上下文判断。Agent 必须决定段落边界、语义归类、限定条件、单位/符号、列表结构和目标语言表达；会改变客户含义的未决判断进入 blocker 或 `needs_judgment`，不得静默猜测。

英文变体只消费标准化模型的 `normalized_values`。若存在英文源文件，它是目标语言证据和交叉校验，不是绕过标准化模型的直接覆写源。英文翻译允许为专业表达调整语序和句法，但不得增加、削弱或改变标准化事实。

### Verbatim Chinese content contract

中文事实是只读源数据，不是可供 Agent 二次润色的候选文本。映射阶段必须为源事实文件、文本字段和性能行记录哈希；覆写前校验 `source_values` 与中文 `normalized_values` 不得分叉，中文写入直接使用源值。生成后必须按章节、标题、性能表行回读 DOCX 并逐项精确比对；仅允许模板已登记的列表序号剥离、外层空白收束和段落拆分，不允许词序、同义词、技术术语、数值、单位、测试条件或免责声明变化。该门禁失败时，CLI 不得进入 PDF 转换，更不得形成可交付 ZIP。

### Source-led performance table

性能表表头、列宽、边框、字体、对齐和合并关系来自对应模板并保持锁定；数据行按源文件顺序写入。源行数量少于模板基线时，删除未被源文件使用的模板示例数据行；源行数量超过基线时，深拷贝最后一个数据行追加。既有和追加数据行的项目标签均来自源文件，标签单元格只允许受控事实写入，格式不得变化。模板存在而源文件不存在的指标不生成“无数据”产品行。

语义归类仅在项目含义和限定条件一致时成立。例如 `PH值（1:10稀释在水中）` 不能归入 `PH值（25℃）`；若模板无同语义槽位，则保留为源标签的扩展行。该例是判断证据，不是供 Agent 机械套用的通用别名规则。

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

- 只允许修改 registry 明确的值槽位；表头、列宽、合并、grid width、段落/字符格式、段落/字符间距、段落编号和页眉页脚均受保护。数据行项目标签是源事实值槽位，格式受保护；不得使用模板标签替换源标签。
- 缺失的源性能行不显示模板示例行；缺失语言事实继续以 `无数据` / `No data available` 形成诊断输出，但正式审计必须阻断，不得复制模板示例值或用另一语言冒充。
- 只在 DOCX 完成内容和结构审计后转换 PDF；PDF 不接受独立内容编辑。
- 发布包必须恰好包含八个矩阵文件及机器可读审计证据，阻断项优先于分数。
