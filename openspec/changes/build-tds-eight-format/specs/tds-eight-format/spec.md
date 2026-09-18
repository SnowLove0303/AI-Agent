# TDS eight-format standardizer

## ADDED Requirements

### Requirement: Four maintained template variants
系统 MUST 内化并独立登记 CN/EN × 冠志/国彩四个用户模板；每个变体 MUST 保存来源文件、来源 hash、active DOCX baseline、snapshot/hash 和适用的字段 registry。

#### Scenario: Four baselines are registered
- **WHEN** 初始化 TDS Skill
- **THEN** 四个变体均有独立来源身份、active DOCX 和结构基线。

### Requirement: One semantic model and one-to-one mapping
一次构建 MUST 只抽取一次源文件并形成一个分离原始证据与标准化值的统一 semantic model；每个输出字段 MUST 映射到一个明确的模板槽位，无法唯一映射或超出模板容量时 MUST fail closed。标准化值 MUST 保留 provenance、判断理由和决策状态。

#### Scenario: One source maps to four variants
- **WHEN** 同一源文件通过 TDS 构建命令生成四个变体
- **THEN** 四个输出均使用同一个 semantic model，且每个值都有唯一目标槽位。

### Requirement: Evidence-preserving normalization and agent judgment
系统 MUST 将原始抽取证据、标准化语义模型和模板呈现值分层保存。别名、模板示例、历史案例和字段位置只能作为候选线索；Agent MUST 根据源文上下文、强标注框架和目标变体判断抽取边界、归类、限定条件、单位/符号、列表结构及是否需要拆分/合并，并在 decision ledger 中保留来源、理由和置信度。会改变客户含义的未决判断 MUST 阻断发布。

#### Scenario: Candidate alias requires contextual judgment
- **WHEN** 源文件标签命中一个别名，但其限定条件或上下文可能与固定字段不同
- **THEN** 系统保留原始标签和值，记录候选归类和 provenance；Agent 未确认前不得静默改写成模板固定字段。

### Requirement: English derives from normalized model
英文输出 MUST 以标准化 semantic model 的 `normalized_values` 为唯一内容来源并进行专业技术翻译。英文源文件（如有）可以作为目标语言证据和交叉校验，但 MUST NOT 绕过标准化层直接驱动英文模板。译文 MUST 保留事实、数值、单位、否定、范围和限定条件，不得增加源文没有的结论或专业事实。

#### Scenario: English presentation follows standardized facts
- **WHEN** 标准化模型包含中文事实、限定条件和 Agent 确认的英文译文
- **THEN** 四个输出的英文值均来自该模型，模板只提供英文结构和格式；英文源文件与模型不一致时产生审计差异，不可静默覆盖模型。

### Requirement: Fresh-clone in-place overwrite
每份输出 DOCX MUST 从对应 active template fresh clone 生成，只能修改 mutation whitelist 允许的值槽位；不得重建表格或把其他变体模板当作替代基线。表头、列结构、列宽、合并和样式必须保持；性能表数据行区域可按源行数量受控裁剪或追加。

#### Scenario: Skeleton is preserved
- **WHEN** 写入产品数据
- **THEN** 表格、合并、grid width、序号列、标签列、段落字符格式和页眉页脚保持对应模板基线。

### Requirement: Source-led performance-row fidelity
性能表 MUST 按源文件原始行顺序输出；每个输出数据行 MUST 保留源项目名称、限定条件、指标值、单位和测试方法。模板示例指标 MUST NOT 被当作产品事实新增；模板标签 MUST NOT 替换源项目名称。语义限定条件不同的项目 MUST NOT 被映射到同一固定字段。

#### Scenario: PU-1001-style source rows
- **WHEN** 源文件包含“外观、固体份含量、粘度(25℃)、PH值（1:10稀释在水中）、密度(25℃)”五行
- **THEN** 输出性能表按这五行原顺序保留，不能插入不存在的 EEW 行，不能把 pH 的稀释条件改写为 25℃。

#### Scenario: Missing template example metric
- **WHEN** 模板包含源文件没有的固定示例指标
- **THEN** 不得把该示例指标写入产品表；未使用的数据行按源行数量裁剪，或将源行作为受控扩展行追加。

### Requirement: Controlled content capacity extension
性能指标和产品特性 MUST 支持超出当前基线数量的源数据；新增性能指标 MUST 按源顺序克隆模板数据行追加，新增产品特性 MUST 克隆模板特性段落追加。只有新性能行的标签单元格允许写入新字段名；既有骨架和格式 MUST 保持不变，超过显式容量或无法一一映射时 MUST fail closed。

#### Scenario: Additional performance rows are supported
- **WHEN** 源文件包含模板五个基线指标之外的明确性能指标
- **THEN** 系统克隆模板数据行追加该指标，保留列宽、边框、字体和列语义，并在四个变体中保持源顺序与语言对应。

#### Scenario: Additional feature paragraphs are supported
- **WHEN** 源文件包含超过模板两个特性段落的产品特性
- **THEN** 系统克隆模板特性段落追加内容，不重建后续章节，且保留段落样式和用户可读顺序。

### Requirement: Sample fact isolation
模板内产品名、成分、指标、危险性、毒理、生态、公司事实 MUST 被标记为结构样例并从产品 semantic model 排除；输出不得泄漏未由源文件提供的样例事实。

#### Scenario: Template sample is not copied
- **WHEN** active 模板包含示例产品或示例性能指标
- **THEN** 输出只出现源文件提供或规则明确的值，示例值不得作为默认事实。

### Requirement: Eight-file output matrix
一次正式构建 MUST 产生四份 DOCX 和四份同名 PDF：`<MODEL>_TDS_CN_冠志`、`<MODEL>_TDS_CN_国彩`、`<MODEL>_TDS_EN_冠志`、`<MODEL>_TDS_EN_国彩`，每个扩展名各一份，不得缺失、重复或混入其他产品文件。

#### Scenario: Package is complete
- **WHEN** 构建完成
- **THEN** 输出目录恰好包含八个预期交付文件和审计证据。

### Requirement: DOCX-derived PDF
PDF MUST 由对应的最终 DOCX 通过统一转换器派生；系统 MUST 记录配对 hash/来源证据，并阻止独立制作或内容不一致的 PDF。

#### Scenario: PDF is traceable
- **WHEN** 四个 DOCX 完成内容和结构审计
- **THEN** 每个 PDF 均由其对应 DOCX 转换，并在报告中记录来源和转换证据。

### Requirement: TDS audit and release blockers
发布前 MUST 审计模板几何、锁定骨架、白名单变更、源事实保真、性能表逐行 parity、CN/EN 语义 parity、冠志/国彩公司 parity、DOCX/PDF 配对、八文件包完整性和证据完整性；任一 B0/B1 阻断失败时 MUST 输出 `RELEASE_FAIL`。

#### Scenario: Blocker takes precedence
- **WHEN** 任一模板基线、受保护骨架、事实隔离或 DOCX/PDF 配对失败
- **THEN** 发布结果为 `RELEASE_FAIL`，不得被分数覆盖。

#### Scenario: Source-output parity blocker
- **WHEN** 输出性能表的行数、顺序、项目标签、限定条件、指标值、单位或测试方法与源文件不一致
- **THEN** 审计 MUST 输出明确的 parity blocker，并禁止正式发布。

### Requirement: Standard spacing without format loss
模板和覆写引擎 MUST 固化章节标题、正文段落和特性项的标准段前、段后及行间距；审计 MUST 验证 active 模板本身符合该契约。间距整改 MUST NOT 改变字体、字号、字符间距、首行/悬挂缩进、编号、制表位、表格结构或页眉页脚。

#### Scenario: Spacing contract is inherited
- **WHEN** 输出从任一 active 模板 fresh clone 并写入产品文本
- **THEN** 输出沿用模板的字体、字号、缩进和编号，仅在注册的垂直预算触发时调整允许的 `w:spacing` 属性；模板间距契约或受保护格式不符合时审计 MUST 阻断。

### Requirement: Native centering for Chinese product titles
两个中文 active 模板的 `product.title` 段落 MUST 使用原生 `w:jc w:val="center"`，且左缩进 MUST 为零或未定义；标题字体、字号、加粗、字符属性和其他段落属性 MUST 继续继承 active 模板。覆写引擎 MUST NOT 通过固定左缩进模拟标题居中。

#### Scenario: Long Chinese title remains centered
- **WHEN** 长度超过历史示例的中文产品名称写入 `product.title`
- **THEN** 输出标题保持原生居中，不因固定左缩进向右偏移或被挤压；标题契约审计通过。

### Requirement: Uniform inter-section vertical gaps
输出中每个章节有效内容的末端到下一个章节标题之间 MUST 使用统一的受控垂直过渡；正文区域不得保留占位空段或压缩空段制造局部额外留白。审计 MUST 检查章节标题前无残留空段，并验证输出正文区域空段数符合 registry 的 `inter_section_spacing` 契约。该整改 MUST NOT 改变字体、字号、正文内部行距、首行/悬挂缩进、编号、制表位或表格结构。

#### Scenario: Application-to-storage gap matches other section transitions
- **WHEN** 输出包含【应用】与【储存】章节以及其他连续章节过渡
- **THEN** 【应用】末行到【储存】标题的垂直间距不得因历史空段而显著大于其他章节过渡；输出间距审计通过。

### Requirement: Verbatim Chinese source fidelity

中文输出 MUST 继承源文档事实，不得对产品名称、正文、产品特性、应用、储存、性能项目、指标值、单位、测试方法或免责声明进行同义改写、词序调整、技术术语替换、数值变更或内容删减。映射 MUST 保存源事实文件及字段/性能行哈希；中文 `normalized_values` MUST 与 `source_values` 一致，中文覆写 MUST 直接使用源值。生成后的 DOCX MUST 由独立门禁按字段、章节行和性能表行精确回读比对；只允许注册的外层空白收束、列表序号剥离和段落拆分。该门禁失败时 MUST 阻断 PDF 转换和交付包发布。

#### Scenario: Chinese normalization mutation is blocked
- **WHEN** Agent 或脚本将中文源字段改成同义词、不同词序、删减语句或改变技术限定条件
- **THEN** 覆写前映射熔断返回明确的字段/性能行突变错误，且不写入可发布 DOCX。

#### Scenario: Generated DOCX mutation is blocked
- **WHEN** DOCX 中的中文标题、正文或性能表内容与源事实不一致
- **THEN** 生成后忠实度门禁返回明确的输出差异，CLI 不执行 PDF 转换，发布报告为失败。

### Requirement: Graduated English vertical budget
英文高密度内容 MUST 使用注册的 Level 1/Level 2 间距预算，并在生成记录中保留实际级别；Level 1 和 Level 2 的标题/正文间距与行距 MUST 与 registry 一致，且最终页数 MUST 继续满足单页契约。

#### Scenario: Dense English output compresses in two levels
- **WHEN** 英文内容项超过预算阈值
- **THEN** 16 项以内使用 Level 1，超过 16 项使用 Level 2；两级均保留字体、字号、缩进和编号，页数超过上限时发布 MUST 失败。
