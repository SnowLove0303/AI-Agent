# Design

## Context

The shared `_field_candidates` extractor serves both Word and PDF table records. It already stores original cell text separately from derived candidates, so the fix can remain in that shared function and the candidate schema.

## Goals / Non-Goals

**Goals:**
- Avoid creating confident field mappings from header pairs or mixed label/value cells.
- Preserve exact source cell text and expose any unmapped label-cell suffix for downstream review.
- Verify the behavior against all 16 PU-3011 body sections and the GUI metadata view.

**Non-Goals:**
- Modify the source MSDS, table geometry, formatting, or rendering behavior.
- Infer semantic mappings for every arbitrary text-only row; uncertain delimiter-free pairs remain visible in the normalized source table rather than being promoted as candidates.

## Decisions

- Keep the rules in the shared candidate extractor so Word and PDF callers receive the same conservative behavior.
- Continue accepting explicit colon-delimited labels. For delimiter-free adjacent cells, require bold label evidence and a numeric data signal in the value; this captures the source's ingredient-to-CAS mappings while rejecting the Section 3 header pair.
- Put any text after an explicit label delimiter in candidate evidence and a machine-readable warning. Do not alter the original cell or merge the suffix into the adjacent value.
- Exercise both whole-document extraction and GUI metadata presentation through the existing PU-3011 check script.

## Risks / Trade-offs

- [Some legitimate delimiter-free text-to-text pairs will not become candidates] → The complete source table and formatting remain available for Agent review; only unambiguous candidates are promoted.
- [A delimiter suffix may be source duplication or layout-hidden text] → Preserve the source and report exact suffix and coordinates without guessing whether it should be deleted.
