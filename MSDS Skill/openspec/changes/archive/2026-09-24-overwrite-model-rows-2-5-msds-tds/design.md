# Design

## Context

See `proposal.md`. The selected products are the workbook sequence numbers 2–5: AMP-95, BEK-100L, BEK-200 and BEK-200L. Each has one CN MSDS DOCX and one CN TDS DOC in its own preprocessing folder; no EN source was found in that input set. The two installed skills have separate templates, mappings, output contracts and audits. Existing central WORD/PDF folders already contain historical outputs and are not the destination for this batch.

## Goals / Non-Goals

**Goals:**
- Produce four company/language variants for each document type from the selected source, with same-basename PDFs derived only from audited DOCX.
- Keep original inputs unchanged and never mix TDS with MSDS semantic rules or templates.
- Keep every product artifact, conversion, mapping and audit inside that model's new `覆写输出` subtree.
- Update only the four status cells after all 16 deliverables for that model pass applicable gates.

**Non-Goals:**
- Do not rewrite existing historical outputs, other workbook rows, templates, or source files.
- Do not create or infer unsupported product facts; ambiguity, unreadable source content, unsupported formats, or failed audit blocks that model's completion mark.

## Decisions

1. **Use the exact workbook data rows, not substring matching.** Select sequence values 2–5, then locate each source folder whose directory name exactly equals the model. This prevents BEK-200 matching BEK-200L.
2. **Use independent skill pipelines.** MSDS uses its installed v3.27.14 template, source-grounded fact packet, reviewed facts, eight-file builder, audits and render checks. TDS uses its installed v1.3.24 templates, source extraction/normalized mapping, TDS builder, fidelity audit, WPS/Word-compatible PDF conversion and eight-format audit. No existing output is used as factual source.
3. **Keep outputs per model.** Create `覆写输出\MSDS` and `覆写输出\TDS` below each source model folder. This avoids existing central output collisions while keeping results beside the corresponding inputs.
4. **Adapt legacy TDS `.doc` in the output evidence area.** Convert each original `.doc` to a temporary `.docx` under that model's TDS audit/source-adapter folder; pass the converted copy as an extraction input and retain the original hash/path as source authority. Use the prescribed WPS/Word-compatible adapter only for final PDF publication.
5. **Mark completion last.** Verify source hashes unchanged and all 16 files exist, are non-empty and pass their type-specific audits before writing “已覆写” in the workbook's final column. Save to a temporary workbook copy and replace the workbook only after the edited copy reopens and the other cells remain unchanged.

## Risks / Trade-offs

- **Legacy `.doc` conversion changes extraction fidelity** → retain original source hash and full extraction evidence; fail closed on unreadable structure or missing content.
- **A product may lack enough evidence for English translation or a semantic mapping** → leave its status blank and report the exact unresolved evidence; do not borrow facts from historical outputs.
- **Office conversion/render differences can affect layout** → use only the skill's approved final converter, render every page, and block completion on clipping, overflow or template drift.
- **Output path interpretation** → use a fresh `覆写输出` child under each exact model folder; existing historical WORD/PDF trees remain untouched.


## Execution findings (2026-09-24)

- Task assessment recorded as P2/E4 because this batch spans 64 deliverables, multiple source formats, bilingual chemical-safety content, and locked-template audits. The installed Superflow CLI exposes workflow modes but no P/E grading command or scale definition; `ssf workflow recommend` recorded **Full** and the high-uncertainty risk reason. The CLI requires the user to choose Quick or Full before the guarded workflow can proceed.
- Confirmed both MSDS pinned templates and all four TDS active templates match their baseline SHA-256. All four TDS legacy sources were adapted to audit-only DOCX copies; all eight original source hashes still match.
- Complete TDS body paragraphs and all tables were reviewed. Four TDS eight-format matrices were generated (32 files total). BEK-200 passed release audit and its four PDF pages were rendered and visually checked. AMP-95 failed the one-page contract on both CN PDFs; BEK-100L failed on all four PDFs; BEK-200L failed on all four PDFs. Their release reports record `page_count_exceeded`.
- MSDS evidence packets exist for all four models but remain `needs-review`; no MSDS deliverables were generated. The workbook is unchanged and no status cells were written.
- This change remains active and unarchived. Completion, workbook status updates, and review receipt are pending the user's Superflow workflow choice and resolution of the page-count gates.

## Follow-up execution (2026-09-24)

- Generated all four MSDS eight-file matrices. Their matrix reports show four formal-ready DOCX/PDF variants per model. All PDF pages were rendered and reviewed; no clipping or unintended overflow was seen.
- Generated all four TDS eight-file matrices. BEK-200 passed. AMP-95, BEK-100L and BEK-200L remain blocked because one or more PDFs exceed the active one-page limit; see `verification-report.md` and each model's `覆写输出/TDS/audit/release_report.json`.
- Rechecked all eight source hashes against the source manifest; every hash matches. Each model now has exactly 16 non-empty output files in its `覆写输出` subtree.
- Wrote `已覆写` only to workbook cell L5 for BEK-200. Other target status cells remain blank. Reopening the workbook confirmed no other cell changed.
- The change remains active and unarchived because three TDS matrices still fail the page-count release gate.
