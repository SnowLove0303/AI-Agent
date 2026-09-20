# Change Proposal: MSDS Unified Typography Enforcement and Independent Row Playbook (v3.26.5)

## Problem
1. When values are written to table cells in python-docx, assigning `cell.text = ...` strips run properties (`<w:rPr>`), leading to missing font sizes (`sz=None`) and fallback font issues.
2. In Section 2.2 GHS Label Elements, intelligent paraphrasing deviated from the source document text for PA-3337A (`羟基丙烯酸酯聚合物GHS危险性分类：不适用\n请注意以下物质：\nN,N-二甲基乙醇胺，中和剂，已键合为盐，质量浓度小于2.0%`).
3. In Section 11 toxicology table, product-level lack of toxicological studies and polymer component lack of data were congested into a single cell/row instead of occupying independent table rows/paragraphs.

## Proposed Resolution
1. **Permanent Unified Value Typography Enforcement**:
   - Provide `set_cell_value_unified(cell, text_or_lines, lang='zh', bold=False, size_pt=12.0)` in `section2_ghs_policy.py`.
   - Clear existing cell paragraphs while preserving/setting `<w:sz w:val="24"/>`, `<w:szCs w:val="24"/>`, `<w:rFonts>` (Arial / 宋体), and bold=False.
   - Enforce single run per paragraph and clean up trailing empty paragraphs.
2. **Verbatim Section 2 Label Element Routing**:
   - Strictly mirror source text verbatim for Section 2.2 in CN and synchronized English.
3. **Independent Row and Paragraph Separation Playbook (`independent_row_playbook.md`)**:
   - Formulate 3 core laws: 主客体分行律 (Subject-Object Separation Law), 分类边界律 (Categorical Boundary Separation Law), and 指标对照分行律 (Metric Pair Separation Law).
   - In Section 11 Table 10, insert independent Row 2 for polymer component data, keeping Row 1 strictly for product-level study status.
4. **Fail-Closed Value Typography Release Audit**:
   - Validate that 100% of value cells across all tables satisfy `sz=24` (12.0 pt) and correct font.
