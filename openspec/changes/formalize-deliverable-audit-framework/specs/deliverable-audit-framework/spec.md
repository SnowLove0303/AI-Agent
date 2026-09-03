## Purpose

为 MSDS 八文件交付包提供一套可重复、可追溯且面向客户交付判断的质量评估契约，将内容、模板、格式、PDF 派生、视觉检查和发布证据统一为可执行的审计结果。

## ADDED Requirements

### Requirement: Audit package identity and scope
审计器 MUST 将一次审计绑定到一个明确的八文件交付包、输入源、维护模板、Skill 版本和审计规则版本，并 MUST 在包缺失、重复或身份不一致时阻止发布。

#### Scenario: Complete package has stable identity
- **WHEN** 审计输入包含一个产品的 CN/EN × 冠志/国彩 DOCX 和对应 PDF
- **THEN** 审计结果记录产品标识、八个预期文件、源文件身份、模板身份、Skill 版本和审计运行标识，并继续执行其余检查

#### Scenario: Missing or duplicate deliverable is supplied
- **WHEN** 输入目录缺少八文件矩阵中的任意文件，或同一矩阵位置存在多个候选文件
- **THEN** 审计结果标记为 `B0`，最终结果为 `RELEASE_FAIL`，且不得被分数覆盖

### Requirement: Weighted quality score and blocker precedence
审计器 MUST 按固定的 100 分模型计算质量分，并 MUST 先处理不可覆盖的发布阻断项。固定权重 MUST 为：源事实与语义 30 分、模板结构与受控覆写 25 分、DOCX 版式与视觉质量 20 分、四格式语义/公司一致性 10 分、DOCX 到 PDF 派生与 PDF 质量 10 分、发布包与审计证据完整性 5 分。任何 B0 或 B1 阻断项存在时，最终结果 MUST NOT 为 `RELEASE_PASS`；无 B0/B1、全部必需检查完成且总分大于等于 95 分时才可通过。

#### Scenario: High score with a hard blocker
- **WHEN** 所有非阻断检查合计达到 95 分，但发现模板 geometry、受控标签骨架或 DOCX/PDF 派生关系的 B0/B1 失败
- **THEN** 最终结果仍为 `RELEASE_FAIL`，报告同时保留加权分数、阻断级别、规则编号和证据路径

#### Scenario: Passing score without blockers
- **WHEN** 所有必需检查通过、没有 B0/B1、总分大于等于 95 分且完整证据已生成
- **THEN** 最终结果为 `RELEASE_PASS`

#### Scenario: Non-passing score without hard blocker
- **WHEN** 没有 B0/B1，但总分低于 95 分
- **THEN** 最终结果为 `NOT_READY` 或 `RELEASE_FAIL`，并明确列出扣分项和需要修复的审计规则；不得输出 `RELEASE_PASS`

### Requirement: Standardized severity and release outcomes
审计器 MUST 使用 B0（发布阻断）、B1（客户交付前必须修复）和 B2（必须记录并在规定范围内处理）三级严重性，并 MUST 输出 `RELEASE_PASS`、`RELEASE_FAIL`、`NOT_READY` 或 `OBSERVATION_ONLY` 之一。

#### Scenario: Observation-only inspection
- **WHEN** 用户只要求查看现状，或输入不是可发布的完整包而审计被显式标记为观察模式
- **THEN** 审计器输出 `OBSERVATION_ONLY`，保留发现项，但不把观察结果误报为发布通过或发布失败

#### Scenario: B2 is recorded
- **WHEN** 发现不影响强制发布契约、但影响维护质量或可读性的 B2 项
- **THEN** 报告记录其严重性、影响、建议和证据，并允许在无 B0/B1 且分数达到阈值时进入 `RELEASE_PASS`

### Requirement: Source fidelity and semantic classification audit
审计器 MUST 核对源文件身份、产品/公司矩阵、事实来源链和统一 semantic model；源文件存在的数据 MUST 被正确归类并保留，缺失数据 MUST 使用约定的“无数据”表达，禁止将示例模板事实、审计说明或未经来源支持的推断写入产品事实。

#### Scenario: Existing source data is mapped to the correct section
- **WHEN** 源文件包含“主要眼睛刺激性”数据，而目标模板以“主要眼睛刺激性”作为 11.3 或其所属主要粘膜刺激性结构承载
- **THEN** 审计器确认该数据进入正确的 Section 11 结构化字段，并报告源文本与目标字段的映射证据

#### Scenario: Template example fact leaks into output
- **WHEN** 输出出现维护模板中的 PEA-4139、示例成分或示例毒理/生态事实，而该事实不在本产品源文件或批准数据中
- **THEN** 审计器标记至少 B1，列出泄漏文本和模板来源，并阻止发布

#### Scenario: Unsupported explanatory inference is added
- **WHEN** 输出包含源文件没有要求、没有事实支持且不是固定法规标签的补充解释或推断
- **THEN** 审计器标记为 B1 或 B2（按客户风险规则），并要求删除或提供可追溯来源

### Requirement: Template geometry and controlled mutation audit
审计器 MUST 验证输出由当前维护 CN/EN 模板 fresh clone 产生，且表格数量、行列、合并关系、grid widths、段落/字符属性、页眉页脚和受控锁定骨架符合模板 snapshot/hash；所有修改 MUST 符合 mutation whitelist，禁止重建英文表格或改变序号列、标签列格式。

#### Scenario: Geometry matches maintained baseline
- **WHEN** CN 或 EN 输出的结构快照与对应维护模板快照一致，且仅存在白名单允许的内容差异
- **THEN** geometry 和 mutation audit 均通过，并记录模板 hash、snapshot hash 和比较结果

#### Scenario: Locked skeleton is changed
- **WHEN** 输出改变序号列、标签列、锁定标签文本或其受保护的 XML/格式属性
- **THEN** 审计器标记 B0/B1（按锁定项规则）并阻止发布，即使正文内容正确

### Requirement: Section-specific content and layout audit
审计器 MUST 对 Section 2、3、8、9、11 和 14 执行专门检查：Section 2 象形图、GHS 标签换行和无数据行排序；Section 3 每个成分一行；Section 8 手部防护和 8.2 工程控制及父项锁定；Section 9 无数据项不展示并重新排序；Section 11 结构化毒理至 11.10 且不得抹除已有数据；Section 14 严格换行。

#### Scenario: Section 2 pictogram and label fields are valid
- **WHEN** 源数据要求 GHS 象形图或标签有害成分提示
- **THEN** 输出包含对应完整象形图和按模板固定格式换行的标签内容，且无“见 2.4-2.6”等把用户引向不可见位置的替代说明

#### Scenario: Section 3 keeps one ingredient per row
- **WHEN** 输出包含多个成分或成分数据缺失
- **THEN** 每个成分恰好占一行；缺失值使用“无数据”而不是“无数据资料”或来源未提供等草稿性说明

#### Scenario: Section 9 omits absent properties
- **WHEN** Section 9 某物性项目没有源数据
- **THEN** 该项目行不展示，剩余项目按连续且符合模板的顺序重排

#### Scenario: Section 11 retains supported toxicology
- **WHEN** 源文件存在急性毒性、刺激性或其他 11.x 数据
- **THEN** 对应结构化字段保留经原文归纳的事实，不得错误输出“无数据”，也不得增加未经要求的推断

#### Scenario: Section 14 line breaks are compliant
- **WHEN** 输出包含运输信息的多项字段
- **THEN** 每个字段按固定模板标签和要求的换行边界呈现，且 CN/EN 四个公司变体遵守同一换行契约

### Requirement: Four-format semantic and company parity
审计器 MUST 对 CN/EN × 冠志/国彩四种格式分别检查内容完整性，并 MUST 检查公司变体只改变获准的公司信息、语言变体只改变受控翻译内容；不得因改公司或改语言而产生结构、事实或标签骨架漂移。

#### Scenario: Four variants remain semantically equivalent
- **WHEN** 一个产品生成四个 DOCX 变体
- **THEN** 四个变体的产品事实、章节结构、危险性分类和固定标签语义一致，仅公司字段和语言字段按规则变化

#### Scenario: Company-specific leakage occurs
- **WHEN** 冠志版本出现国彩公司信息，或国彩版本出现冠志公司信息
- **THEN** 审计器标记 B1 并阻止发布，同时给出变体、字段和证据路径

### Requirement: DOCX-derived PDF and visual QA
审计器 MUST 确认 PDF 是对应最终 DOCX 的转换产物，而非另行重建；PDF 页数、页面尺寸、文本可提取性、空白页/零字节异常、象形图和关键 Section 的可见版式 MUST 通过自动与逐页 QA。

#### Scenario: PDF is derived from final DOCX
- **WHEN** DOCX 已完成内容和模板审计，且同一矩阵位置有 PDF
- **THEN** 报告记录 DOCX/PDF 配对、转换时间或来源证据、页数和渲染检查结果，并继续到逐页检查

#### Scenario: PDF cannot be traced or has layout failure
- **WHEN** PDF 无法追溯到对应最终 DOCX，或出现空白页、截断、关键表格溢出、象形图缺失或页数异常
- **THEN** 审计器标记 B0/B1 并阻止发布

### Requirement: Evidence-complete machine-readable audit report
每条审计规则 MUST 生成版本化证据记录，至少包括 `rule_id`、`category`、`severity`、`status`、`source_of_truth`、`method`、`pass_condition`、`observed`、`evidence_paths` 和 `message`；最终报告 MUST 同时支持机器读取和用户阅读，并 MUST 显示未通过项而不是只显示总分。

#### Scenario: Successful audit has complete evidence
- **WHEN** 一次完整审计运行结束
- **THEN** JSON 报告包含每个必需规则恰好一条结果、汇总分数、阻断项、最终 outcome、输入身份和证据路径，并能生成对应的人类可读报告

#### Scenario: Audit execution is incomplete
- **WHEN** 必需规则因缺文件、工具错误或未执行而没有结果
- **THEN** 报告将其标记为 `NOT_CHECKED` 或 `ERROR`，最终不得为 `RELEASE_PASS`，并明确记录缺失原因

### Requirement: Regression and release gate coverage
MSDS Skill MUST 提供自动化测试覆盖评分边界、阻断优先级、清单完整性、证据 schema、当前 PU-2345/OS-9015 八文件回放和 ZIP 完整性；发布前 MUST 运行 V2.9 inheritance、模板 geometry、semantic/company parity、全部自动测试和逐页 QA。

#### Scenario: Release gate is complete
- **WHEN** V3.4 发布命令执行
- **THEN** 所有 release blocker 检查、自动测试和证据完整性检查均有结果，任意失败都会使发布失败并保留失败证据

#### Scenario: Audit checklist drifts from implementation
- **WHEN** 文档清单中存在没有规则实现或测试覆盖的必需检查项
- **THEN** 清单覆盖审计失败，版本不得发布，直到规则、文档和测试重新对齐
