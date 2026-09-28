# Proposal

## Why

TDS generation already preserves source hashes and template geometry, but the runtime still permits three failure classes documented in `TDS_Skill_漏洞复盘与架构优化建议.md`: a changed or cross-company template can be used silently, vertical-budget logic can compress body line spacing, and a locked deliverable path can discard the newly generated file. The change closes those release-blocking gaps while preserving the active templates as the sole layout authority.

## What Changes

- Add runtime SHA-256 and company-asset validation for all four registered variants.
- Add a DOCX preflight linter for body-layout inheritance, illegal line breaks, source-output fidelity, and variant assets; run it before PDF conversion.
- Reject complete source clauses copied from another section when they appear in normalized output without target-section evidence.
- Restrict English vertical budgeting to spacing after/before adjustments; preserve body line spacing and line rules.
- Retain generated DOCX/PDF content as a `.pending` sibling when the target is locked, and fail explicitly without overwriting the original.
- Add regression coverage and publish the hardened source package as TDS Skill `1.3.25`.

## Capabilities

### New Capabilities

- `tds-quality-gates`: Runtime template, source-fidelity, layout, asset, and safe-output gates for eight-format TDS delivery.

### Modified Capabilities

- None.

## Impact

- Affected code: `TDS Skill/scripts/tds_common.py`, `overwrite_tds.py`, `audit_tds_eight.py`, `convert_docx_to_pdf.py`, and new `lint_tds_docx.py`.
- Affected contracts: variant registry, manifest, skill documentation, and release metadata.
- No template binary is redesigned; generated product files remain outside the skill package output boundary.
