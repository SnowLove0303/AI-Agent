## Purpose

为 MSDS 覆写流水线提供可复用、可测量且不削弱质量门禁的效率能力，减少源文件、事实映射、审计和 PDF 转换中的重复工作，同时确保源事实、模板结构和正式交付证据仍然拥有明确且不可越权的权威边界。

## ADDED Requirements

### Requirement: Source evidence reuse remains review-bound

The system MUST provide a reusable source-evidence packet containing the complete readable source inventory, source identity, candidate fact ledger, review queue and mapping checkpoints. A packet MAY be reused only when the original source bytes, source format, adapter/extractor contract, packet schema and active source-interpretation rules match. Reuse MUST never set approved status, bypass source review or permit direct template overwrite.

#### Scenario: Matching packet is reused

- **WHEN** the source bytes, source format, adapter/extractor contract, packet schema and active interpretation rules match a stored packet
- **THEN** the system reuses the mechanical inventory, records a cache hit and keeps the packet in a review-required state

#### Scenario: Packet identity is stale

- **WHEN** the source hash, format, adapter/extractor contract, packet schema or interpretation rules differ from the stored packet
- **THEN** the system rejects reuse, performs a fresh mechanical extraction and records the cache miss reason

#### Scenario: Agent tries to build from an unreviewed packet

- **WHEN** a packet has unresolved review items, incomplete source mapping, incomplete output traceability or `build_allowed` is false
- **THEN** the system blocks template cloning and formal output generation with actionable blockers

### Requirement: Product-family candidates cannot replace source facts

The system MUST support declarative product-family or ontology candidates for repeated mapping and rule selection, but every final non-empty product value MUST remain bound to current-source evidence, reviewed translation traceability or an explicitly permitted controlled overlay. A family candidate that is absent from or contradicted by the current source MUST remain a candidate or be omitted; it MUST NOT auto-fill the output.

#### Scenario: Candidate is confirmed by the current source

- **WHEN** a family candidate matches a reviewed source fact and has a source locator and disposition
- **THEN** the system may reuse the mapping rule, records the provenance and permits the approved value to enter the semantic write plan

#### Scenario: Candidate has no current-source support

- **WHEN** a family candidate is not found in the current source and is not an allowed controlled overlay
- **THEN** the system leaves the corresponding value absent or applies the ordinary source-presence policy, and does not synthesize a value

#### Scenario: Candidate conflicts with the source

- **WHEN** a family candidate conflicts with a current-source value or classification
- **THEN** the system marks the conflict as a release blocker and requires an explicit reviewed resolution before overwrite

### Requirement: Legacy-source conversion cache is source-bound in the formal path

The formal build path MUST accept a persistent cache location for approved legacy-source conversion and reuse a valid converted DOCX only when its original-source hash, source format and adapter version match. The source-grounding check MUST use the prepared, source-bound representation when the original format cannot be searched directly, while preserving the original source path and hash in evidence.

#### Scenario: Legacy conversion cache hit

- **WHEN** a `.doc`, `.odt` or `.rtf` source has a valid cache entry whose identity matches the current source and adapter contract
- **THEN** the build reuses the converted DOCX, records the adapter cache hit and preserves the original source identity

#### Scenario: Legacy conversion cache miss

- **WHEN** no valid matching converted DOCX exists
- **THEN** the build performs one approved conversion, publishes the result atomically to the cache and uses that prepared representation for extraction and grounding

#### Scenario: Cache entry is invalid

- **WHEN** a cached conversion is partial, not a valid DOCX or bound to different source bytes/format/adapter version
- **THEN** the system ignores it, performs a fresh conversion and never uses the invalid entry as source evidence

### Requirement: Shared audit context preserves independent release gates

The system MUST permit independent semantic, template, value-typography, whitespace, numbering, geometry, terminology, lineage and render checks to reuse a read-only parsed representation of one staged DOCX. Context reuse MUST not remove a gate, change blocker precedence, or make an in-memory checkpoint authoritative over the saved final DOCX.

#### Scenario: Audits share a parsed document

- **WHEN** multiple release gates inspect the same staged DOCX during one build
- **THEN** they may consume a common read-only index and each produces its own pass/fail evidence without reopening the DOCX unnecessarily

#### Scenario: Saved artifact differs from memory

- **WHEN** the saved staged DOCX does not match the in-memory audit representation or final-file lineage cannot be verified
- **THEN** the release is blocked and the saved DOCX is revalidated as the authoritative conversion input

#### Scenario: A gate finds a locked-template violation

- **WHEN** a shared audit context detects changed labels, sequence, bold label formatting, table structure, geometry or other locked content
- **THEN** the corresponding blocking gate remains failed and optimization does not downgrade it to a warning

### Requirement: Performance telemetry distinguishes work categories

The system MUST emit machine-readable timing and progress data that distinguish source/evidence preparation, constrained normalization, fixed-template overwrite, post-overwrite fine-tuning, DOCX save, release audit, PDF conversion wall time, cache hit/miss and retry/failure status. Telemetry MUST be observational and MUST NOT control whether a release gate runs.

#### Scenario: Comparable matrix run completes

- **WHEN** a four-variant MSDS matrix completes
- **THEN** the matrix report records per-stage events, aggregate durations, per-variant DOCX/PDF timings, cache decisions, worker count and the final output identity

#### Scenario: Fast diagnostic mode is used

- **WHEN** the Agent invokes preflight-only, DOCX-only or an audited DOCX preview checkpoint
- **THEN** the system returns the requested early feedback and clearly marks that the checkpoint is not a formal eight-file release

#### Scenario: Telemetry fails

- **WHEN** timing or progress recording cannot be written
- **THEN** the system retains the original build and release-gate semantics; telemetry failure MUST NOT convert a blocker into a pass

### Requirement: PDF scheduling is bounded and evidence-preserving

The system MUST convert only saved, fully audited final DOCX masters into PDFs, MAY use bounded parallel workers, and MUST preserve one-to-one DOCX/PDF source and output hashes. The default scheduling strategy MUST remain conservative until comparable worker-count measurements demonstrate both throughput improvement and WPS stability.

#### Scenario: Bounded PDF batch succeeds

- **WHEN** all four DOCX masters pass their gates and bounded PDF workers convert them successfully
- **THEN** the system records each DOCX/PDF pair, hashes and converter identity, then continues to the complete matrix gate

#### Scenario: WPS worker count is unstable

- **WHEN** a higher worker count causes converter failures, file locks, timeouts or inconsistent output
- **THEN** the run fails closed or falls back to a configured conservative worker count, records the evidence and never publishes a partial matrix

#### Scenario: PDF input is not the final audited DOCX

- **WHEN** a PDF conversion request is not bound to the saved final DOCX that passed the release gates
- **THEN** the conversion or matrix gate blocks the release

### Requirement: Four-stage order and mutation boundary remain invariant

The system MUST execute full source extraction, constrained information normalization, fixed-structure template overwrite and post-overwrite fine-tuning in that order. Efficiency features MUST NOT permit changes to template labels, sequence, bold label formatting, table architecture, geometry, headers or footers; only approved value-cell writes, empty/presence decisions and explicitly authorized styled-row operations remain permitted.

#### Scenario: Optimized run follows the business stages

- **WHEN** an Agent runs the optimized pipeline
- **THEN** the recorded stage order is extraction, normalization, fixed template overwrite and fine-tuning, with no DOCX mutation before semantic approval

#### Scenario: Optimization attempts a forbidden mutation

- **WHEN** an optimization path attempts to rebuild a table, change a label, alter boldness/formatting, globally hide rows or fill unsupported facts
- **THEN** the system blocks the operation and reports the locked-template or source-grounding violation

#### Scenario: Empty-value omission is applied

- **WHEN** a source field is absent or explicitly unsupported
- **THEN** the authorized fine-tuning policy hides/removes the corresponding value row where required and repairs visible sequence prefixes without changing the locked labels or table architecture
