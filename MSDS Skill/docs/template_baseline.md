# Built-in template baseline

## Authority
The language-specific files below are the authoritative MSDS templates bundled with this skill:

- CN: `examples/template_reference.docx`
- EN source record: `examples/template_reference_en_source.docx` (byte-preserved copy of the latest user-supplied file)
- EN active baseline: `examples/template_reference_en.docx` (byte-identical to the latest user-supplied EN template)
- Previous v3.11 EN baseline: `examples/archive/template_reference_en_v3.11_pre_field_update.docx` (rollback/audit only; not active)
- Historical normalized EN baseline: `examples/archive/template_reference_en_v3.10_normalized.docx` (retained for rollback/audit only; not active)

Pinned source filenames supplied by the user: `模板_MSDS_CN_冠志.docx` for CN and
`模板_MSDS_EN_冠志 - 副本.docx` for EN.

CN SHA-256: `cbbf558fb6511edecd8b6a44d3e6bde23ce8a01d715e370d5a19ddc1978a1c9c`

EN source SHA-256: `2f287b544705d0db7ff724610c6f7878a88ff2912bbf074151e107f36a588a0e`

EN active SHA-256: `2f287b544705d0db7ff724610c6f7878a88ff2912bbf074151e107f36a588a0e`

## Structural baseline
- 16 tables / MSDS sections.
- CN table row counts: `10, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2`.
- EN table row counts: `9, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2`.
- CN and EN intentionally retain different physical structures. The same semantic model and overwrite rules are projected into each language's existing slots.
- Section 15 has 9 rows in the current baseline.
- Section 15 has 9 rows and **does include** the row `物质或混合物的相关安全、健康和环保法律法规`. Preserve it exactly as part of the current template.
- Section 11 now has 6 table rows and its current 4-column/merged-cell geometry is authoritative; do not rebuild it from older outputs.
- Section 2 current 16-row table geometry, labels, and spacing are authoritative.
- Section 8 explicitly includes the hand-protection slot and the `8.2 工程控制` row.
- Section 11 explicitly includes the structured toxicology layout through `11.10 附加信息`.
- v3.6.2 border adjustment: Section 8 changes the internal boundaries for the PPE/hand-protection rows to dotted lines and adjusts the surrounding top/bottom boundary edges; Section 11 changes the boundary edges around the introductory/reference-data transition to dotted lines. These are template-owned visual properties and must be retained by fresh-clone generation.
- v3.6.2 audit finding: table count, row counts, column/grid widths, merges, paragraph properties and character properties are unchanged from v3.6.1; only the approved Section 8/11 cell-border geometry and a non-visible footer table-property extension changed.
- `tests/template_snapshot.json` records the CN table/cell merges, grid and cell widths, paragraph/run properties, and header/footer parts.
- `tests/template_snapshot_en.json` and `tests/template_snapshot_en_v312.json` record the exact active EN baseline with the same geometry/property coverage.
- Both language baselines have 16 tables and column counts `2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 1, 1`; their row capacities differ only where the supplied templates differ.
- The EN source supplied by the user has nine rows in its first table and is used as-is. Its Section 11 sublabels are `Oral:`, `Inhalation:`, `Dermal:`, `Fertility:`, `Teratogenicity:` and `In vitro genotoxicity:`. `scripts/normalize_en_template.py` is retained only as a historical migration utility and must not run in the active v3.12 generation path.
- Product-like text embedded in either template is example content only; it is never a source of product facts.

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
