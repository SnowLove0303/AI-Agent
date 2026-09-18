## 1. Contract and baseline

- [x] 1.1 Add the V3.26 efficiency/cache/profile/telemetry contract schemas and record the existing revision plus recoverable snapshot path; verify `openspec validate "msds-throughput-efficiency-v326" --strict` accepts the planning artifacts.
- [x] 1.2 Add regression fixtures for a direct DOCX source, a legacy source, a matching evidence packet, a stale packet and an unapproved family candidate; verify fixtures contain no formal output or template mutation.

## 2. Evidence and source-cache integration

- [x] 2.1 Add an explicit cache-root option to the formal build entry point and thread it through matrix construction to source preparation; verify existing direct-DOCX builds retain their current output contract and the default cache path is deterministic.
- [x] 2.2 Make legacy source preparation reuse only valid source-hash/format/adapter-bound converted DOCX entries and make source grounding search the prepared representation while retaining original path/hash provenance; verify matching, changed-source and invalid-cache tests.
- [x] 2.3 Add explicit evidence-packet provenance validation to the reviewed-facts workflow without allowing a packet to approve facts or supply values; verify stale, unresolved and `build_allowed: false` packets block the build with actionable errors.
- [x] 2.4 Update the Harness runbook and CLI help with the resumable sequence `prepare packet → review mapping/traceability → preflight → build`, including cache-hit/miss reporting; verify commands and paths match the implemented interfaces.

## 3. Reviewed product-family candidates

- [x] 3.1 Implement a dependency-free declarative family-profile loader and validator for candidate mappings, model scope, source-evidence requirements and disposition metadata; verify malformed, cross-model and incomplete profiles fail before template cloning.
- [x] 3.2 Integrate family candidates into constrained normalization as suggestions/validators only, requiring current-source evidence, approved translation traceability or an allowed controlled overlay before a candidate can enter approved facts; verify no candidate is written directly to a DOCX value cell.
- [x] 3.3 Add tests for source-confirmed, source-absent and source-conflicting candidates, including the required omission/empty-row policy and S2/S8/S11 endpoint routing; verify absent and conflicting candidates remain non-publishable.

## 4. Shared audit context

- [x] 4.1 Build a read-only per-DOCX audit context containing deduplicated topology, labels, writable value boundaries, visible numbering, typography and required XML signatures; verify context construction does not mutate the document or template.
- [x] 4.2 Route compatible semantic, locked-skeleton, value-typography, whitespace, numbering and layout gates through the shared context while retaining persisted ZIP/package checks and independent blocker ownership; verify all existing gates still execute and report their original categories.
- [x] 4.3 Add equivalence tests comparing the shared-context path with the current independent path on passing output and representative locked-label, boldness, geometry, blank-line, empty-row and discontinuous-numbering failures; verify no blocker becomes a warning or disappears.

## 5. Measurement and bounded PDF scheduling

- [x] 5.1 Extend matrix telemetry with evidence/cache decisions, machine-vs-supplied review duration labels, per-variant wall times, PDF batch wall time, worker count, retry/failure state and final DOCX/PDF hashes; verify the JSON schema is additive and telemetry failures cannot change release outcomes.
- [x] 5.2 Add a non-publishing benchmark command or test harness for cold/warm evidence/cache runs and PDF worker counts 1, 2 and configured higher values; verify it reports median/max timings and WPS instability without changing the formal output directory.
- [x] 5.3 Keep bounded threaded WPS conversion as the default, expose conservative serial fallback and reject any PDF whose source hash is not the saved audited DOCX; verify lineage, timeout, file-lock and worker-bound tests.
- [x] 5.4 Update the performance contract and runbook to distinguish current implemented scheduling from measured results, explicitly deferring ProcessPool/COM daemon adoption until stability evidence exists; verify no unsupported fixed-duration SLA is documented.

## 6. Full verification and release readiness

- [x] 6.1 Run the targeted efficiency/cache/family/audit tests, the complete MSDS test suite and strict OpenSpec validation; verify all failures remain release-blocking and the pre-existing change artifacts are not modified by this change.
- [ ] 6.2 Run a real comparable matrix benchmark with the preserved baseline and the optimized path, including DOCX-only and PDF-enabled modes, then record the result and environment; verify the report separates Agent/manual time from machine time and contains no unsupported speedup claim.
- [x] 6.3 Update the public version/changelog and manifest only after implementation and verification pass, keep formal output at four DOCX plus four PDF, build the requested local ZIP, and retain the old packages/snapshot until explicit user acceptance; commit, push and old-package removal remain acceptance-gated.

### Verification note

Task 6.2 remains intentionally open: this workspace contains no reviewed
approved facts model and no confirmed WPS conversion target, so only the
non-publishing evidence-packet cold/warm benchmark could be run. No synthetic
matrix or unsupported speedup claim was substituted.
