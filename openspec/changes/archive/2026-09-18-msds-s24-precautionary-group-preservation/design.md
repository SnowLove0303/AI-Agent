## Context

See `proposal.md` for the motivation. The current extractor exposes `p_statements` as a flat list, sends non-coded Section 2 lines to `other`, and the fixed-slot projection joins only the flat P list. The helper regex for group headings is therefore insufficient: it handles a leading heading in a narrow utility test but does not preserve headings that occur between P-statements. The maintained template already has a writable value area containing a source-style precautionary heading example, so the change belongs at the semantic extraction/projection boundary rather than in template reconstruction.

The worktree contains unrelated pre-existing modifications and retained package archives. The implementation must not revert or normalize them. Baseline is `HEAD 3e5eef903da06b249bce3b4fbd43f49b3e97b087`; before code edits, copy the affected implementation and test files to a task-scoped temporary backup and record its path in the implementation evidence. Rollback is restoring only those affected files from that backup, then rerunning focused tests and `git diff --check`.

## Goals / Non-Goals

**Goals:**

- Preserve source-present precautionary group headings and their ordered P-statement membership through extraction, reviewed facts, CN/EN projection, overwrite, and audit.
- Keep the current flat `p_statements` compatibility path safe while making the grouped representation authoritative for new extraction output.
- Fail closed when a source-present non-empty group disappears from approved facts or output traceability.
- Hide orphan/empty groups without introducing blank paragraphs, new Section 2 rows, or new parent numbering.
- Add focused CN/EN regression coverage for line shapes, translation, provenance, template immutability, whitespace, and omission behavior.

**Non-Goals:**

- No DOCX template replacement or snapshot/hash change.
- No changes to locked labels, sequence text, table geometry, merges, columns, boldness, fonts, paragraph properties, headers, footers, or page layout.
- No automatic invention of missing P-statements, GHS categories, signal words, or group headings absent from source evidence.
- No general-purpose translation engine or external dependency.

## Decisions

1. **Use an ordered group/token model at the extraction boundary.** A list of group records containing a controlled group key, source heading, source locator, and complete P-statement records preserves information that two independent arrays cannot represent. Keep `p_statements` as a compatibility projection, but do not use `other` as the group store.

2. **Tokenize heading boundaries before code boundaries.** The parser will operate on logical source lines and split both recognized heading boundaries and H/P code boundaries. This handles a heading after a prior P-statement and prevents a following heading from being appended to the previous statement. Recognition is scoped to the S2 precautionary region and uses the existing controlled heading vocabulary.

3. **Render one value string inside the existing value cell.** The grouped model will render headings and complete P-statements as semantic lines, then pass the result through the existing value-only writer. No row insertion is needed. This preserves the template's fixed `2.6` label and lets the current non-bold value exemplar provide typography.

4. **Treat source headings as content evidence, not template labels.** Source S2.4/S2.6 numbering selects the semantic destination only. The current template's fixed label remains authoritative; a source heading is written only into the non-bold value area and never participates in parent `2.x` renumbering.

5. **Make grouped presence auditable but conservative.** A group is retained only when it has at least one valid child P-statement. Orphan headings are omitted and recorded for review; a source-proven group with valid statements that is absent from approved facts or output traceability blocks release. This avoids both silent loss and unsupported heading invention.

6. **Translate only controlled group keys.** CN-to-EN output uses the approved four heading equivalents and retains the source P-code sequence. The transformation is represented in traceability; no free-form heading translation is inferred.

Alternatives considered:

- **Only patch PU-1002 facts:** rejected because the extractor/projection defect would recur for every product.
- **Append headings back from `s2.other`:** rejected because it loses group membership and can reintroduce unrelated Section 2 prose.
- **Add extra template rows:** rejected because it changes the locked template topology and is unnecessary; the existing value cell already supports semantic lines.
- **Reconstruct headings from P-code ranges:** rejected because the source may omit groups, use nonstandard combinations, or contain product-specific ordering; source evidence must control.

## Risks / Trade-offs

- [Risk] Legacy approved facts contain only flat `p_statements` and no group evidence. → Keep a compatibility fallback for flat, source-traceable P lists; require grouped parity only when source coverage proves explicit headings, and add a review/blocker for unrepresented source groups.
- [Risk] A source paragraph contains ordinary prose that resembles a group heading. → Scope heading detection to the S2 precautionary region, require the controlled heading form with a colon, and test non-S2 false positives.
- [Risk] Existing value writers could alter line-break typography when given multiple logical lines. → Reuse the existing value-cell-only writer, run whitespace and non-bold audits, and verify the fresh-template locked skeleton.
- [Risk] Source and template numbering differ. → Assert the projection target is the maintained `2.6` semantic slot and never copy the source numeric prefix into the locked label.

## Migration Plan

1. Preserve the affected pre-edit files in a task-scoped temporary backup and record the baseline in the change evidence.
2. Implement the grouped extractor/model/projection and audit checks behind the existing Section 2 semantic boundary.
3. Add and run focused regressions, then the complete project test suite and OpenSpec validation.
4. If verification fails, restore only the affected files from the backup; retain unrelated worktree changes and old package archives.
5. Do not package, commit, push, or remove prior packages until implementation verification and explicit user acceptance are complete.

## Open Questions

None. The report's cited PU-1002 source DOCX is not available in the current workspace, so the real-document replay remains an acceptance check when that source is supplied; the synthetic four-group fixtures are sufficient to implement the specified behavior.
