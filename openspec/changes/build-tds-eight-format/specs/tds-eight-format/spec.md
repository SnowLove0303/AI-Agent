# TDS eight-format standardizer

## ADDED Requirements

### Requirement: Four maintained template variants
系统 MUST 内化并独立登记 CN/EN × 冠志/国彩四个用户模板；每个变体 MUST 保存来源文件、来源 hash、active DOCX baseline、snapshot/hash 和适用的字段 registry。

#### Scenario: Four baselines are registered
- **WHEN** 初始化 TDS Skill
- **THEN** 四个变体均有独立来源身份、active DOCX 和结构基线。

### Requirement: One semantic model and one-to-one mapping
一次构建 MUST 只抽取一次源文件并形成一个统一 semantic model；每个输出字段 MUST 映射到一个明确的模板槽位，无法唯一映射或超出模板容量时 MUST fail closed。

#### Scenario: One source maps to four variants
- **WHEN** 同一源文件通过 TDS 构建命令生成四个变体
- **THEN** 四个输出均使用同一个 semantic model，且每个值都有唯一目标槽位。

### Requirement: Fresh-clone in-place overwrite
每份输出 DOCX MUST 从对应 active template fresh clone 生成，只能修改 mutation whitelist 允许的值槽位；不得重建表格或把其他变体模板当作替代基线。

#### Scenario: Skeleton is preserved
- **WHEN** 写入产品数据
- **THEN** 表格、合并、grid width、序号列、标签列、段落字符格式和页眉页脚保持对应模板基线。

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
发布前 MUST 审计模板几何、锁定骨架、白名单变更、源事实保真、CN/EN 语义 parity、冠志/国彩公司 parity、DOCX/PDF 配对、八文件包完整性和证据完整性；任一 B0/B1 阻断失败时 MUST 输出 `RELEASE_FAIL`。

#### Scenario: Blocker takes precedence
- **WHEN** 任一模板基线、受保护骨架、事实隔离或 DOCX/PDF 配对失败
- **THEN** 发布结果为 `RELEASE_FAIL`，不得被分数覆盖。

