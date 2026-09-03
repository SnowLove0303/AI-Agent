# Built-in template baseline

## Authority
The language-specific files below are the authoritative MSDS templates bundled with this skill:

- CN: `examples/template_reference.docx`
- EN source record: `examples/template_reference_en_source.docx` (byte-preserved copy of the user-supplied file)
- EN maintained baseline: `examples/template_reference_en.docx` (the source record with the approved Section 1.1 capacity repair)

Pinned source filename supplied by the user: `模板_MSDS_CN_冠志.docx`

CN SHA-256: `cbbf558fb6511edecd8b6a44d3e6bde23ce8a01d715e370d5a19ddc1978a1c9c`

EN source SHA-256: `415bcaf73256c17b3707c4d660dc6f5c4b7f69e2ab5d728ec8f3108dde16b569`

EN maintained SHA-256: `b36d542e7e000c7fa979875f127459505dc9f7d9e0b9180ecb1f3856fd74103f`

## Structural baseline
- 16 tables / MSDS sections.
- Table row counts: `10, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2`.
- Section 15 has 9 rows in the current baseline.
- Section 15 has 9 rows and **does include** the row `物质或混合物的相关安全、健康和环保法律法规`. Preserve it exactly as part of the current template.
- Section 11 now has 6 table rows and its current 4-column/merged-cell geometry is authoritative; do not rebuild it from older outputs.
- Section 2 current 16-row table geometry, labels, and spacing are authoritative.
- Section 8 explicitly includes the hand-protection slot and the `8.2 工程控制` row.
- Section 11 explicitly includes the structured toxicology layout through `11.10 附加信息`.
- v3.6.2 border adjustment: Section 8 changes the internal boundaries for the PPE/hand-protection rows to dotted lines and adjusts the surrounding top/bottom boundary edges; Section 11 changes the boundary edges around the introductory/reference-data transition to dotted lines. These are template-owned visual properties and must be retained by fresh-clone generation.
- v3.6.2 audit finding: table count, row counts, column/grid widths, merges, paragraph properties and character properties are unchanged from v3.6.1; only the approved Section 8/11 cell-border geometry and a non-visible footer table-property extension changed.
- `tests/template_snapshot.json` records the CN table/cell merges, grid and cell widths, paragraph/run properties, and header/footer parts.
- `tests/template_snapshot_en.json` records the maintained EN baseline with the same geometry/property coverage.
- The shared logical baseline is 16 tables with row counts `10, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2` and column counts `2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 1, 1`.
- The EN source supplied by the user had nine rows in its first table; `scripts/normalize_en_template.py` adds the missing Section 1.1 row in the maintained copy and preserves the source record unchanged.
- Product-like text embedded in either template is example content only; it is never a source of product facts.

## Replacement procedure
When the user explicitly designates a new approved template as the new built-in baseline:
1. Preserve the supplied source file as an unchanged `*_source.docx` record.
2. Create the maintained language baseline by applying only an approved structural normalization.
3. Update this document's source filenames, SHA-256 values and structural baseline.
4. Regenerate the corresponding language snapshot(s) with `scripts/snapshot_template_geometry.py`.
5. Run locked-label / structural audits against each maintained baseline.
6. Render each template to PNG and visually inspect every page.
7. Update `CHANGELOG.md` and bump the skill version.
8. Rebuild and integrity-test the ZIP.

Regression examples are not template authorities and must never override this file.


## Company variants
Within each language, the Guanzhi and Guocai outputs use the same language-specific template and only a controlled company-profile overlay. `CN_国彩` is not a different structural template, and neither is `EN_国彩`. Do not maintain separate drifting company templates unless the user later supplies and approves a genuinely different layout.
