## Context

The v3.26.1 baseline already has a fixed-template overwrite pipeline, a mutation whitelist, source-grounded facts, an English layout normalizer, a terminology gate, and pinned CN/EN template hashes. The English template and the current product-identity policy are nevertheless internally consistent with the wrong behavior: the active EN template preserves known Chinese/incorrect literals, while the pipeline intentionally leaves the EN Section 1.1 value blank. The existing terminology audit checks only a small banned-phrase list and missing-data markers, so it cannot catch Chinese characters, full-width punctuation, or unit typography drift across headers, footers and body XML.

The implementation must honor the established boundary: agents may write only approved non-bold value cells, presence decisions and explicitly authorized styled data rows. A corrected active baseline is a maintainer-controlled template migration, not a runtime permission to rewrite labels or geometry.

## Goals / Non-Goals

**Goals:**

- Make the active English template customer-ready without changing its table count, row capacity, merge topology, widths or locked-format contract.
- Require reviewed, source-traceable English product identity and correct Section 2 route/label projection.
- Detect Chinese leakage, template contamination, full-width English punctuation and known unit/terminology defects in every customer-visible English document part.
- Preserve numeric/source meaning, empty-row suppression, line ordering, and four-variant DOCX/PDF lineage.
- Leave a tested rollback path to the v3.26.1 revision and package.

**Non-Goals:**

- No TDS production mapper or TDS output regeneration; the report's TDS findings are outside this repository.
- No new external translation service, network dependency, or automatic chemical-name invention.
- No runtime rewriting of locked labels, boldness, table geometry, or template-owned headers beyond the approved baseline migration.
- No new Section 1.4 row or other structural expansion solely to mirror a recommendation when the maintained template has no such slot; emergency contact data remains source-/facts-gated in the existing supplier contact boundary.

## Decisions

### 1. Migrate the active EN baseline while preserving the supplied source record

Use the existing `template_reference_en_source.docx` as the immutable supplied-template record and produce a corrected `template_reference_en.docx` as the active baseline. Correct only customer-visible literal English/template artifacts identified by the report: header/title, Section 6.1/standard section labels, Section 8 hand-protection label, punctuation and spacing. Do not add rows or alter merges, widths, boldness, or table geometry. Regenerate the active snapshot and update the pinned active hash while retaining the source hash.

Alternative considered: sanitize every output after cloning while leaving the active baseline unchanged. Rejected because it hides baseline defects, makes fresh-template comparison misleading, and allows the same contamination to reappear in future agents or packages.

### 2. Make English product identity an approved fact, not a fallback translation

Extend the reviewed English fact contract with a professional product-name value and provenance. The build validates it before cloning; the identity policy checks model convention, non-empty content and source traceability. Existing source-grounded Chinese identity remains the basis for review, but English prose is supplied by the reviewed mapping layer. Missing or conflicting identity blocks rather than falling back to the model or a template sample.

Alternative considered: derive a name from the model code or a hard-coded PU dictionary. Rejected because it can narrow or invent chemical meaning and violates source grounding.

### 3. Normalize semantic English values before the template write and preserve value boundaries

Keep labels and value cells separate. Add controlled mappings for Section 2 health-route prefixes and label-element prose, plus a narrow English typography normalizer for full-width colons, temperature, density, viscosity and inequality presentation. Apply it only to approved values/translation outputs and to the versioned baseline migration; never use it to overwrite arbitrary labels or to infer missing facts. Preserve codes, numbers, qualifiers and meaningful line breaks.

Alternative considered: run a document-wide text replacement after saving. Rejected because it can modify locked labels, headers, XML fragments, source evidence text or unrelated words without semantic context.

### 4. Clone value typography from maintained run prototypes

The English writer will obtain a non-bold Arial 12 pt value `rPr` from the maintained EN template and preserve destination paragraph properties. For Section 2 route values, it will retain or derive the template-owned bold prefix `rPr` and apply the body prototype only to the descriptive tail. New runs will insert `rPr` before `w:t` and will be checked against the template's XML-level format anchors. No generic `cell.text` assignment or default `add_run()` path is allowed for production English values.

Alternative considered: set `font.name`, `font.size` and `font.bold` after creating text with `python-docx`. Rejected because it can omit East Asia/complex-script font slots, lose paragraph/run inheritance and produce the exact 10.5 pt or mixed-font defect reported in the supplemental audit.

### 5. Expand the English gate to all customer-visible DOCX parts

The terminology audit will inspect body tables, headers, footers and other text-bearing XML parts that can be customer-visible. It will emit structured findings for Chinese characters, full-width colons, known contamination, non-canonical section terms, company suffix drift and unit/spacing violations. The existing release pipeline will retain blocker precedence and attach these findings to the normal evidence report.

Alternative considered: rely on human visual QA alone. Rejected because the report shows repeated cross-model defects and because hidden header/footer text is easy to miss.

### 6. Treat the English baseline as a versioned migration with explicit evidence

Before implementation, the change records baseline revision `e3ce23706f56d0e9c3791b3361cd005fa90576cf` and v3.26.1 package SHA256 `4CD4C28FC8C0486D198A3996288F87D2071F65F8FD8026C0AEC582FECB60CEDC`. During implementation, snapshots, hashes and tests become the rollback/restore checks. The old package remains available until the user accepts v3.26.2.

## Risks / Trade-offs

- [Risk] Correcting the active EN template changes its pinned hash and may invalidate stale downstream copies. → Mitigation: keep the source template and v3.26.1 package, publish the new active hash in the package, and fail closed on stale baselines.
- [Risk] Requiring an English product name can block legacy facts that were previously accepted with a blank value. → Mitigation: make the preflight error actionable, add reviewed fixtures, and never silently fill from a model or example.
- [Risk] Full-width punctuation or unit normalization could touch legitimate source prose. → Mitigation: apply only the approved English value/translation layer, preserve numeric tokens and qualifiers, and test both valid and invalid examples.
- [Risk] A newly written value can look semantically correct while using the wrong run properties. → Mitigation: clone XML-level value prototypes, test font/size/boldness explicitly, and block mismatched output before PDF conversion.
- [Risk] Scanning all XML parts may surface hidden legacy text not visible in the ordinary body API. → Mitigation: classify findings by customer-visible part, retain evidence paths, and block only actual English customer-visible residue or known contamination.
- [Risk] The report covers TDS outputs that this repository does not build. → Mitigation: explicitly mark TDS as out of scope and do not claim it was fixed in the MSDS 3.26.2 release.

## Migration Plan

1. Implement the approved baseline and pipeline changes on top of the recorded v3.26.1 revision while preserving unrelated worktree changes.
2. Run focused English/template tests, the complete MSDS suite, strict OpenSpec validation, and a package extraction test.
3. Build the v3.26.2 complete package only after all release blockers pass; retain v3.26.1 for rollback until acceptance.
4. Roll back by reverting the v3.26.2 commit and restoring the v3.26.1 package if the active baseline, output geometry or quality gates regress.

## Open Questions

None. The fixed-template boundary and the TDS repository scope are resolved by the existing project rules and the report's code-availability check.
