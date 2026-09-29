# Tasks

## 1. Candidate extraction

- [x] 1.1 Restrict delimiter-free adjacent candidates to data-backed values and report mixed-cell suffixes without changing source text; verify Section 8 and Section 3 candidate diagnostics.
- [x] 1.2 Add full-document regression assertions for all sections, including the Section 3 header row and Section 8 exact warning/source retention; verify with `py 检索功能\check_msds_format_reading.py`.

## 2. Integration verification

- [x] 2.1 Verify GUI format metadata exposes the corrected candidates and warning while preserving table layout and text rendering; run `py 检索功能\check_msds_format_reading.py --gui`.
- [x] 2.2 Validate and archive the OpenSpec change; verify strict validation and final project status.
