## Purpose

为 Section 2 防范说明提供可追溯的分组事实表示，使源文件中的预防、事故响应、安全储存和废弃处置小标题与其 P 语句在抽取、翻译、模板覆写和审计中保持顺序与归属。

## ADDED Requirements

### Requirement: Preserve precautionary group structure

当源文件在防范说明区域明确提供分组小标题时，系统 MUST 将每个小标题与其后属于该组的完整 P 语句保存为有序、可追溯的语义结构。小标题和 P 语句 MUST 保留源顺序、源定位和组归属；小标题不得降级为普通 `s2.other` 文本。

#### Scenario: Four source groups are extracted
- **WHEN** the source contains `预防措施：`、`事故响应：`、`安全储存：` and `废弃处置：` with P-statements beneath them
- **THEN** the extracted semantic model contains four ordered groups, each group retains its source heading and its complete child P-statements, and no heading is emitted as an unrelated Section 2 fact

#### Scenario: Headings and P-statements share a source line
- **WHEN** a source cell places a heading, one or more P-statements, and the next heading on the same line or paragraph
- **THEN** the system separates every heading and complete P-statement at semantic boundaries without attaching the next heading to the preceding P-statement

### Requirement: Recognize headings only inside precautionary content

系统 MUST 识别中英文防范说明分组标题、全角/半角冒号和源文件常见换行形态，但 MUST 仅在已经判定为 Section 2 防范说明的内容区域内识别这些标题。其他章节中普通语句包含“预防措施”等词语时，不得被归入 Section 2 防范说明分组。

#### Scenario: Chinese and English heading variants are accepted
- **WHEN** the precautionary content uses Chinese headings or their approved English equivalents with either colon form and arbitrary surrounding whitespace
- **THEN** the headings resolve to the controlled semantic groups `prevention`, `response`, `storage`, and `disposal` while their source text and locator remain available for evidence

#### Scenario: Similar prose outside Section 2 is not captured
- **WHEN** Section 5, 6, 7, or another source section contains ordinary prose mentioning prevention, response, storage, or disposal
- **THEN** that prose remains in its own source section and does not create or alter a Section 2 precautionary group

### Requirement: Project grouped content into the fixed value slot

系统 MUST 将已审核的分组防范说明投影到当前维护模板的固定 Section 2 防范说明值区，并保留组顺序、完整 P 语句和组间语义换行。源文件的 Section 2.4 语义内容 MUST 映射到当前模板拥有的 `2.6 防范说明：` 值区；系统 MUST NOT 改写模板标签、序号、表格结构、合并、列数、加粗属性或其他模板拥有格式。

#### Scenario: Grouped CN content is written
- **WHEN** reviewed Chinese facts contain multiple non-empty precautionary groups
- **THEN** the value cell contains each source group heading followed by its complete P-statements in source order, while the maintained template label remains unchanged and only the non-bold value content is written

#### Scenario: Grouped EN content is translated and written
- **WHEN** reviewed English facts are generated from grouped Chinese/source facts
- **THEN** the output uses the approved heading equivalents `Prevention:`, `Response:`, `Storage:`, and `Disposal:` where those source groups exist, keeps the same P-code order and group membership, and records the translation trace

### Requirement: Hide empty groups and fail closed on structural loss

系统 MUST 在写入前判断每个分组是否有有效、来源可追溯的 P 语句。没有子语句的孤立标题不得写入客户文件；所有子语句为空、缺失或不支持的组 MUST 被隐藏。若源文件明确存在有效分组标题及其 P 语句，而批准事实或输出追溯缺少该组，系统 MUST 阻止正式覆写/发布，而不是静默丢弃、标记为未审查重复或从模板示例补回。

#### Scenario: An empty group is suppressed
- **WHEN** a source group heading has no valid child P-statement after missing-data evaluation
- **THEN** the group heading is omitted without an orphan line or blank paragraph, and the parent Section 2 row is removed only if its entire value is empty

#### Scenario: A source-present group is missing from the approved output
- **WHEN** source evidence proves that a group has at least one valid P-statement but the approved model or output trace does not contain that group
- **THEN** the interpretation/audit result is blocking and no formal deliverable is promoted

### Requirement: Preserve line and provenance invariants

每条 P 语句 MUST 保持其完整代码和正文在同一逻辑行，组标题 MUST 占独立逻辑行，源顺序 MUST 保持不变。系统 MUST 为组标题、P 语句和最终 CN/EN 值记录可关联的事实、源定位、变换方式和目标槽位；P 语句不得被拆成多个语句、重复归组或重新当作 `2.x` 主编号。

#### Scenario: Complete P-statements remain intact
- **WHEN** a group contains combined codes such as `P305+P351+P338` or multiple P-statements
- **THEN** each combined code remains attached to its full statement, each statement occupies one logical line, and no P line consumes a Section 2 parent number

#### Scenario: Traceability is complete
- **WHEN** grouped precautionary content is written to CN and EN output values
- **THEN** the trace identifies the source group/statement facts, the semantic target `precautionary_statements`, the approved language transformation, the line-break policy, and the fixed template value slot
