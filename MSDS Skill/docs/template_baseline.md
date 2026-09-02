# Built-in template baseline

## Authority
The file `examples/template_reference.docx` is the default authoritative Guanzhi Chinese MSDS template bundled with this skill.

Pinned source filename supplied by the user: `模板_MSDS_CN_冠志.docx`

SHA-256: `cbbf558fb6511edecd8b6a44d3e6bde23ce8a01d715e370d5a19ddc1978a1c9c`

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
- `tests/template_snapshot.json` records table/cell merges, grid and cell widths, paragraph/run properties, and header/footer parts.
- Product-like text embedded in this template is example content only; it is never a source of product facts.

## Replacement procedure
When the user explicitly designates a new approved template as the new built-in baseline:
1. Replace `examples/template_reference.docx` with the supplied file bytes.
2. Update this document's source filename, SHA-256 and structural baseline.
3. Regenerate `tests/template_snapshot.json` with `scripts/snapshot_template_geometry.py`.
4. Run locked-label / structural audits against the new baseline.
5. Render the template to PNG and visually inspect every page.
6. Update `CHANGELOG.md` and bump the skill version.
7. Rebuild and integrity-test the ZIP.

Regression examples are not template authorities and must never override this file.


## Company variants
The bundled template remains the structural authority. `CN_国彩` is not a different structural template: it is the same approved structure with a controlled company-profile overlay. Do not maintain separate drifting templates for the two companies unless the user later supplies and approves a genuinely different Guocai layout.
