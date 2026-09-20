# Change Proposal: Adopt Standard EN Master Template & 12-Row Geometry Baseline (v3.27.0)

## Problem
1. The previous English MSDS template baseline suffered from an extra 8th blank page overflow in native WPS rendering due to trailing empty paragraph height.
2. Section 8 (Table 7) in the previous template contained 16 rows including unused occupational exposure limit rows, whereas the user's standardized master uses a streamlined 12-row engineering controls structure.
3. User issued a strict requirement: bold font styling and cell formatting across all 16 tables must be 100% immutable and preserved, prohibiting global string replacements that destroy Word run boundaries.
4. Residual Chinese annotations in Table 7 Row 3 must be cleanly eliminated while retaining field label styling.

## Proposed Resolution
1. Adopt user's standardized master template `"D:\应用缓存\Edge\模板_MSDS_EN_冠志 - 副本.docx"` as official baseline (`examples/template_reference_en.docx`).
2. Update Section 8 geometry to 12 rows across `template_runtime.py`, `section_overwrite_rules.py`, and test assertions.
3. Lock all 325 bold runs across 16 tables. Value writes inherit non-bold formatting from target cells without mutating labels.
4. Clean Table 7 Section 8.2 residual Chinese characters, enforcing a strict 0 Chinese character gate.
5. Apply 1pt micro line height to trailing document paragraph, ensuring deterministic 7-page PDF output.
6. Verify full 258 pytest suite (100% pass) and compile 16 deliverables for benchmark model PA-3337A.
