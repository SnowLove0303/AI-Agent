# PU-3011 workflow studies

These are the reports from the recognition review and two workflow timing
studies for source `PU-3011 msds_CN 冠志.docx`.

## Reports

- `recognition-and-review-time-analysis.md` — recognition accuracy and review
  time observations.
- `phase-timings.json` and `timing-and-blocker-report.json` — measured machine
  phases and blocker history from earlier diagnostic runs.
- `workflow-stage-decomposition.md` and `workflow-stage-benchmark.json` —
  stage-level decomposition and three-run DOCX-only diagnostic benchmark.
- `timing-report.md` and `timing-ledger.json` — fresh end-to-end run on
  2026-09-28, with the full wall-clock ledger.

## Evidence limits

The fresh end-to-end run took 41m55s wall-clock. Only 15.107s of machine
operations and 67.142s of retry overhead were directly timed; Agent active
review was not instrumented and is therefore not reported as a separate
duration. The run stopped at the pre-clone SOP gate and produced no formal
DOCX/PDF matrix. The separate workflow decomposition report covers a
three-run DOCX-only diagnostic build and must not be read as a comparable
baseline-vs-optimized full release benchmark. No speedup claim is made.

Source documents were not copied into this report bundle. The reports include
source hashes and execution evidence; the original source remains in its
existing customer-data location.
