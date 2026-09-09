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

## Current policy

The historical compaction pass is retained only as regression evidence. It is
not part of the active overwrite path. The current release rule is stricter:
the fresh-cloned formal CN template remains authoritative for table-body and
footer formatting, and any global font/spacing/indent normalization is a
release blocker. Renderer differences must be handled by the approved native
WPS/Word rendering path or by an explicitly approved template revision, never
by silently changing the DOCX layout.

## Release evidence

The correction is accepted only after all four final DOCX files and four
derived PDFs are replayed, audited, rendered page by page and checked for
clipping, overlap, broken borders, missing headers/footers, page-number errors,
excessive blank space and material divergence from the supplied reference.
