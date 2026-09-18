## Purpose

为英文 MSDS 建立源文件可追溯、模板结构锁定且可发布阻断的国际化质量契约，确保英文交付物不泄漏中文或模板示例，不丢失英文产品身份和 Section 2 语义，并保持现有固定表格结构与值区覆写边界。

## ADDED Requirements

### Requirement: Maintained English baseline is sanitized without runtime skeleton mutation

系统 MUST 将经过审核的英文维护模板作为英文 DOCX 的唯一结构基准，并 MUST 将供应的原始英文模板作为不可变源记录保留。活动模板可以在版本迁移中修正模板自身的英文硬编码，但 MUST 保持 16 张表、行容量、列数、合并、宽度、边框、加粗标签和锁定骨架；运行时 Agent MUST NOT 改写锁定标签或表格结构。

#### Scenario: Corrected English baseline is adopted

- **WHEN** a new skill version adopts an English template remediation
- **THEN** the active-template hash/snapshot is updated, the original source-template hash remains traceable, and the geometry/locked-format audit accepts only the corrected active baseline

#### Scenario: Runtime attempts to change an English label

- **WHEN** an English build changes a sequence label, locked label, boldness, merge, row/column structure or other template-owned property
- **THEN** the build is release-blocked and the value-only mutation boundary is reported with evidence

### Requirement: Reviewed English product identity is required

英文正式输出 MUST 在现有 Section 1.1 `Product name` 值区写入来源可追溯、经审核的专业英文产品名，并保留型号后缀规则。缺少、冲突或无法追溯的英文产品名 MUST 在模板克隆前阻止正式构建；系统 MUST NOT 从型号、模板示例或未经审核的词典猜造化学品名称，也 MUST NOT 为此新增或重排表格行。

#### Scenario: Reviewed English product name is projected

- **WHEN** approved English facts contain a traceable product description and model
- **THEN** Section 1.1 contains the professional English product name with the approved model convention, while header/footer identity and all template-owned labels remain valid

#### Scenario: English product name is absent

- **WHEN** approved facts leave the English product name empty, conflicting or unsupported
- **THEN** preflight returns an actionable blocker and no formal English DOCX or PDF is promoted

### Requirement: English semantic translation preserves source meaning and line boundaries

英文投影 MUST 使用受控术语和 Section 2/8/9/11 语义映射，将健康危害路线、标签要素、测试/测量条件和结构化值写入对应现有值区。中文前缀、中文标签词、孤立翻译片段和模板示例事实 MUST NOT 进入客户文件；源数值、代码、单位量级、限定词和有效换行 MUST 保持可追溯，不得通过翻译或排版改写其事实含义。

#### Scenario: Section 2 health routes are translated

- **WHEN** reviewed facts contain route-specific health-hazard values such as inhalation, ingestion, skin, eyes or symptoms
- **THEN** each populated value begins with the approved English route prefix, keeps the source-supported text on the intended logical lines, and no Chinese route prefix remains

#### Scenario: Label ingredients are not confused with signal word

- **WHEN** Section 2 contains a label-ingredient explanation and a separate signal word
- **THEN** the label-ingredient explanation remains in the label-elements value slot, the signal word remains in the signal-word slot, and neither value is cross-routed or flattened

#### Scenario: Source value contains missing data or multiple lines

- **WHEN** an English endpoint is explicitly missing or contains meaningful source line breaks
- **THEN** the existing empty-value/hide-and-renumber policy is applied without leaving orphan labels, blank paragraphs or invented prose, and meaningful lines remain in source order

### Requirement: English value typography inherits maintained prototypes

英文值区写入 MUST 从当前维护英文模板的对应值文本原型继承字体、字号和非粗体/加粗边界；MSDS EN 普通值与正文 MUST 使用 Arial 12 pt，Section 2 健康危害路线前缀 MUST 为 Arial 12 pt 加粗、后续描述 MUST 为 Arial 12 pt 常规。任何新增值文本不得因裸 `cell.text`、未带原型的 `add_run()` 或默认样式回退而使用 10.5 pt、错误字体或错误粗体属性。该规则仅约束值区和经批准的模板迁移，不授权修改锁定标签或表格结构。

#### Scenario: A populated English value matches its prototype

- **WHEN** a reviewed English value is written into a populated or previously empty value cell
- **THEN** its run properties match the maintained value prototype, including Arial 12 pt and the cell's approved boldness boundary, while paragraph/table geometry remains unchanged

#### Scenario: Section 2 route prefix and description are split correctly

- **WHEN** a Section 2 health-route value contains an approved prefix and source-grounded description
- **THEN** the prefix is a separate bold Arial 12 pt run, the description is a regular Arial 12 pt run, and both remain in one logical value line without a Chinese prefix

#### Scenario: Unstyled or mismatched value write is detected

- **WHEN** an output value has 10.5 pt size, Times New Roman in an MSDS EN value cell, a missing `rPr`, or an unexpected boldness change
- **THEN** the typography/locked-format audit emits a blocking finding and the output is not promoted

### Requirement: English terminology and typography are release-blocking

每个英文 DOCX 的正文、页眉和页脚 MUST 通过可执行审计：中文字符残留、模板污染短语、全角冒号、非法/混淆的单位符号、错误章节术语和不一致的企业名称后缀 MUST 产生阻断项。审计 MUST 允许受控的源证据例外仅在明确配置且不属于客户可见值时使用；客户可见英文值区不得静默放过这些问题。

#### Scenario: English output is clean

- **WHEN** all customer-visible English text uses approved terminology, ASCII punctuation and canonical unit typography
- **THEN** the terminology audit passes and records the checked document parts, rules and hashes

#### Scenario: Chinese residue or full-width punctuation is found

- **WHEN** any customer-visible English body/header/footer contains Chinese characters or a full-width colon
- **THEN** the audit emits a blocking finding with location/evidence and the formal matrix is not published

#### Scenario: Unit normalization preserves facts

- **WHEN** an English value contains source-supported temperature, viscosity, density or inequality notation
- **THEN** the output uses the approved presentation form such as `< 500 mPa·s`, `g/cm³` and `°C` without changing the numeric value or comparison meaning

### Requirement: English outputs remain four-variant and evidence-complete

英文冠志/国彩 DOCX 与其 PDF MUST 继续属于同一四变体交付矩阵；语言变化只能影响受控英文内容，公司变化只能影响获准公司信息。英文修复 MUST 在发布证据中记录 active/source template identity, source fact locators, translation rule, output slot, audit result and final DOCX/PDF lineage.

#### Scenario: English variants remain semantically aligned

- **WHEN** one model is built for both English companies
- **THEN** product facts, section order, hazard semantics, locked structure and English quality gates are equivalent, with only approved company fields differing

#### Scenario: Any English gate is incomplete

- **WHEN** a required English terminology, identity, template or lineage check is missing, errors or has no evidence
- **THEN** the release result is `NOT_READY` or `RELEASE_FAIL`, never `RELEASE_PASS`
