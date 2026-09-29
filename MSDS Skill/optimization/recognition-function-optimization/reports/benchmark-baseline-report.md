# MSDS recognition benchmark report

## Corpus and replay identity

- Corpus: `F:\MSDS覆写\MSDS\TDS MSDS (2)`
- Corpus manifest: 3,419 files, captured in `corpus-manifest.json`
- Benchmark seed: `20260929`
- Recognizer: `scripts/msds_table_search.py` at the repository baseline recorded in `repository-baseline.json`, plus the VML image fix in this change
- Comparator schema: `recognition-comparator-v1`
- All benchmark outputs are outside the corpus.

## Smoke run

The six-DOCX smoke run is in `smoke-docx-fixed-v2/benchmark-summary.json`.

- All six items completed recognition.
- Body table counts, row counts, columns and merge structure passed.
- Image parity passed after adding VML `v:imagedata` extraction and preserving images from header/footer text records.
- Content remains a mismatch/partial cluster in the current comparator because source body paragraph/table ordering and logical line boundaries differ; each item retains source/recognized hashes and per-item evidence.
- Formatting is `PARTIAL` until native Word/WPS rendering is enabled; no formatting parity pass is claimed from normalized properties alone.

## Larger mixed-format run

The 30-item run is in `benchmark-large/benchmark-summary.json`:

| Extension | Selected | Complete | Blocked |
|---|---:|---:|---:|
| DOCX | 10 | 9 | 1 |
| DOC | 10 | 0 | 10 |
| PDF | 10 | 0 | 10 |

The 9 complete DOCX items all passed table structure and image parity where applicable, while content/order and native-format dimensions remain explicitly reported. The blocked items were not treated as recognition passes.

## Environment gaps

- PDF extraction requires `pdfplumber` in the active Python environment.
- Legacy DOC conversion requires `pywin32` plus Microsoft Word/WPS automation.
- One DOCX exposed an unsupported structure and was recorded as `BLOCKED` rather than partially accepted.

## Targeted fix

The source sample exposed header images stored as legacy VML `v:imagedata` rather than DrawingML `a:blip`. `scripts/msds_table_search.py` now extracts those images, and the regression test covers image preservation from text records. The same fixed seed was replayed after the change.

## Release boundary

This benchmark validates recognition evidence only. It does not claim customer MSDS/TDS eight-file release readiness and does not modify the corpus.
