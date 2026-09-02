# CN PDF layout compatibility regression

## Observed failure

The customer supplied `PU-2345_MSDS_CN_Guanzhi.pdf` as the approved visual
reference. It is a 9-page A4 PDF produced by WPS. The same source/template
content rendered through the available LibreOffice headless engine expanded to
16-17 pages. The expansion was visible as excessive vertical spacing, large
blank areas, repeated table continuation headers, and a footer revision date
wrapping its first character onto a separate line.

This was a renderer-compatibility issue, not permission to remove facts,
collapse Section 11 fields, rebuild tables, or independently author a PDF.

## Controlled correction

After final CN content is written into the fresh template clone, run
`scripts/compact_cn_layout.py`:

- table-body runs are set to 10 pt;
- table-body paragraphs use single line spacing and zero before/after spacing;
- table grid widths, merges, row order and source facts are unchanged;
- bold label paragraph properties remain locked to the template;
- the footer revision-date paragraph's inherited oversized first-line and
  character-based indent attributes are cleared for both language variants,
  keeping `修订日期：2024/8/15` or `Revision date: 2024/8/15` on one line;
- the Section 16 final information row is kept together to prevent a one-line
  orphan at the end of the document.

Table-body compaction is CN-only. Footer normalization is shared by CN and EN
because the same inherited template defect affects both language variants.

## Release evidence

The correction is accepted only after all four final DOCX files and four
derived PDFs are replayed, audited, rendered page by page and checked for
clipping, overlap, broken borders, missing headers/footers, page-number errors,
excessive blank space and material divergence from the supplied reference.
