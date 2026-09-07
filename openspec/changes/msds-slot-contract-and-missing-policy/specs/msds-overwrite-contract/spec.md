## Purpose

为 MSDS 文档覆写建立可验证的事实、模板槽位和缺失数据契约，使 Agent 能在源文件结构差异中灵活判断映射，同时让最终写入始终受正式模板和发布规则约束。

## ADDED Requirements

### Requirement: Template slot authorization

每个 MSDS 输出 MUST 从对应维护模板 fresh clone 生成。系统 MUST 将模板内容区分为锁定结构/标签、可写值对象、故意留空槽位、整格说明槽位和 Section 8.2 专用数据槽位；普通覆写只能写入已授权的可写值对象。模板空值对象在非 Section 8.2 场景下 MUST 保持为空，即使源文件出现同名文字也不得写入。

#### Scenario: Source fact targets a writable value object

- **WHEN** 源文件包含一个与模板已注册字段对应的事实
- **THEN** 系统将该事实写入对应值对象，并保持模板表格、标签、合并、边框、宽度、段落和字符格式不变

#### Scenario: Source fact targets an intentionally blank slot

- **WHEN** 源文件包含 Section 8“建议”等内容，但对应模板值对象被定义为空且不是 Section 8.2 专用槽位
- **THEN** 系统不写入该内容，保持该模板槽位为空，并在审计证据中记录该源字段没有可授权目标槽位

#### Scenario: Template example is not a product fact

- **WHEN** 维护模板含有示例地址、成分、危害、毒理、生态或职业接触限值
- **THEN** 系统先清理这些示例值，再只写入本产品批准事实；示例值不得出现在输出中

### Requirement: Source fidelity and shared semantic model

源文件 MUST 是产品事实的权威来源。对已映射到授权值对象的事实，系统 MUST 保留原文语义和完整限定信息，不得擅自摘要、改字、同义替换、跨章节补写或根据常识推断。四个语言/公司变体 MUST 复用同一个已批准的产品语义模型；公司差异和语言差异只能发生在受控覆盖层。

#### Scenario: Exact source text is preserved

- **WHEN** 源文件包含供应商地址或带限定条件的危害描述
- **THEN** 对应输出保留源文件的地址和完整限定内容，不出现“掬泉路”到“揽泉路”或完整危害描述到摘要文字的漂移

#### Scenario: One semantic model drives four variants

- **WHEN** 系统为同一产品生成 CN/EN 与冠志/国彩四个变体
- **THEN** 四个变体共享相同的产品事实、危险性和章节语义，仅使用批准的语言呈现和公司信息覆盖

#### Scenario: Unmapped source fact is not silently invented or discarded

- **WHEN** 源文件存在事实但正式模板没有授权目标槽位，或字段映射存在歧义
- **THEN** 系统不新增模板行、不改写其他字段、不猜测目标，输出可定位的审查记录并阻止正式发布，直到该事实被明确处理

### Requirement: Section-specific missing-data states

系统 MUST 区分 `SUPPORTED`、`EXPLICIT_MISSING`、`NOT_APPLICABLE` 和 `ABSENT` 四种源字段状态。`ABSENT` 表示源文件没有该字段，模板对应字段 MUST 不显示；`NOT_APPLICABLE` MUST 保留；具体缺失展示和省略 MUST 按章节策略执行。

#### Scenario: Section 9 explicit missing value

- **WHEN** Section 9 的源字段明确为无数据
- **THEN** 系统删除该完整物性行，并按原语义顺序连续重排剩余可见编号

#### Scenario: Section 11 or 12 has no valid endpoint data

- **WHEN** Section 11 或 Section 12 除章节说明行外没有任何有效终点数据
- **THEN** 系统只保留源文件说明行，删除模板终点结构和无数据终点行，不显示模板专有字段

#### Scenario: Other section has explicit missing data

- **WHEN** 非 Section 9/11/12 的源字段在源文件中明确存在且值为无数据
- **THEN** 系统保留该源字段对应的模板值对象并显示统一的 `无数据` 或 `No data available`

#### Scenario: Source field is absent

- **WHEN** 模板有一个字段但源文件没有该字段
- **THEN** 系统不显示该模板字段，不使用模板示例值或自动生成的无数据文字填充它

### Requirement: Section 8.2 controlled table exception

Section 8.2 MUST 作为唯一的普通表格数据例外处理。系统 MUST 保留其父行、表头文字、列数、网格和格式；模板示例数据行 MUST 被清理。只有经源文件验证的控制参数记录可以写入数据行；源文件没有控制参数时不得生成工程控制 prose、职业接触限值或其他产品事实。

#### Scenario: Source contains control-parameter records

- **WHEN** 源文件提供一个或多个可验证的 Section 8.2 控制参数记录
- **THEN** 系统按一条记录一行写入物质、依据、类型和值，并保留 8.2 父行和表头结构

#### Scenario: Source has no Section 8.2 data

- **WHEN** 源文件没有 Section 8.2 工程控制或控制参数记录
- **THEN** 系统不生成工程控制描述、不保留模板示例 OEL 事实，并按批准的空表策略处理数据区域

### Requirement: Agent flexibility is bounded by reviewable mapping

Agent MAY 对源文件字段别名、自然语言语义、Section 2 危害归类、Section 11/12 终点映射和英文呈现进行判断，但每个非机械判断 MUST 记录源依据、目标字段、处理状态和理由。Agent MUST NOT 通过修改模板结构来解决映射不确定性。

#### Scenario: Alias maps to an existing slot

- **WHEN** 源文件使用与模板不同但已确认等价的字段名称
- **THEN** 系统将其映射到现有授权槽位，保留源值，并记录别名和源位置证据

#### Scenario: Ambiguous mapping needs review

- **WHEN** 一个源字段可能对应多个模板槽位且无法由已批准规则唯一确定
- **THEN** 系统生成审查项并阻止该产品正式发布，不凭猜测继续写入
