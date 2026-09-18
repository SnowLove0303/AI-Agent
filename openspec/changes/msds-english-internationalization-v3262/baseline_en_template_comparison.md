# v3.26.2 English Template Baseline Comparison

## Baseline

- Repository revision: `e3ce23706f56d0e9c3791b3361cd005fa90576cf`
- Retained rollback package: `MSDS Skill/release/MSDS/msds_unified_eight_deliverable_skill_v3.26.1-full-package.zip`
- Rollback package SHA256: `4CD4C28FC8C0486D198A3996288F87D2071F65F8FD8026C0AEC582FECB60CEDC`
- Supplied source template: `MSDS Skill/examples/template_reference_en_source.docx`
- Active baseline before remediation: `MSDS Skill/examples/template_reference_en.docx`
- Source and active baseline before remediation were byte-identical:
  `34a259eed50d2e78b4609c66453fa9baab610a623dcc7ee531db359b1a988497`

## Read-only structural findings

- Table count: `16`
- Row counts: `[9, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2]`
- Maximum column counts: `[2, 2, 3, 2, 2, 2, 2, 5, 2, 2, 4, 2, 2, 2, 1, 1]`
- The active template contains the reported Chinese header, the contaminated Section 8 hand-protection label, and the incorrect Section 6.1 label.
- The English product-name value slot exists in the current geometry and is empty by policy; no new row is required.

## v3.26.2 candidate result

- Candidate generated from the preserved source template by
  `MSDS Skill/scripts/remediate_en_template.py`.
- Candidate hash used for this comparison:
  `49a279aa8c7a50f38ee6929ca2f030cf13b01ee0d1e476d790a2352a316bfa2b`
- Table/row/column geometry: `True` (unchanged).
- Cell grid and cell-property geometry: `True` (unchanged).
- Paragraph and run formatting properties for corresponding existing runs:
  unchanged except for the five explicitly approved health-hazard route-prefix
  runs, which are translated to English and promoted to the locked bold
  prototype required by the value-typography policy.
- Changed customer-visible text cells: `103`, limited to the approved English
  template remediation (header, canonical headings, labels, punctuation,
  contaminated hand-protection/Section 6.1 literals, and five health-hazard
  route prefixes).
- Corrected values include `SAFETY DATA SHEET`, `Version: 1.0`,
  `Personal precautions, protective equipment and emergency procedures:`, and
  `Hand protection:`.

## Visual verification note

The required `render_docx.py` visual render was attempted twice, but the
workspace has no bundled or PATH-resolvable `soffice.exe`. No rendered PNG/PDF
was claimed as passed. Structural OOXML and format-anchor checks remain the
blocking pre-promotion checks until a renderer is available.
