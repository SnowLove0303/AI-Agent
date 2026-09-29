# Recognition smoke analysis

## Run

- Corpus root: `F:\MSDS覆写\MSDS\TDS MSDS (2)`
- Seed: `20260929`
- Sample: 6 DOCX files, two product-family/layout groups represented by the sampler
- Evidence: `smoke-docx-final/benchmark-summary.json`

## Findings

- All 6 DOCX items completed recognition without Tk or renderer prerequisites.
- Table count/row/merge structure passed for all 6 items after excluding Section 0 header/footer furniture from the body-table comparison.
- Content ordered hashes remained mismatched/partial on all 6 items; normalized ordered similarity ranged from approximately 0.94 to 0.97. The primary cluster is segmentation/order differences between body paragraphs and table-cell records, not source mutation.
- Image parity passed on image-free items and reported mismatches where the source contained an image that the normalized reader record did not expose. Those cases remain actionable recognition gaps; source package media hashes are retained for repair.
- Formatting remained `PARTIAL` because effective Word inheritance and native rendered-page comparison were not requested in the smoke run. This is an evidence limitation, not an accuracy pass.
- A mixed DOC/DOCX/PDF run produced 2 complete DOCX items and 4 explicit `BLOCKED` items: PDF extraction lacks `pdfplumber`, and legacy DOC conversion lacks `pywin32`/Word. No blocked item was treated as recognized.

## Next repair targets

1. Preserve/compare body paragraph/table ordering without converting meaningful line boundaries into false content mismatches.
2. Expand image extraction coverage for pictograms or drawing types retained only in OOXML (`w:pict`/unsupported tags).
3. Install or explicitly provision PDF/DOC adapters before the larger mixed-format run; keep unavailable dimensions marked as such.
