## MODIFIED Requirements

### Requirement: Section-specific content and layout audit

审计器 MUST 对 Section 2、3、8、9、11 和 14 执行专门检查，包括象形图、标签换行、成分一行、手部防护、8.2 工程控制、无数据项省略重排、11.10 和运输换行。审计器 MUST additionally 检查 Section 2 防范说明中源文件明确存在的分组小标题、组顺序、P 语句归属和 CN/EN 对等性。显式存在且有有效子语句的防范说明分组不得在批准模型、输出追溯或最终值区中静默丢失；此类丢失 MUST 作为阻断项处理。Section 8 source records MUST be split into independent label/value facts before template projection. Mapping MUST be semantic and source-order aware; a missing source subsection heading, inline label/value contamination, tabs, or a differing row count MUST NOT trigger positional cascade matching.

#### Scenario: Section 2 pictogram and label fields are valid
- **WHEN** 源数据要求 GHS 象形图或标签有害成分提示
- **THEN** 输出包含完整象形图和换行标签内容，且不使用不可见位置交叉引用

#### Scenario: Section 2 precautionary groups are retained
- **WHEN** 源文件的防范说明包含一个或多个明确分组小标题，且每个分组有来源支持的 P 语句
- **THEN** CN/EN 输出在固定防范说明值区保留相同的组顺序和 P 语句归属，审计记录每个组的来源和目标槽位；缺失任何有效分组时结果为阻断

#### Scenario: Empty precautionary groups are hidden safely
- **WHEN** 某个防范说明分组没有有效 P 语句，或整个 Section 2 防范说明没有来源支持的值
- **THEN** 孤立小标题和空行不出现在客户文件中，必要的完整值行按既有空值删除策略隐藏，并在主项省略后执行连续重排

#### Scenario: Section 2 headings do not mutate the template skeleton
- **WHEN** 输出恢复源文件中的防范说明小标题
- **THEN** 模板固定 `2.6 防范说明：` 标签、序号、值区边界、表格拓扑、加粗标签和非粗体值格式保持不变

#### Scenario: Section 3 keeps one ingredient per row
- **WHEN** 源文件提供多个成分或不完整成分数据
- **THEN** 每个成分恰好占一行，缺失值使用 `无数据` 或 `No data available`

#### Scenario: Section 9 omits absent properties
- **WHEN** Section 9 某物性项目没有源数据
- **THEN** 该项目行不展示，剩余项目按连续原语义顺序重排

#### Scenario: Section 8 PPE records are source-order aware
- **WHEN** 源有 PPE 行、缺少预期小节标题，或使用制表符/内联文本合并标签和值
- **THEN** 提取器恢复独立标签/值记录并映射到匹配模板行，不因行数差异触发位置级级联

#### Scenario: Section 8 recommendation is source-gated
- **WHEN** 源文件没有实质性 Section 8 建议
- **THEN** 建议值保持为空或按批准策略隐藏，不复制相邻防护值

#### Scenario: Section 11 retains supported toxicology
- **WHEN** 源文件存在急性毒性、刺激性或其他支持的 11.x 数据
- **THEN** 对应字段保留在正确结构化终点，不推断或跨字段替换

#### Scenario: Section 14 line breaks are compliant
- **WHEN** 输出包含多项运输信息
- **THEN** 每个字段在固定标签和值边界按要求换行，不产生空行或仅斜杠行
