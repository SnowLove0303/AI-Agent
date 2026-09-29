# Proposal

## Why

型号表序号 2–5（AMP-95、BEK-100L、BEK-200、BEK-200L）目前缺少覆写完成标记。现有预处理目录为每个型号提供一份中文 MSDS 和一份中文 TDS，需要依照各自技能规范生成四个变体的 DOCX 与派生 PDF，并保留源件。

## What Changes

- 每个型号分别处理 MSDS 与 TDS，形成 16 个成品（各 4 个 DOCX、4 个同名 PDF）。
- 将成品与审计资料放入各型号源文件夹下的 `覆写输出\MSDS`、`覆写输出\TDS` 子目录，避免覆盖源文件和已有的历史输出。
- 仅在该型号 16 个成品及必要审计全部通过后，将型号表最后一列写为“已覆写”。

## Capabilities

### New Capabilities

- `msds-tds-batch`：定义本批次的型号选择、源文件保护、八格式交付和状态标记验收条件；不改变软件行为。

### Modified Capabilities

无。

## Impact

- 输入：`型号数据库.xlsx` 中序号 2–5；`TDS MSDS 预处理` 下四个型号目录中的 CN MSDS/TDS 源文件。
- 输出：每型号 16 个 MSDS/TDS 文件、技能要求的审计资料，以及型号表状态单元格。
- 源文件保持原字节不变；模板来自已安装 MSDS/TDS Skill 的受控 active baseline。
