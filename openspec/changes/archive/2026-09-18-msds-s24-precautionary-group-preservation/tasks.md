## 1. Baseline and model boundary

- [x] 1.1 Preserve the pre-edit hashes and copies of every affected implementation/test/contract file in a task-scoped temporary backup, record the backup path and rollback command in evidence, and verify the baseline with `git diff --check`
- [x] 1.2 Define the reviewed precautionary-group data shape, controlled group keys, CN/EN heading map, compatibility behavior for legacy flat `p_statements`, and source/output trace fields; verify the shape is represented in the new and modified OpenSpec specs without changing template ownership

## 2. Source extraction and semantic grouping

- [x] 2.1 Implement boundary-aware CN/EN heading recognition scoped to the Section 2 precautionary region, including full-width/half-width colons, whitespace, separate paragraphs, and inline headings; verify non-S2 prose is not recognized as a group
- [x] 2.2 Update Section 2 extraction to emit ordered group records with source locators and complete child P-statements while retaining a safe legacy flat projection; verify headings no longer enter `s2.other`
- [x] 2.3 Preserve combined P codes, source order, and logical line boundaries when headings occur before, between, or after P-statements; verify no next heading is appended to the preceding P sentence
- [x] 2.4 Add source mapping and Section 2 routing validation for grouped facts, including group membership, exclusive target ownership, and blocking of source-present groups that have no reviewed disposition

## 3. Projection, translation, and overwrite safety

- [x] 3.1 Implement grouped precautionary rendering for the fixed Section 2 value slot, retaining only non-empty groups and suppressing orphan headings/blank lines; verify the parent row is hidden only when the entire value is empty
- [x] 3.2 Integrate controlled CN-to-EN heading translation and output traceability while preserving P-code order and group membership; verify missing source headings are never invented from template examples
- [x] 3.3 Keep the existing value-cell-only writer and post-omission ordering, and assert the maintained template `2.6 防范说明：` label, numbering policy, run formatting, table topology, merges, columns, and bold locks are unchanged
- [x] 3.4 Add an output audit that compares source-proven group presence and order with CN/EN values and blocks silent loss, wrong-target routing, duplicate groups, or malformed logical lines

## 4. Regression coverage and contract documentation

- [x] 4.1 Add extractor regressions for four separated headings, inline/mixed lines, heading-after-P boundaries, no headings, orphan headings, and false positives outside Section 2; verify source order and locators
- [x] 4.2 Add CN/EN projection and overwrite regressions for grouped output, empty-group suppression, no artificial blank lines, non-bold writable values, and immutable template labels/geometry
- [x] 4.3 Add routing/traceability regressions for missing group evidence, silently dropped groups, duplicated target use, and approved translated output; verify failures are fail-closed
- [x] 4.4 Update the public Section 2 mapping, source interpretation, overwrite, and QA documentation to make explicit group retention a mandatory rule; verify the docs preserve the distinction between source S2.4 semantics and the current template `2.6` label

## 5. Verification and release readiness

- [x] 5.1 Run focused Section 2 extraction, policy, projection, router, and regression tests and verify all grouped scenarios pass
- [x] 5.2 Run the complete `py -m pytest -q "MSDS Skill/tests"` suite, `openspec validate "msds-s24-precautionary-group-preservation"`, and relevant whitespace/locked-skeleton audits; verify no template hash or unrelated worktree changes are introduced
- [x] 5.3 Perform a final scope/rollback audit, retain the old package archives, and record that packaging, commit, push, and deletion remain acceptance-gated until the user explicitly accepts the result
