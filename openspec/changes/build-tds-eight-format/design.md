# Design: Independent TDS mapping and eight-format build

## Repository boundary

唯一代码根为 `F:\APP Location\Guanzhi Tong\Skill\覆写技能\AI-Agent`。新增内容仅在 `TDS Skill\`；`MSDS Skill\` 作为既有独立模块保持不变。四个 `.doc` 来源文件从用户指定资料目录复制为只读模板来源，转换后的 `.docx` 只作为 TDS active baseline。

## Data flow

```text
source DOC/DOCX
  -> one extraction
  -> normalized TDS semantic model
  -> four variant mappings (CN/EN x Guanzhi/Guocai)
  -> fresh clone of each active DOCX template
  -> whitelist-controlled in-place value overwrite
  -> template/semantic audit
  -> DOCX-derived PDF
  -> pair audit + eight-file package audit
```

模板负责结构、固定标签、页眉页脚、语言和公司骨架；源文件负责产品事实；映射层只负责把事实送入当前模板已经存在的槽位。字段无法唯一匹配、模板容量不足或出现未授权结构变化时立即失败，不猜测、不扩表。

## Variant identity

每个变体使用独立 `variant_id`、源文件 hash、active DOCX hash、snapshot 和 field registry：

- `TDS_CN_Guanzhi`
- `TDS_CN_Guocai`
- `TDS_EN_Guanzhi`
- `TDS_EN_Guocai`

CN/EN 的翻译由受控字段规则生成；公司差异来自各自模板和 company overlay。四变体不得维护四份独立产品事实。

## Mutation and release rules

- 只允许修改 registry 明确的值槽位；序号、标签、表格行列、合并、grid width、段落/字符格式和页眉页脚均受保护。
- 缺失事实按 TDS 规则输出 `无数据` / `No data available`，但不复制模板示例值。
- 只在 DOCX 完成内容和结构审计后转换 PDF；PDF 不接受独立内容编辑。
- 发布包必须恰好包含八个矩阵文件及机器可读审计证据，阻断项优先于分数。

