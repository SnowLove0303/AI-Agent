# PDF 发布契约

TDS 的 PDF 必须严格派生自四份最终 Word 主文件。唯一允许的路径是：

```text
最终 DOCX 覆写
  → DOCX preflight
  → 中文源事实忠实度门禁
  → 内置 Word/WPS-compatible word2pdf 转换器
  → PDF 来源/哈希/page-count 审计
  → PDF 页面视觉复核
  → 八格式发布门禁
```

硬性规则：

- 先完成 Word，再转换 PDF；不能先做 PDF 再回填 Word。
- 中文源事实忠实度门禁未通过时不得转换 PDF 或形成交付 ZIP；允许的列表序号剥离、外层空白收束和段落拆分之外，正文、标题和性能表必须逐项与源事实一致。
- `scripts/convert_docx_to_pdf.py` 每次只接收一个已经完成的 `.docx`，输出一个同名 `.pdf`。
- 转换器使用主机 WPS/Word-compatible `kwpsconvert.exe` 或 `wpscli.exe` 的 `word2pdf` 接口。
- 转换通过同卷临时文件完成，成功后原子替换目标 PDF，避免生成半成品客户文件。
- 转换必须写出 source DOCX hash、output PDF hash、converter version、page count 和 `source_is_final_docx` 证据。
- 禁止 LibreOffice fallback、第二套渲染器、独立 PDF 排版、PDF 后编辑和 PDF 内容分支。
- 最终审计必须校验 conversion evidence 的 source path、source hash、output hash、`source_is_final_docx=true` 和 `independent_pdf_authoring=false`。

如果 WPS converter 不存在、Word/PDF 哈希不匹配、证据缺失或转换失败，发布必须 fail closed；不能用另一套渲染器“补出一个能用的 PDF”。
