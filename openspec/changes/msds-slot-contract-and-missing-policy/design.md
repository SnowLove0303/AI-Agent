## Context

See `proposal.md` for the motivation. The current MSDS pipeline already clones language-specific templates and has mutation/audit helpers, but ordinary rows are still projected from positional arrays and the Section 11/12 policy is broader than the newly confirmed user contract. The implementation must remain inside the existing MSDS Skill and preserve the active template snapshots; the user source `.doc`, formal templates, TDS Skill, and PDF converter are outside the change.

## Goals / Non-Goals

**Goals:**

- Make writable template cells explicit and reject writes to locked labels or intentionally blank ordinary slots.
- Preserve source text and provenance for mapped facts, while making unsupported or ambiguous mappings reviewable.
- Implement the four source-field states and the Section 9/11/12 rules from the new contract.
- Keep Section 8.2 as a narrow table exception and prevent template example leakage or generated engineering-control prose.
- Add PU-1001 regression coverage and reuse one approved semantic model for all four variants.

**Non-Goals:**

- Do not modify the authoritative formal templates or user source documents.
- Do not redesign the 16-section document, add new template rows, merge TDS and MSDS, or create per-product generator copies.
- Do not introduce parallel PDF authoring, a new external dependency, or unmeasured Office-process concurrency.
- Do not solve unrelated historical product mappings in this change; they remain regression inputs unless the shared contract exposes a failure.

## Decisions

### 1. Register template slots instead of relying on row positions

The existing semantic payload remains the input boundary, but the write boundary becomes a template-derived registry keyed by section, physical row/cell identity, and semantic field. Each slot records whether it is locked, writable, intentionally blank, a whole-note slot, or an 8.2 data row. This fixes the root cause once for all callers instead of adding product-specific exceptions. A positional fallback is not allowed because it cannot distinguish a blank slot from a writable value cell.

### 2. Use explicit source states and section policies

The normalized model will carry `SUPPORTED`, `EXPLICIT_MISSING`, `NOT_APPLICABLE`, or `ABSENT` for each source field. A small policy function will decide display/omit behavior by section. Section 9 removes pure-missing rows; Sections 11/12 collapse to their source note when no valid endpoint exists; other sections retain an explicit source missing value but suppress fields absent from the source. This keeps missing-data semantics out of generic cell-writing code.

### 3. Treat source text as immutable evidence by default

Extraction will keep exact source text and location. Normalization may assign a target field or perform an approved language translation, but it may not shorten a customer fact or change a proper name/address. Any semantic judgment records its source basis and target slot. Unmapped or ambiguous facts become review blockers rather than guesses.

### 4. Keep Section 8.2 on its existing dedicated path

The existing special writer remains the only path allowed to mutate the 8.2 data area. It will validate the locked parent/header topology, remove illustrative rows, and accept only verified four-column records. Ordinary row projection will never write 8.2 prose or table cells.

### 5. Reuse the approved model across variants and optimize measured repetition

Extraction and semantic normalization run once per source/model fingerprint. The four output variants clone their own language template and apply only authorized value/company overlays. Audits remain fail-closed; performance work will first remove repeated parsing and then measure whether any safe parallelism is worthwhile. WPS conversion remains serial by default because reliability is more important than an unmeasured speedup.

## Risks / Trade-offs

- [Existing products depend on broader Section 11/12 rows] → Add PU-1001 and existing structured-toxicology tests before changing the shared policy; unsupported legacy behavior must fail visibly rather than be silently preserved.
- [Template has prefilled illustrative values and malformed-looking example labels] → Keep the template bytes immutable, classify cells in the registry, and audit every non-value mutation against the pinned snapshot.
- [Source has a field with no template slot] → Produce a review blocker with source location; never add rows or discard the fact silently.
- [Reducing repeated DOCX parsing could hide audit differences] → Keep one final persisted-file audit pass and compare its results with the existing 65-test baseline.

## Migration Plan

1. Add the OpenSpec contract and PU-1001 regression expectations.
2. Implement the registry and state-policy helpers behind the existing shared pipeline.
3. Update mutation and audit gates, then run the focused PU-1001 tests.
4. Re-run the full MSDS test suite and the four-variant build/QA path.
5. If a gate regresses, revert only the change files or disable the new path behind the existing pipeline boundary; do not restore template examples or modify the formal templates.
