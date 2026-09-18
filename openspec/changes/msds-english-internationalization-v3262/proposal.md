## Why

The PU-series review found recurring English MSDS defects that are systemic rather than product-specific: Chinese text leaks from the maintained English template, several fixed labels use incorrect or non-standard English, Section 2.8 route prefixes can remain Chinese, and English values can retain Chinese punctuation or inconsistent unit typography. The current product-identity contract also deliberately leaves the English `Product name` value blank, which conflicts with the reviewed delivery requirement. These defects must be corrected at the maintained-template, reviewed-facts, and release-audit boundaries before the next English batch is generated.

## What Changes

- Create a sanitized active English template baseline while preserving the supplied English template as an immutable source record; keep the 16-table geometry, row capacity, merges, widths, locked labels, and boldness contract unchanged.
- Correct template-owned English artifacts at baseline level, including the header/title text, the Section 8 hand-protection label, the Section 6.1 label, standard Section 1/6/7/11/14 headings, and full-width colon usage. Runtime agents still may not rewrite locked labels.
- Replace the current blank-English-product-name policy with a reviewed-fact requirement for a professional English product name in the existing Section 1.1 value cell; do not synthesize a name from an unsupported dictionary or change the table structure.
- Add controlled English normalization for Section 2 health-route prefixes, ordinary labels, punctuation, spacing, and source-supported unit/temperature notation while preserving numeric facts and qualifiers.
- Make every newly written MSDS EN value inherit the maintained value-cell style prototype: Arial 12 pt for ordinary values, with Section 2 health-route prefixes bold and their descriptions regular at the same 12 pt size; prohibit unstyled direct cell/paragraph replacement.
- Add release-blocking audits for Chinese characters in English DOCX body/header/footer, full-width punctuation in English labels/values, known template contamination, required product identity, and approved terminology/units.
- Add regression fixtures and tests for PU-1001 through PU-1004-shaped English content, empty-value handling, line breaks, locked-label preservation, template hashes/geometry, and fail-closed behavior.
- Keep TDS production out of scope because no TDS production mapper exists in this MSDS repository; document the report's TDS findings as an external follow-up rather than silently claiming they are fixed here.
- Bump the maintained skill package version and changelog to `3.26.2` only after the implementation, package extraction test, OpenSpec validation, and full test suite pass.

## Capabilities

### New Capabilities

- `english-internationalization`: Source-grounded English MSDS template remediation, reviewed product-name projection, controlled terminology/typography normalization, and fail-closed English-language release auditing.

### Modified Capabilities

- `deliverable-audit-framework`: English deliverables gain mandatory Chinese-residual, punctuation/typography, template-contamination, and product-identity release blockers with evidence-complete results.

## Impact

- Affected assets: `MSDS Skill/examples/template_reference_en.docx`, its English snapshot/hash contract, the preserved `template_reference_en_source.docx` evidence record, English normalization, value-style and identity helpers, the MSDS pipeline's release gates, translation resources, tests, documentation, `VERSION.txt`, `CHANGELOG.md`, `manifest.txt`, and the v3.26.2 package.
- External interface: reviewed facts must provide a source-grounded English product name before an English formal build is allowed; missing or unresolved English values remain non-publishable rather than being guessed.
- Rollback baseline: repository revision `e3ce23706f56d0e9c3791b3361cd005fa90576cf` (v3.26.1) and the retained package `MSDS Skill/release/MSDS/msds_unified_eight_deliverable_skill_v3.26.1-full-package.zip` (SHA256 `4CD4C28FC8C0486D198A3996288F87D2071F65F8FD8026C0AEC582FECB60CEDC`). Rollback is by reverting the v3.26.2 commit or restoring that package; verification is the v3.26.1 package test suite plus the existing strict OpenSpec and release-audit checks.
