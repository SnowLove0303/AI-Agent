# deliverable-audit-framework Specification

## Purpose

为 MSDS 八文件交付包提供一套可重复、可追溯且面向客户交付判断的质量评估契约，将内容、模板、格式、PDF 派生、视觉检查和发布证据统一为可执行的审计结果。

## Requirements

### Requirement: Audit package identity and scope
审计器 MUST 将一次审计绑定到一个明确的八文件交付包、输入源、维护模板、Skill 版本和审计规则版本，并 MUST 在包缺失、重复或身份不一致时阻止发布。

#### Scenario: Complete package has stable identity
- **WHEN** 审计输入包含一个产品的 CN/EN × 冠志/国彩 DOCX 和对应 PDF
- **THEN** 审计结果记录产品标识、八个预期文件、源文件身份、模板身份、Skill 版本和审计运行标识，并继续执行其余检查

#### Scenario: Missing or duplicate deliverable is supplied
- **WHEN** 输入目录缺少八文件矩阵中的任意文件，或同一矩阵位置存在多个候选文件
- **THEN** 审计结果标记为 `B0`，最终结果为 `RELEASE_FAIL`，且不得被分数覆盖

### Requirement: Weighted quality score and blocker precedence
审计器 MUST 按固定的 100 分模型计算质量分：源事实与语义 30 分、模板结构与受控覆写 25 分、DOCX 版式与视觉质量 20 分、四格式语义/公司一致性 10 分、DOCX 到 PDF 派生与 PDF 质量 10 分、发布包与审计证据完整性 5 分。任何 B0 或 B1 存在时不得通过；无 B0/B1、全部必需检查完成且总分至少 95 分时才可通过。

#### Scenario: High score with a hard blocker
- **WHEN** 非阻断检查合计达到 95 分，但发现模板 geometry、受控标签骨架或 DOCX/PDF 派生关系的 B0/B1 失败
- **THEN** 最终结果为 `RELEASE_FAIL`，并保留分数、阻断级别、规则编号和证据路径

#### Scenario: Passing score without blockers
- **WHEN** 所有必需检查通过、没有 B0/B1、总分至少 95 分且完整证据已生成
- **THEN** 最终结果为 `RELEASE_PASS`

### Requirement: Standardized severity and release outcomes
审计器 MUST 使用 B0、B1、B2 三级严重性，并 MUST 输出 `RELEASE_PASS`、`RELEASE_FAIL`、`NOT_READY` 或 `OBSERVATION_ONLY` 之一。

#### Scenario: Observation-only inspection
- **WHEN** 审计被显式标记为观察模式
- **THEN** 输出 `OBSERVATION_ONLY`，保留发现项但不误报为发布结论

### Requirement: Source fidelity and semantic classification audit
源文件存在的数据 MUST 被正确归类并保留，缺失数据 MUST 使用约定表达，禁止示例事实、审计说明或无来源推断写入产品事实。

#### Scenario: Existing source data is mapped to the correct section
- **WHEN** 源文件包含“主要眼睛刺激性”数据，而目标模板以 11.3 承载该结构
- **THEN** 数据进入正确的 Section 11 字段，并记录源文本与目标字段映射证据

#### Scenario: Template example fact leaks into output
- **WHEN** 输出出现维护模板中的 PEA-4139、示例成分或示例毒理/生态事实，且该事实不在本产品批准数据中
- **THEN** 审计器至少标记 B1 并阻止发布

### Requirement: Template geometry and controlled mutation audit
输出 MUST 由当前维护 CN/EN 模板 fresh clone 产生，表格、行列、合并、grid widths、段落/字符属性、页眉页脚和锁定骨架 MUST 符合 snapshot/hash；修改 MUST 符合 mutation whitelist。

#### Scenario: Geometry matches maintained baseline
- **WHEN** 输出结构快照与对应维护模板一致，且仅存在白名单允许的内容差异
- **THEN** geometry 和 mutation audit 通过并记录模板证据

#### Scenario: Locked skeleton is changed
- **WHEN** 输出改变序号列、标签列或其受保护格式属性
- **THEN** 审计器标记阻断并禁止发布

### Requirement: Section-specific content and layout audit
审计器 MUST 对 Section 2、3、8、9、11 和 14 执行专门检查，包括象形图、标签换行、成分一行、手部防护、8.2 工程控制、无数据项省略重排、11.10 和运输换行。

#### Scenario: Section 2 pictogram and label fields are valid
- **WHEN** 源数据要求 GHS 象形图或标签有害成分提示
- **THEN** 输出包含完整象形图和换行标签内容，且不使用不可见位置交叉引用

#### Scenario: Section 3 keeps one ingredient per row
- **WHEN** 输出包含多个成分或成分数据缺失
- **THEN** 每个成分恰好占一行，缺失值使用 `无数据` 或 `No data available`

#### Scenario: Section 9 omits absent properties
- **WHEN** Section 9 某物性项目没有源数据
- **THEN** 该项目行不展示，剩余项目按连续原语义顺序重排

#### Scenario: Section 11 retains supported toxicology
- **WHEN** 源文件存在急性毒性、刺激性或其他 11.x 数据
- **THEN** 对应结构化字段保留原文归纳事实，不错误输出无数据或追加推断

#### Scenario: Section 14 line breaks are compliant
- **WHEN** 输出包含运输信息多项字段
- **THEN** 每个字段按固定标签和要求换行呈现

### Requirement: Four-format semantic and company parity
审计器 MUST 检查 CN/EN × 冠志/国彩四种格式的内容完整性，并确认公司变体只改变获准公司信息、语言变体只改变受控翻译内容。

#### Scenario: Four variants remain semantically equivalent
- **WHEN** 一个产品生成四个 DOCX 变体
- **THEN** 产品事实、章节结构、危险性分类和固定标签语义一致，仅公司与语言字段按规则变化

### Requirement: DOCX-derived PDF and visual QA
PDF MUST 是对应最终 DOCX 的转换产物，并通过页数、页面尺寸、文本、空白页/零字节、象形图和关键页面视觉 QA。

#### Scenario: PDF is derived from final DOCX
- **WHEN** DOCX 完成内容和模板审计且有对应 PDF
- **THEN** 报告记录 DOCX/PDF 配对、来源证据、页数和渲染检查结果

#### Scenario: PDF cannot be traced or has layout failure
- **WHEN** PDF 无法追溯到最终 DOCX，或出现空白页、截断、溢出或缺图
- **THEN** 审计器标记阻断并阻止发布

### Requirement: Evidence-complete machine-readable audit report
每条规则 MUST 生成带 `rule_id`、`category`、`severity`、`status`、`source_of_truth`、`method`、`pass_condition`、`observed`、`evidence_paths` 和 `message` 的版本化证据记录；最终报告 MUST 同时支持 JSON 和人类阅读。

#### Scenario: Successful audit has complete evidence
- **WHEN** 一次完整审计运行结束
- **THEN** JSON 报告包含每个必需规则恰好一条结果、分数、阻断项、outcome、输入身份和证据路径

#### Scenario: Audit execution is incomplete
- **WHEN** 必需规则因缺文件、工具错误或未执行而没有结果
- **THEN** 标记 `NOT_CHECKED` 或 `ERROR`，最终不得为 `RELEASE_PASS`

### Requirement: Regression and release gate coverage
Skill MUST 提供评分、阻断、清单、证据 schema、PU-2345/OS-9015 八文件回放和 ZIP 完整性测试；发布前 MUST 运行 V2.9 inheritance、模板 geometry、semantic/company parity、自动测试和逐页 QA。

#### Scenario: Release gate is complete
- **WHEN** 发布命令执行
- **THEN** 所有 release blocker、自动测试和证据完整性检查均有结果，任意失败都会使发布失败并保留证据

#### Scenario: Audit checklist drifts from implementation
- **WHEN** 清单中有未实现或未测试的必需项
- **THEN** 覆盖审计失败，版本不得发布
