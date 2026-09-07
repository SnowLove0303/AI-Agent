## MODIFIED Requirements

### Requirement: Source fidelity and semantic classification audit

源文件存在的数据 MUST 被正确归类并保留，缺失数据 MUST 按字段状态和章节策略处理，禁止示例事实、审计说明或无来源推断写入产品事实。审计 MUST 检查源事实是否发生改字、摘要、跨章节迁移、值对象错写或丢失。

#### Scenario: Existing source data is mapped to the correct section

- **WHEN** 源文件包含“主要眼睛刺激性”数据，而目标模板以 11.3 承载该结构
- **THEN** 数据进入正确的 Section 11 字段，并记录源文本与目标字段映射证据

#### Scenario: Source fact changes during overwrite

- **WHEN** 源文件地址为“掬泉路3号”或危害描述包含完整限定信息，而输出出现不同地址或缩写内容
- **THEN** 审计器至少标记 B1，保留源/输出差异证据并阻止发布

#### Scenario: Template-only fact leaks into output

- **WHEN** 输出出现维护模板中的 PEA-4139、示例成分、示例毒理/生态事实或示例 OEL 数据，且该事实不在本产品批准数据中
- **THEN** 审计器至少标记 B1 并阻止发布

#### Scenario: Template example fact leaks into output

- **WHEN** 输出出现维护模板中的 PEA-4139、示例成分或示例毒理/生态事实，且该事实不在本产品批准数据中
- **THEN** 审计器至少标记 B1 并阻止发布

#### Scenario: Source field has no authorized target slot

- **WHEN** 源文件有字段但模板值对象为空或没有该字段的授权槽位，且输出尝试把内容写入该槽位或其他字段
- **THEN** 审计器标记 B1，并要求存在可定位的 unmapped/review 证据

### Requirement: Template geometry and controlled mutation audit

输出 MUST 由当前维护 CN/EN 模板 fresh clone 产生，表格、行列、合并、grid widths、段落/字符属性、页眉页脚和锁定骨架 MUST 符合 snapshot/hash；修改 MUST 符合 mutation whitelist。审计 MUST 检查普通空值对象未被写入，并允许的删行只能来自明确的章节缺失策略。

#### Scenario: Geometry matches maintained baseline

- **WHEN** 输出结构快照与对应维护模板一致，且仅存在白名单允许的内容差异
- **THEN** geometry 和 mutation audit 通过并记录模板证据

#### Scenario: Locked skeleton or blank slot is changed

- **WHEN** 输出改变序号列、标签列、固定页眉文字、受保护格式属性，或向非 Section 8.2 的故意留空槽位写入内容
- **THEN** 审计器标记 B1/B0 级阻断并禁止发布

#### Scenario: Locked skeleton is changed

- **WHEN** 输出改变序号列、标签列或其受保护格式属性
- **THEN** 审计器标记阻断并禁止发布

### Requirement: Section-specific content and layout audit

审计器 MUST 对 Section 2、3、8、9、11 和 14 执行专门检查，包括象形图、标签换行、成分一行、手部防护、8.2 工程控制、无数据项省略重排、11/12 说明行收缩、11.10 和运输换行。

#### Scenario: Section 8 source parameters are retained

- **WHEN** 源文件提供 FKM/IIR/NBR 厚度和穿透时间
- **THEN** 输出保留三组完整数值，缺失任何一组都标记 B1

#### Scenario: Section 8.2 does not invent data

- **WHEN** 源文件没有 Section 8.2 控制参数或工程控制描述
- **THEN** 输出不得含有从其他章节概括出的工程控制 prose 或模板示例 OEL 事实

#### Scenario: Section 9 omits absent properties

- **WHEN** Section 9 某物性项目没有源数据或源值为纯无数据
- **THEN** 该项目行不展示，剩余项目按连续原语义顺序重排；`不适用`和实测值仍保留

#### Scenario: Section 11 or 12 is note-only

- **WHEN** Section 11 或 Section 12 没有任何有效终点数据
- **THEN** 输出只保留源说明行，不显示模板终点行或自动生成的无数据终点内容

#### Scenario: Section 2 pictogram and label fields are valid

- **WHEN** 源数据要求 GHS 象形图或标签有害成分提示
- **THEN** 输出包含完整象形图和换行标签内容，且不使用不可见位置交叉引用

#### Scenario: Section 3 keeps one ingredient per row

- **WHEN** 输出包含多个成分或成分数据缺失
- **THEN** 每个成分恰好占一行，缺失值使用 `无数据` 或 `No data available`

#### Scenario: Section 11 retains supported toxicology

- **WHEN** 源文件存在急性毒性、刺激性或其他 11.x 数据
- **THEN** 对应结构化字段保留原文归纳事实，不错误输出无数据或追加推断

#### Scenario: Section 14 line breaks are compliant

- **WHEN** 输出包含运输信息多项字段
- **THEN** 每个字段按固定标签和要求换行呈现

### Requirement: Regression and release gate coverage

Skill MUST 提供评分、阻断、清单、证据 schema、既有八文件回放和 ZIP 完整性测试；发布前 MUST 运行 V2.9 inheritance、模板 geometry、semantic/company parity、自动测试和逐页 QA。回归套件 MUST 覆盖 PU-1001 的事实保真、槽位边界、Section 8.2、Section 9/11/12 缺失数据和固定模板文字。

#### Scenario: PU-1001 regression catches known overwrite defects

- **WHEN** 运行 MSDS 回归测试
- **THEN** 测试验证“掬泉路”、完整 Section 2 食入危害、三组手套参数、Section 8 建议空槽位、Section 8.2 不补写、Section 10 缺失字段不显示、Section 11/12 说明行保留以及模板 Version 固定文字

#### Scenario: Release gate is complete

- **WHEN** 发布命令执行
- **THEN** 所有 release blocker、自动测试和证据完整性检查均有结果，任意失败都会使发布失败并保留证据

#### Scenario: Audit checklist drifts from implementation

- **WHEN** 清单中有未实现或未测试的必需项
- **THEN** 覆盖审计失败，版本不得发布
