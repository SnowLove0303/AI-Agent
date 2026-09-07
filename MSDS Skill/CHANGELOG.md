# MSDS Unified Eight-Deliverable Standardizer Skill — Changelog

## v3.15 — 2026-09-07
- Published the template-slot contract and four-state source-presence policy from the PU-1001 replay: ordinary blank template slots are non-writable, Section 8.2 remains a controlled table exception, Section 9 suppresses pure missing rows and renumbers survivors, and Sections 11/12 reduce to source explanation rows when no valid endpoint exists.
- Added source-fidelity regression coverage, independent package evidence, CN/EN and company-overlay parity checks, and DOCX-first eight-file release verification. PU-1001 replay completed with `RELEASE_PASS` and `100/100` package audit.
- Preserved the active formal CN/EN template baselines and fixed template-owned version text `Version：V1.0`; no source or template files are modified by the overwrite path.

## v3.14.2 — 2026-09-04
- Added the mechanical/agent-split parameterized workflow: `scripts/extract_source_facts.py` (positioned draft with provenance, coverage fingerprint, EN skeleton; S2/S11/translation stay needs-review), `scripts/msds_pipeline.py` (canonical DOCX-first flow with in-process gates including S9-leftover and S11-toxicology checks) and `scripts/build_eight.py` (one command: 4 DOCX + gates + 4 PDF + matrix report).
- Hardened the CN compact pass to skip the locked S8.2 parent/header rows and fixed a variant-name key bug found by the pipeline smoke test. Legacy `_task_work` generators are frozen and keep proving prior behavior.
- Documented the mechanical-vs-judgment split and the batch-matching ban in the new SKILL §20; every agent call is recorded as a traceable `AGENT_DECISION`.

## v3.14.1 — 2026-09-04
- Fixed the GHS label-elements value to stay empty when the source states no label ingredients, so the existing missing-row suppression removes the whole row instead of leaving a bare `必须列在标签上的有害成分：` heading in customer-facing output. Behavior with verified ingredients is unchanged.

## v3.14.0 — 2026-09-04
- Adopted the user-supplied formal templates byte-for-byte as the authoritative CN/EN baselines (CN SHA-256 `2e4f55086bb13de9caa9e933465fad55eb62efc785d595170bc65749a2de6cfc`; EN `59445b62c6d33b25a2e04c05778d428656f1ce0cbe7c21212721b145468c4416` for both source record and active baseline).
- Replaced the v3.13 nested 8.2 child-table design with the formal top-level four-column control-parameter rows: one-cell `工作场所组分控制参数 / Control parameters for workplace components` parent, locked header (`物质 / 依据 / 类型 / 数值`; EN `Substance / Basis / Type / Value`), then data rows (Section 8 grows 12 to 16 rows; all other tables unchanged).
- Reworked the whitelist writer for top-level S8.2 data rows: only source-grounded records may be written or cloned; the two template example OEL rows are illustrative and must be cleared — replaced by source records when present, otherwise reduced to a single data row carrying the exact missing-data placeholder (`无数据` / `No data available`) in the value column.
- Retired the nested child-table installer; archived both v3.13 language baselines separately and regenerated active/versioned snapshots and regression coverage. Template example facts remain non-authoritative.
- Preserved all v2.9/v3.11/v3.12/v3.13 overwrite rules, unified semantic model, four-language/company matrix, source-only facts, DOCX-first WPS/Word-compatible PDF conversion, release blockers and page-by-page QA.

## v3.13.0 — 2026-09-03
- Added the controlled Section 8.2 engineering-controls child table to both maintained language templates without changing the 16 top-level table count, parent rows, sequence/label cells, merges or headers/footers.
- Pinned the CN child-table headers as `物质 / 依据 / 类型 / 数值` and the EN headers as `Substance / Basis / Type / Value`, using the established four-column grid `[2400, 1100, 1100, 1600]` twips so the child table fits inside the parent value cell.
- Added a whitelist writer that can populate only source-grounded S8.2 data rows and clone the approved styled data row for additional verified records; child headers and topology are release-locked.
- Extended the recursive template snapshot and geometry audit to cover nested child-table geometry, cell properties, paragraph/run properties and header/footer parts.
- Preserved the latest EN attachment byte-for-byte as the source record (`2f287b544705d0db7ff724610c6f7878a88ff2912bbf074151e107f36a588a0e`), generated the active child-table baseline with a non-splittable 8.2 parent row (`4ba9475bb211bfa7dae6328243cddb1797ff36afb17875b66d53d782b15216ff`), and removed one known accidental Chinese suffix from the EN Hand protection label while retaining its formatting.
- Corrected the child-table grid to `[2400, 1100, 1100, 1600]` twips so the fourth `Value/数值` column remains visible inside the parent value cell; regenerated geometry snapshots and the eight-file replay evidence.
- Archived both v3.12 language baselines separately and regenerated active/versioned snapshots and regression coverage. Template example facts remain non-authoritative.

## v3.12.0 — 2026-09-03
- Adopted the latest user-supplied EN template as the authoritative source and active baseline with SHA-256 `2f287b544705d0db7ff724610c6f7878a88ff2912bbf074151e107f36a588a0e`.
- Preserved the prior v3.11 EN baseline at `examples/archive/template_reference_en_v3.11_pre_field_update.docx`.
- Locked the six revised Section 11 EN sublabels to the supplied template wording: `Oral:`, `Inhalation:`, `Dermal:`, `Fertility:`, `Teratogenicity:` and `In vitro genotoxicity:`.
- Updated the EN template source/active hash, structural snapshot, layout normalizer, generator payloads and regression tests without changing CN geometry or the shared source-grounded overwrite rules.

## v3.11.0 — 2026-09-03
- Corrected the EN template authority: `examples/template_reference_en.docx` now uses the user-supplied `模板_MSDS_EN_冠志 - 副本.docx` byte-for-byte with SHA-256 `415bcaf73256c17b3707c4d660dc6f5c4b7f69e2ab5d728ec8f3108dde16b569`.
- Preserved the previous normalized EN baseline as `examples/archive/template_reference_en_v3.10_normalized.docx`; it is rollback/audit evidence only and is not used for generation.
- Removed the false CN/EN physical-capacity assumption. EN Section 1 remains the supplied 9-row structure, while CN remains the independent 10-row structure; the shared semantic model projects only fields supported by each template.
- Updated EN geometry snapshots, hash/lineage checks, capacity validation, generator mapping and template-format parity coverage. Section 8 hand protection/8.2 and Section 11 through 11.10 remain template-owned.
- Preserved all v2.9/v3.2/v3.3/v3.8/v3.9/v3.10 overwrite rules, unified semantic model, four-language/company matrix, source-only facts, DOCX-first WPS/Word-compatible PDF conversion, release blockers and page-by-page QA.

## v3.10.0 — 2026-09-03
- Fixed the single DOCX-to-PDF publication adapter to use the native WPS/Word-compatible `word2pdf` exporter. LibreOffice is no longer a silent alternate renderer because it produced material pagination and table-layout drift from the approved Word/WPS baseline.
- Added a unified customer-deliverable evaluation standard with a fixed 100-point model and separate release outcome.
- Added B0/B1/B2 blocker precedence so score cannot override template, source-fidelity, PDF-lineage or package failures.
- Added a complete stable-ID audit checklist, evidence schema and human-readable/JSON report contract.
- Added deterministic eight-file discovery and DOCX/PDF pairing primitives plus an orchestrator that fails closed on missing evidence.
- Preserved the V2.9 inheritance contract, V3.8/V3.9 template, whitelist, semantic model, four-format matrix and DOCX-first PDF behavior.

## v3.9.0 — 2026-09-03
- Added the executable template mutation whitelist based on the Feishu “17节Section 标准骨架结构” contract.
- Locked sequence/label cell formatting and wording by default; ordinary writes now target only existing value cells, with explicit S3/S8.2/note-slot exceptions.
- Added a release-blocking locked-skeleton XML audit covering paragraph/run properties, cell properties and label-body preservation after approved S2/S9 omission.
- Changed the Section 11 alias policy so source `主要粘膜刺激性` is classified into the existing `11.3 主要眼睛刺激性` endpoint while preserving the source value and avoiding duplicate `11.10` content.
- Removed legacy customer-facing Section 2 cross-reference payloads from the generator facts and kept label elements explicit and line-separated.
- Preserved the complete v2.9/v3.2/v3.3/v3.8 inheritance, four-language/company matrix, DOCX-first PDF derivation and all prior release gates.
- Published as an independent V3.9 directory; V3.8 and all earlier versions remain intact.

## v3.8.0 — 2026-09-02
- Added source-grounded Section 2 GHS pictogram extraction and in-place insertion, preserving the maintained template table geometry and the source image as the visual authority.
- Replaced customer-facing Section 2 cross-references such as `见2.4-2.6` / `See 2.4-2.6` with explicit, line-separated label-element tips; pure missing-data rows are suppressed and surviving Section 2 items are renumbered continuously.
- Corrected the OS-9015 Section 11 projection to use the toxicology facts actually present in the source and blocked unrequested method, species, classification, similar-product, overall-assessment and additional-information inference.
- Changed production EN formatting to synchronize paragraph and run properties from the maintained EN template before row suppression; global font/size normalization is no longer used in the production path.
- Added Section 2 release auditing and regression coverage for pictogram presence, explicit label tips, missing-row suppression, source-only Section 11 mapping and EN template-format parity.
- Released as an independent V3.8 directory; V3.7 and all earlier versions remain intact.

## v3.7.0 — 2026-09-02
- Added the supplied EN template as a separate, language-specific template lineage while preserving the exact source copy for auditability.
- Normalized the EN template's missing Section 1.1 row so CN and EN expose the same section positions and semantic fields; no product facts were promoted from template examples.
- Changed the generator to clone CN outputs from the CN reference and EN outputs from the maintained EN reference. Added fail-fast template capacity validation and per-output template hash evidence.
- Added EN template source/baseline snapshots, CN/EN geometry and template-lineage regression coverage, and retained the existing v2.9/v3.2/v3.3/v3.6.2 inheritance, semantic, PDF, and page-QA requirements.
- Generated the eight PU-2345 deliverables by final-DOCX-first conversion for the EN format repair; historical local versions and GitHub `MSDS Skill 1.0` remain unchanged.

## v3.6.2 — 2026-09-02
- Replaced the bundled authoritative template with the newer user-supplied `模板_MSDS_CN_冠志.docx` and pinned SHA-256 `cbbf558fb6511edecd8b6a44d3e6bde23ce8a01d715e370d5a19ddc1978a1c9c`.
- Regenerated the complete template geometry/header/footer snapshot and updated the geometry release baseline.
- Absorbed the confirmed table-only adjustment: Section 8 PPE/hand-protection internal boundary lines and surrounding first exposure-control boundaries, plus Section 11 introductory/reference-data boundary lines. Table count, row count, grid widths, merges, paragraph properties and character properties remain unchanged.
- Preserved the full v2.9 inheritance core, v3.2/v3.3 four-format/eight-file architecture, unified semantic model, professional English, structured Section 11 through 11.10, continuous Section 9 omission/renumbering, DOCX-first PDF derivation, release blockers and page-by-page QA.
- Template example facts remain non-authoritative; PEA-4139, sample ingredients, hazards, toxicology and ecology values are never copied into product facts.

## v3.6.1 — 2026-09-02
- Added the Section 9 property omission rule requested from the customer review: pure `无数据。` / `No data available` property rows are removed as whole rows before write, while `不适用` / `Not applicable`, measured values and substantive `其他信息` / `Other information` remain.
- Renumbered the surviving Section 9 properties continuously in semantic order and added a PU-2345 CN/EN regression test for the resulting `9.1`–`9.13` visible sequence.
- Updated the locked-label audit to tolerate approved whole-row deletion by checking surviving bold anchors as an ordered subsequence within each table, preserving paragraph formatting and geometry invariants.
- Released as an independent patch directory and ZIP so v3.6 and all earlier versions remain recoverable.

## v3.6.0 — 2026-09-02
- Added the CN PDF layout compatibility regression from the customer-supplied WPS reference PDF.
- Added `scripts/compact_cn_layout.py`, a CN-only post-write layout pass that preserves table geometry and facts while normalizing table-body text to 10 pt, single spacing and zero paragraph before/after spacing.
- Fixed the inherited oversized footer first-line indent so `修订日期：2024/8/15` remains on one line, and kept Section 16's final information block together to prevent an orphaned final line.
- Preserved locked template label paragraph properties, English baseline behavior, the unified semantic model and all v2.9/v3.5 requirements.
- Added a regression document and tests; the same PU-2345 input must be replayed through the complete DOCX-first pipeline before release.
- Generalized footer character-indent removal to CN and EN after visual QA
  found the same inherited split in `Revision date`.

## v3.5.0 — 2026-09-01
- Added the bundled `scripts/convert_docx_to_pdf.py` publication adapter, based on the verified LibreOffice headless conversion pattern documented by GitHub `dconv`.
- Enforced DOCX-first publication: only the exact final audited DOCX may be converted to its same-basename PDF; independent PDF authoring/editing is prohibited.
- Added isolated LibreOffice profiles, same-volume temporary output, atomic replacement, timeout/error handling, UTF-8-safe diagnostics, and conversion evidence with source/target hashes, converter version, page count and timing.
- Added PDF converter adoption documentation and regression tests; added a maintenance rule to turn user feedback into cross-language/cross-company regression cases.
- Fixed the v3.4 inherited `SKILL.md` frontmatter so the unified skill passes strict automatic loading validation.

## v3.4.3 — 2026-09-01
- Registered `audit_locked_labels.py` and `audit_whitespace.py` as approved v3.4 audit enhancements so the v2.9 inheritance gate distinguishes preserved v2.9 core files from new release controls.
- No v2.9 overwrite content, program, or requirement was removed or weakened; only the inheritance audit's approved-change list was corrected.

## v3.4.1 — customer-facing content and layout correction
- Section 3 now writes one component per physical row; the PU-2345 four-component case extends the cloned template row in place while retaining the authoritative row formatting.
- Customer-facing missing values are normalized to `无数据` / `No data available`; internal phrases such as `源文件未提供`, `源文件记载`, `按源文件列示` and their English equivalents are prohibited in deliverables.
- Section 11 acute dermal, acute inhalation, skin/eye irritation, sensitization and mutagenicity content now uses direct source-grounded structured field lines, including species, result, classification, method and supported similar-product-study qualifiers.
- Section 14 transport values now use one logical field per line instead of semicolon-packed strings.
- Removed the obsolete S3 capacity blocker from the PU-2345 release matrix and regenerated all four DOCX masters and four PDF derivatives from the corrected DOCX masters.

- Replaced the sole authoritative template reference with the user-uploaded `模板_MSDS_CN_冠志.docx`.
- Pinned template SHA-256 to `3226489c0e82576152e3adb17ca810821bee9ac67b876199710592b6c06ed9b4`.
- Regenerated the template snapshot with table/cell merge geometry, grid and cell widths, paragraph/run properties, and header/footer parts.
- Locked the revised Section 2, Section 8 hand-protection/8.2 engineering-control structure, and Section 11 through 11.10.
- Added a structural snapshot generator and regression checks; template example facts remain non-authoritative.
- Fixed v2.9 ZIP inheritance audit fallback for legacy mis-encoded member names while retaining exact content-hash comparison.

# v3.3
- Adds four PDF publication derivatives for a default total of eight deliverables.
- Preserves the full v2.9 DOCX overwrite core and v3.2 four-format semantic/template requirements.
- PDFs must be converted one-to-one from final audited DOCX masters; independent PDF authoring/editing is prohibited.
- Adds PDF preflight/full-page render QA and an eight-file release matrix audit.

# v3.2
- Added hard v2.9 full-inheritance contract and byte-level parity audit.
- Bundled rollback copies of intentionally enhanced v2.9 core documentation/sentence policy.
- v2.9 parity is now a release blocker before four-format delivery.

# Changelog

## 3.0.0 — unified four-format architecture
- Merged the Chinese Word Standardizer v2.9 and English Professional Standardizer v1.0 into one maintained skill.
- Default output is now four synchronized DOCX variants: CN/EN × Guanzhi/Guocai.
- Established one normalized semantic model as the only source for all four outputs.
- Added professional English translation resources to the unified package.
- Added `output_matrix.py` and four-variant synchronization policy.
- Added shared Section 11 structured toxicology policy; punctuation-first splitting is explicitly forbidden in Section 11.
- Fixed ordinary sentence-boundary policy so Section 11 is excluded from automatic punctuation splitting.
- Added cross-language factual parity and cross-company whitelist-only QA requirements.
- Retained the latest user-approved `(3)` template baseline and all v2.9 omission, numbering, identity, layout and dual-company rules.
- Separate CN and EN skill branches are superseded by this package.

## 3.1.0
- Made authoritative-template in-place overwrite the highest-priority contract.
- Prohibited blank/rebuilt EN documents and EN-specific geometry redesign.
- Added mandatory four-format geometry/company-parity release gate.
- Made item-presence decisions shared across all four variants.
- Clarified Section 11 structured mapping as prior to all punctuation line-breaking.
- Non-zero applicable audit is now an explicit no-delivery condition.
## v3.4.2 - PU-2345 content and release-audit correction

- Aligned the Chinese Section 1 heading with the new template's fixed label (`1.物料及供应商标识`).
- Updated the eight-file audit to accept both legacy Chinese company-name aliases and the generated English company-name filenames, including variant subdirectories.
- Corrected locked-label auditing to validate physical paragraph anchors and paragraph formatting, allowing translated or merged Word runs.
- Corrected whitespace auditing so controlled line breaks in structured Section 11/14 fields are measured and reported without being misclassified as failures.
- Re-rendered all four final DOCX files to their corresponding PDFs and re-ran the release gates.
