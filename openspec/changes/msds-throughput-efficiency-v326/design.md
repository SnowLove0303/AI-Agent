## Context

The current MSDS implementation already loads the maintained CN/EN templates once per matrix, builds four DOCX masters before PDF conversion, and uses bounded WPS conversion workers. It also has a separate source-evidence packet and source-hash cache implementation. The remaining efficiency gap is that the packet and legacy conversion cache are not consistently part of the formal build invocation, while most product-specific semantic work still happens outside a reusable declarative boundary.

The design must preserve the existing four-stage business order and the mutation boundary: source extraction and semantic normalization happen before any DOCX mutation; the template owns tables, labels, sequence, bold label runs, geometry, headers and footers; only value-cell writes, presence decisions and explicitly authorized styled-row operations are allowed. The saved, audited DOCX remains the only PDF input.

The implementation baseline is the existing dirty worktree at revision `3e5eef903da06b249bce3b4fbd43f49b3e97b087`, preserved in `C:/Users/52882/AppData/Local/Temp/msds-efficiency-baseline-20260917-3.zip`. The baseline contains pre-existing user changes and historical artifacts; rollback must restore that snapshot or revert only change-owned files and must not reset or clean the worktree globally.

## Goals / Non-Goals

**Goals:**

- Make source-evidence preparation and source-adapter reuse observable and safely reusable from the formal MSDS workflow.
- Remove repeated product-family rule/mapping code by introducing reviewed candidate profiles, without allowing unsupported facts to enter an approved facts model or output.
- Reuse a read-only parsed/indexed DOCX representation across independent audits while keeping every existing gate and its blocker semantics.
- Produce comparable stage, cache and PDF scheduling telemetry that separates machine work from Agent/manual review time where that information is available.
- Verify PDF worker-count choices empirically and retain a conservative default with a clean failure and lineage trail.
- Keep the change additive and reversible so existing approved facts and the current four-DOCX/four-PDF release contract remain usable during migration.

**Non-Goals:**

- No ProcessPool or COM/WPS daemon becomes the default converter lifecycle without a measured stability result and an explicit follow-up decision.
- No knowledge-base, product memory or family profile may auto-fill a source fact, translate an unreviewed value or override an ambiguity/conflict.
- No reduction, reordering or weakening of source, semantic, locked-template, whitespace, geometry, lineage, render or package gates.
- No table reconstruction, global soft-hide, label/sequence rewrite, boldness change, or alternate PDF authoring engine.
- No fixed 20-second SLA or report percentage is accepted as an engineering guarantee before comparable benchmarks exist.

## Decisions

### 1. Make caching an explicit build input, not an implicit global cache

Add one cache-root boundary to the formal CLI and pipeline. The default location is derived from the requested output workspace when available, while callers may provide an explicit directory for Harness reuse. The cache key continues to include source bytes, source format, adapter version, extractor/schema version and active source-interpretation inputs.

The evidence packet remains a review artifact. The build may accept packet metadata as provenance, but it must still load an independently approved facts model and re-run facts/source-grounding validation. A packet cache hit only skips mechanical extraction or conversion; it cannot set `build_allowed` or bypass review.

Alternative considered: automatically discover a packet beside the facts file. Rejected because implicit discovery can select a stale packet in a shared Harness workspace and makes provenance harder to diagnose. An explicit or deterministically derived cache root is easier to report and roll back.

### 2. Use source-bound family profiles as candidate mapping data

Introduce a dependency-free declarative profile format under the skill's configuration area. A profile can declare family identity, reusable section/rule hints and candidate values, but each candidate carries a source-evidence requirement and disposition. The normalization stage may use the profile to propose or validate a mapping; only the approved facts file is consumed by the overwrite stage.

Profile values are never copied directly into a value cell. A profile candidate is accepted only when it is confirmed by the current source, an approved translation trace, or an explicitly permitted controlled overlay. Conflicts remain blockers. The profile loader must reject malformed, cross-model or unreviewed approval metadata before it reaches the write plan.

Alternative considered: a Python factory that returns complete facts for a product family. Rejected because it recreates the manual-script coupling and makes source absence indistinguishable from inherited knowledge. Alternative considered: a general knowledge-base autofill. Rejected by the source-authority contract.

### 3. Share immutable audit indexes, not one opaque fusion gate

After a staged DOCX is loaded, construct a read-only audit context containing the table/row/cell topology, deduplicated cells, paragraphs, labels, writable value boundaries, visible numbering, run typography and relevant XML signatures. Existing audits consume this context through optional parameters and continue to emit their own evidence and blockers. Checks that intentionally inspect the persisted ZIP package, such as broad terminology or final lineage checks, remain saved-file checks.

The final saved DOCX is re-opened or package-scanned where the audit contract requires persisted-artifact evidence. The shared context is an optimization for duplicate parsing/traversal, not a replacement for final-file validation.

Alternative considered: one `UnifiedFusionAudit` that returns a single pass/fail. Rejected because it would obscure gate ownership, make diagnostic attribution less precise and create pressure to drop checks for speed.

### 4. Keep bounded threaded WPS conversion and add measurement before changing lifecycle

Retain the existing external WPS command per PDF and bounded `pdf_workers` scheduling. Add worker-count and converter-health telemetry to the matrix report and a benchmark command/test fixture that can compare workers 1, 2 and a configured higher value without publishing output. Conversion remains one-to-one with the saved audited DOCX and retains source/output hashes.

Alternative considered: Python `ProcessPoolExecutor`. Rejected as a default because the actual expensive operation is still an external WPS process; a process pool would add Windows process overhead without removing WPS cold starts. Alternative considered: resident COM/WPS service. Deferred because of office-session ownership, file-lock, crash-recovery and version-compatibility risks.

### 5. Make telemetry additive and gate-independent

Extend the existing low-overhead stage timer with cache decisions, packet preparation timing, per-variant wall time, PDF batch wall time, worker count, retry/failure state and an optional manual-review duration supplied by the caller. Reports must identify whether a duration is measured machine time or an externally supplied review time. Progress events remain checkpoints only and cannot influence gate execution.

The benchmark compares identical source bytes, facts, templates, WPS version and machine conditions. It reports median and maximum values over repeated runs and separates cold-cache from warm-cache results. This avoids converting the attachment's rough percentages into a false SLA.

### 6. Preserve migration compatibility and isolate change-owned files

Existing commands retain their current semantics. New cache/profile/benchmark inputs are additive, and absence of a profile means the current source-grounded facts path is used. The implementation updates documentation and tests together with the code. Before any distributable is rebuilt, the previous package remains available; commit, push and removal of old packages remain acceptance-gated.

## Risks / Trade-offs

- [Stale evidence cache] → Bind every cache artifact to source bytes, format, adapter/extractor/schema versions and source-interpretation inputs; record hit/miss reasons and keep packets review-required.
- [Family profile becomes an implicit knowledge base] → Store candidates separately from approved facts, require current-source evidence and fail on unresolved or conflicting candidates.
- [Shared audit context misses a persisted XML detail] → Keep package-level/final-file checks, compare in-memory and saved identities where required, and preserve the old independent audit entry points for regression tests.
- [Higher WPS parallelism causes file locks or unstable output] → Make the worker bound explicit, benchmark before changing the default, support conservative serial mode and fail closed on lineage or conversion errors.
- [Telemetry adds noise or slows the hot path] → Use monotonic timers and bounded JSON events only; do not serialize full DOCX objects or source text into progress events.
- [Dirty worktree causes unrelated files to be overwritten] → Limit edits to change-owned paths, inspect diffs before every implementation batch, and use the preserved baseline archive for rollback rather than `git reset` or broad cleanup.
- [Legacy source grounding remains tied to the original non-DOCX path] → Pass the prepared source representation to grounding while retaining original path/hash metadata, and add regression coverage for cache hit/miss and source-anchor behavior.

## Migration Plan

1. Add the OpenSpec contracts, cache/profile/telemetry schemas and regression fixtures without changing the current output path.
2. Add explicit cache-root plumbing to evidence preparation and formal build; verify direct DOCX behavior is unchanged and legacy source conversion reuses only matching entries.
3. Add optional reviewed family profiles and require provenance checks before they can influence approved facts.
4. Add the shared audit context behind the existing audit interfaces and prove output/gate equivalence against the pre-change path.
5. Add benchmark execution and collect cold/warm cache and WPS worker-count baselines. Keep the default worker count conservative until the measurements pass stability criteria.
6. Run the full test suite, OpenSpec validation, DOCX/PDF audit and render checks. Repackage only after the user accepts the verified result; retain the baseline package/snapshot until then.

Rollback is to restore `msds-efficiency-baseline-20260917-3.zip` and the recorded HEAD/status, or to revert only the files introduced/modified by this change while preserving the pre-existing working tree. No broad reset, clean or deletion of historical packages is permitted.

