# Verification report (2026-09-24)

## Result

All four selected models now have 16 non-empty deliverables each (8 MSDS and 8 TDS), for 64 total. All four MSDS matrices have four formal-ready variants. All four TDS release reports are `RELEASE_PASS`; PDFs with more than one page are accepted under the user's latest instruction, and actual page counts are recorded below. All eight original source files retain their pre-processing SHA-256 values.

| Model | MSDS | TDS status | TDS PDF page counts (CN Guanzhi, CN Guocai, EN Guanzhi, EN Guocai) | Workbook status |
|---|---|---|---|---|
| AMP-95 | 8 files; 4 formal-ready | RELEASE_PASS | 2, 2, 1, 1 | 已覆写 |
| BEK-100L | 8 files; 4 formal-ready | RELEASE_PASS | 2, 2, 2, 2 | 已覆写 |
| BEK-200 | 8 files; 4 formal-ready | RELEASE_PASS | 1, 1, 1, 1 | 已覆写 |
| BEK-200L | 8 files; 4 formal-ready | RELEASE_PASS | 2, 2, 2, 2 | 已覆写 |

## Checks

- Each model has exactly four MSDS DOCX + four MSDS PDF and four TDS DOCX + four TDS PDF; all are non-empty.
- Each MSDS `matrix-report.json` records `formal_ready_count=4` and `draft_count=0`. Each TDS `audit/release_report.json` records `RELEASE_PASS`, zero errors, and the actual page count for each PDF.
- Conversion evidence remains in each TDS `audit/pdf_conversion` directory. The audit confirms each PDF is derived from the corresponding final DOCX and its source/output hashes match.
- TDS final-review page images exist for every reported page. The three previously blocked models' all-pages contact sheets were visually checked; multipage continuation is readable, and no clipping or table damage was visible. MSDS output pages had previously been visually checked with no clipping or unintended overflow.
- All eight source SHA-256 values match `TDS MSDS 预处理/batch-rows-2-5-source-manifest.json`; source files were not edited.
- The workbook sheet `MSDS型号清单` was saved and reopened. `L3:L6` all read `已覆写`; the only newly changed cell values were L3, L4, and L6.
- TDS skill release is 1.3.24. Its installed files were not changed; the task-local audit copy and task-local registry record the no-page-limit policy.

## Output roots

- `TDS MSDS 预处理/7 水性助剂 OS等/AMP-95/覆写输出`
- `TDS MSDS 预处理/7 水性助剂 OS等/BEK-100L/覆写输出`
- `TDS MSDS 预处理/7 水性助剂 OS等/BEK-200/覆写输出`
- `TDS MSDS 预处理/7 水性助剂 OS等/BEK-200L/覆写输出`

Full audit evidence is stored under each model's `覆写输出\MSDS` and `覆写输出\TDS` directories.


## Follow-up correction: collocated proofreading files (2026-09-24)

- Per the user's correction, each model's `覆写输出` root now contains byte-identical copies of its original MSDS/TDS sources alongside the 16 final deliverables. All DOCX and PDF deliverables are co-located there; audit evidence remains organized below `MSDS` and `TDS`. The original source files remain untouched.
- The deliverables were moved, not duplicated. All audit path references were updated. The four TDS release audits were rerun from the flat per-model output roots and passed with conversion source/output hash lineage intact.
