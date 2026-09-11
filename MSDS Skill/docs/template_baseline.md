# Built-in template baseline

## Authority
The language-specific files below are the authoritative MSDS templates bundled with this skill:

- CN: `examples/template_reference.docx`
- CN source record: `examples/template_reference_cn_source.docx` (byte-preserved copy of the user-supplied formal template)
- EN source record: `examples/template_reference_en_source.docx` (byte-preserved copy of the user-supplied formal template)
- EN active baseline: `examples/template_reference_en.docx` (current user-supplied formal template, byte-for-byte)
Historical rollback copies are not shipped in the active skill package.

Pinned source filenames supplied by the user: `正式模板_MSDS_CN_冠志.docx` for CN and
`正式模板_MSDS_EN_冠志.docx` for EN.

CN SHA-256: `b6c52c3d6003d4314e578733c5066dc9541c70ee49957ab56c24dd749ade2d43`

EN source SHA-256: `34a259eed50d2e78b4609c66453fa9baab610a623dcc7ee531db359b1a988497`

EN active SHA-256: `34a259eed50d2e78b4609c66453fa9baab610a623dcc7ee531db359b1a988497` (current user-supplied formal template)

## Structural baseline
- 16 tables / MSDS sections.
- CN table row counts: `10, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2`.
- EN table row counts: `9, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2`.
- CN and EN intentionally retain different physical structures. The same semantic model and overwrite rules are projected into each language's existing slots.
- Section 15 has 9 rows in the current baseline.
- Section 15 has 9 rows and **does include** the row `物质或混合物的相关安全、健康和环保法律法规`. Preserve it exactly as part of the current template.
- Section 11 now has 6 table rows and its current 4-column/merged-cell geometry is authoritative; do not rebuild it from older outputs.
- Section 2 current 16-row table geometry, labels, and spacing are authoritative.
- Section 8 explicitly includes the hand-protection slot and the `8.2 工程控制` row.
- Section 8.2 uses the formal top-level four-column control-parameter rows: a one-cell `工作场所组分控制参数` (EN `Control parameters for workplace components`) parent row, one locked header row (`物质 / 依据 / 类型 / 数值`; EN `Substance / Basis / Type / Value`), then data rows. The two template example OEL rows are illustrative only and must be cleared. With verified source records they are replaced by source data rows (cloned in place when more records exist); with no verified records the complete workplace-component block is hidden, including its parent, header and data rows. Never emit a synthetic missing-data row for an absent workplace-parameter block.
- Section 11 explicitly includes the structured toxicology layout through `11.10 附加信息`.
- v3.6.2 border adjustment: Section 8 changes the internal boundaries for the PPE/hand-protection rows to dotted lines and adjusts the surrounding top/bottom boundary edges; Section 11 changes the boundary edges around the introductory/reference-data transition to dotted lines. These are template-owned visual properties and must be retained by fresh-clone generation.
- v3.6.2 audit finding: table count, row counts, column/grid widths, merges, paragraph properties and character properties are unchanged from v3.6.1; only the approved Section 8/11 cell-border geometry and a non-visible footer table-property extension changed.
- `tests/template_snapshot.json` and `tests/template_snapshot_en.json` record the active CN/EN table/cell merges, grid and cell widths, paragraph/run properties, and header/footer parts. Historical versioned snapshots are not shipped and are never template authorities.
- Both language baselines have 16 tables and column counts `2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 1, 1`; their row capacities differ only where the supplied templates differ.
- The current CN and EN source records supplied by the user are used as-is. The EN source has nine rows in its first table and its Section 11 sublabels are `Oral:`, `Inhalation:`, `Dermal:`, `Fertility:`, `Teratogenicity:` and `In vitro genotoxicity:`.
- Product-like text embedded in either template is example content only; it is never a source of product facts.
- The active CN and EN formal templates allow their tables to span pages. Their row-level `w:cantSplit` settings are retained as supplied by the current baseline (including the intentional settings in Sections 2, 6 and 11), and repeating section headers remain controlled by `w:tblHeader`. These are template baseline properties, not post-generation layout patches.

## Replacement procedure
When the user explicitly designates a new approved template as the new built-in baseline:
1. Preserve the supplied source file as an unchanged `*_source.docx` record.
2. Install the supplied language template byte-for-byte as the active baseline; do not normalize it to the other language.
3. Update this document's source filenames, SHA-256 values and structural baseline.
4. Regenerate the corresponding language snapshot(s) with `scripts/snapshot_template_geometry.py`.
5. Run locked-label / structural audits against each active language baseline.
6. Render each template to PNG and visually inspect every page.
7. Update `CHANGELOG.md` and bump the skill version.
8. Rebuild and integrity-test the ZIP.

Regression examples are not template authorities and must never override this file.


## Company variants
Within each language, the Guanzhi and Guocai outputs use the same language-specific template and only a controlled company-profile overlay. `CN_国彩` is not a different structural template, and neither is `EN_国彩`. Do not maintain separate drifting company templates unless the user later supplies and approves a genuinely different layout.
