# Design: Unified Typography & Independent Row Playbook Architecture

## 1. Value Cell Typography Engine
- Function: `set_cell_value_unified(cell, text_or_lines, lang='zh', bold=False, size_pt=12.0)`
- Guarantees:
  - Single run per paragraph (`len(p.runs) == 1`).
  - Strict `<w:sz w:val="24"/>` (12.0 pt).
  - Explicit font family (`Arial` for EN/numbers, `SimSun`/宋体 for East Asian).
  - Explicit bold property (`r.font.bold = bold`).
  - No trailing empty paragraphs in cell (`len(cell.paragraphs) == len(lines)`).

## 2. Independent Row Separation Engine
- Table 10 (Section 11) Row 1: Product-level statement (`该产品无可用的毒理学研究。` / `No toxicological studies are available on the product itself.`).
- Table 10 Row 2: Deep-copied independent row for polymer tier (`羟基聚丙烯酸酯分散体：\n毒性：无资料；刺激性：无资料。`).
- Preserves full column widths, border styles, and XML grid alignment.

## 3. Release Audit Gate
- `audit_value_cell_typography(docx_path)` traverses all tables and cells, ensuring zero typography degradation.
