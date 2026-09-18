## Why

The efficiency report identifies two different costs that are currently mixed together: repeated Agent work to rebuild product facts/mappings, and machine time spent on source conversion, audits, DOCX generation and WPS PDF conversion. The current MSDS runtime already batches DOCX work and bounded PDF conversion, but the reusable evidence packet is not part of the formal build path and legacy-source caching is not consistently passed through the main pipeline. This change establishes a measurable V3.26 efficiency path without weakening source authority, locked-template authority or release gates.

The current worktree is not a clean release baseline. Before implementation, the recoverable baseline is the recorded `3e5eef903da06b249bce3b4fbd43f49b3e97b087` revision plus the pre-existing working-tree state preserved at `C:/Users/52882/AppData/Local/Temp/msds-efficiency-baseline-20260917-3.zip`. Rollback means restoring that snapshot and discarding only the files owned by this change; no historical package or pre-existing user change is to be removed.

## What Changes

- Add a source/evidence preparation path that can be reused by the Agent while keeping packets review-required and unusable as approved facts until mapping, disposition and traceability are complete.
- Integrate a source-hash-bound cache directory into the formal build path for legacy source conversion and evidence preparation, including adapter/spec/version invalidation.
- Add a reviewed, declarative product-family candidate configuration boundary so repeated mapping and rule logic can be reused without automatically filling a fact that is absent from the current source.
- Add shared read-only document/audit indexing so independent release gates can reuse parsed structure while retaining separate blocker semantics and final-file verification.
- Expand telemetry to distinguish evidence preparation, semantic review/build, DOCX, audit and PDF wall-clock measurements, and provide a repeatable benchmark harness for comparable runs.
- Keep the existing bounded WPS conversion strategy as the default; evaluate worker counts empirically and make any alternative converter lifecycle opt-in only after stability and lineage checks.
- Preserve the four-stage order: full source extraction, constrained normalization, fixed-structure template overwrite, and post-overwrite fine-tuning.
- **BREAKING**: the optimized path MUST NOT treat a cached packet, family candidate, or fast checkpoint as approval, source evidence, or a replacement for any release gate.

## Capabilities

### New Capabilities

- `msds-throughput-efficiency`: Source/evidence reuse, reviewed product-family candidates, shared audit context, performance telemetry and measured PDF scheduling for the MSDS overwrite pipeline.

### Modified Capabilities

<!-- No existing deliverable-audit requirement is changed by this proposal. The new capability preserves the existing audit contract while changing only how repeated work is scheduled and measured. -->

## Impact

- Affected implementation: `MSDS Skill/scripts/build_eight.py`, `msds_pipeline.py`, `source_ingest.py`, `evidence_packet.py`, audit modules and new benchmark/config support.
- Affected documentation and machine-readable contracts: the MSDS performance runbook, efficiency contract and agent execution guidance.
- Affected tests: cache-key invalidation, packet reuse without approval, family-candidate provenance, audit-context equivalence, timing schema and WPS worker scheduling.
- No new office engine is required. WPS remains the formal DOCX-to-PDF converter; LibreOffice remains limited to approved legacy-source conversion.
- Formal output remains four audited DOCX plus four corresponding PDF files for the MSDS matrix. Template tables, labels, sequence, bold label runs, geometry, headers, footers and all semantic/source/render blockers remain unchanged.
