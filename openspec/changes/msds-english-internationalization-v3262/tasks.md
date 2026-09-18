## 1. Baseline and rollback safeguards

- [x] 1.1 Record the v3.26.1 baseline revision/package hash in the implementation notes and create a read-only active/source English template comparison report before editing.
- [x] 1.2 Verify the current EN geometry, merges, locked labels, boldness and writable-value registry; add regression assertions that the remediation changes no table count, row capacity, column topology or locked-format boundary.

## 2. English template remediation

- [x] 2.1 Create the corrected active EN template from the maintained source record, removing the reported Chinese header/hand-protection contamination and correcting the Section 6.1 and canonical section labels without changing structure.
- [x] 2.2 Normalize template-owned English punctuation/spacing and generate updated active-template snapshot/hash evidence while preserving the original source-template hash and byte record.

## 3. Reviewed facts and semantic projection

- [x] 3.1 Extend English fact validation/identity mapping so a source-traceable professional product name is required in the existing Section 1.1 value slot and missing/conflicting names block before cloning.
- [x] 3.2 Add controlled English mappings for Section 2 health-route prefixes, label-ingredient prose, canonical section terminology and source-supported test/property conditions; preserve codes, numbers, qualifiers and meaningful line breaks.
- [x] 3.3 Apply the missing-value/hide-and-renumber policy to the updated English values and add regression cases for empty routes, orphan labels, line breaks and label-elements/signal-word separation.
- [x] 3.4 Make production English value writes clone maintained XML style prototypes, including Arial 12 pt ordinary values and bold-prefix/regular-tail Section 2 routes; verify no 10.5 pt, wrong-font, missing-`rPr` or unintended-bold output survives the typography audit.

## 4. Release audits and evidence

- [x] 4.1 Expand the English terminology audit to body, header and footer customer-visible XML, blocking Chinese characters, full-width colons, known template artifacts, non-canonical headings, company suffix drift and invalid unit typography.
- [x] 4.2 Route the new English findings through the existing release-blocker/evidence schema with document-part location, rule id, observed text and evidence path; verify incomplete or failed checks cannot produce `RELEASE_PASS`.

## 5. Regression, documentation and release

- [x] 5.1 Add focused tests and fixtures for PU-series English defects, corrected baseline hashes, product identity, Section 2 routes, Arial 12 pt value typography, bold-prefix/regular-tail runs, punctuation/units, locked structure and no-template-mutation behavior; record the external TDS Times New Roman requirement without implementing TDS production here.
- [x] 5.2 Update `SKILL.md`, English translation resources/runbook, `README.md`, `VERSION.txt`, `CHANGELOG.md` and `manifest.txt` for v3.26.2; explicitly document that TDS production is outside this package.
- [x] 5.3 Run focused tests, the complete MSDS suite, strict OpenSpec validation, `git diff --check`, and an independent extraction/content/test audit of the v3.26.2 ZIP; retain the v3.26.1 package for rollback until acceptance.
