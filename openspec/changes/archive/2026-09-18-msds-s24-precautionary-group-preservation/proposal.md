## Why

Source MSDS files can place `预防措施：`, `事故响应：`, `安全储存：` and `废弃处置：` above their respective P-statements. The current extraction model flattens the P-statements and can discard these source-backed group headings before template overwrite, so a customer-facing Section 2 value loses meaningful GHS organization even though the P-codes remain. This must be corrected now because the maintained template and existing mapping rules already require these headings to remain in the value area when present.

The source heading is a semantic value, not permission to change the maintained template label or numbering. Source S2.4 precautionary content must continue to project into the current fixed template `2.6 防范说明：` value slot.

## What Changes

- Add a source-grounded, ordered precautionary-group representation that binds each recognized group heading to its child P-statements and source locators.
- Update S2 extraction to recognize CN/EN group headings in separate paragraphs, inline text, and mixed line shapes without confusing ordinary prose in other sections with S2 headings.
- Project and translate the grouped value into the existing non-bold Section 2 value cell while preserving group order, complete P-statements, and semantic line breaks.
- Treat orphan headings and source-present-but-output-missing headings as review/blocking conditions; suppress an empty group rather than emitting an isolated heading or blank line.
- Extend source mapping, output traceability, and Section 2 audits so headings cannot be silently classified as `other`, discarded as an unreviewed duplicate, or regenerated from template examples.
- Add CN/EN regression coverage for separated, inline, reordered, absent, orphaned, and mixed heading/P-statement inputs, plus locked-template and whitespace checks.
- Do not modify the maintained DOCX templates, locked labels, sequence text, table topology, merges, columns, boldness, fonts, paragraph properties, or page layout.

## Capabilities

### New Capabilities

- `section2-precautionary-groups`: Source extraction, semantic binding, translation, projection, and traceability of Section 2 precautionary group headings and their P-statements.

### Modified Capabilities

- `deliverable-audit-framework`: Section 2 source-fidelity and release-audit requirements are strengthened so explicit precautionary group headings are retained, ordered, and verified in the fixed value slot.

## Impact

- Affected implementation: `MSDS Skill/scripts/extract_source_facts.py`, `section2_hp_policy.py`, `section2_ghs_policy.py`, `section2_fact_router.py`, and the source/output audit contracts.
- Affected tests and documentation: Section 2 extraction/projection/router regressions and the mandatory overwrite/mapping rules.
- No new runtime dependency and no template replacement.
- Baseline before implementation: repository `HEAD` `3e5eef903da06b249bce3b4fbd43f49b3e97b087` with the pre-existing dirty worktree preserved. Rollback is to restore the affected files from the recorded pre-edit snapshot and retain all unrelated worktree changes; verification is the focused Section 2 test suite plus the pre-edit `git diff --check` result.
