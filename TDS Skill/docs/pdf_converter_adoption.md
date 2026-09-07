# Word 到 PDF 转换器采用记录

TDS 采用与 MSDS Skill 一致的内置 `scripts/convert_docx_to_pdf.py` 设计，但保持 TDS 独立目录和独立审计链路。

## 采用方案

转换器调用主机的 WPS/Word-compatible `word2pdf`：

- 显式路径优先，其次读取 `WPSCLI_PATH`，再查找 `kwpsconvert.exe`、`wpscli.exe` 和 Windows App Paths 注册表；
- 输入必须是最终 `.docx`，输出必须是 `.pdf`；
- 每个输入 Word 只生成一个同名 PDF；
- 在 PDF 目标目录同卷创建临时目录，成功后使用 `os.replace` 原子替换；
- 输出 JSON 证据，包含两个文件的 SHA-256、转换器版本、页数和禁止独立制作标志。

## 明确拒绝的方案

- LibreOffice `soffice`：不作为 fallback。不同 Office 引擎可能改变页眉位置、分页、继承段落间距、字距和表格几何；
- 直接用 PDF 绘图库重新排版；
- 先制 PDF、再反向修 Word；
- 以 PDF 后处理掩盖 DOCX 渲染问题。

## 构建门禁

`tds_cli.py build` 严格按以下顺序执行：

1. 生成四份 Word；
2. 运行 DOCX-only preflight，失败则不进入 PDF 转换；
3. 对四份 Word 分别调用内置转换器；
4. 将转换证据放入 `audit/pdf_conversion/`；
5. 运行最终八格式审计，校验 Word/PDF 同名配对和双向哈希；
6. 通过后才允许用户进行完整页面视觉复核。
