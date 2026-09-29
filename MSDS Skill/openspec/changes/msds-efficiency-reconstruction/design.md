# Design

## Context

In MSDS Skill v3.27.16, the mechanical execution takes ~15 seconds, but the wall-clock lifecycle takes ~42 minutes (as measured in the PU-3011 study). The gap is dominated by:
1. Cold-start preflight failures (280+ initial blockers) caused by manual JSON scaffolding.
2. Duplicate field-selection and slot-mapping decisions across Chinese and English layers.
3. Multiple build retries caused by fragile edge cases in multi-pictogram drawing embedding and Python interpreter misrouting (LibreOffice embedded Python).

See `proposal.md` for background motivation and `specs/msds-efficiency-workflow/spec.md` for formal behavioral requirements.

## Goals / Non-Goals

**Goals:**
- Provide `scripts/scaffold_evidence_packet.py` to auto-generate 80-90% of standard slot mappings, fact ledgers, and compliant SOP stages, reducing preflight blockers to <10.
- Provide a `SemanticMaster` intermediate abstraction (`source_fact_id -> slot_id -> zh_value -> en_value -> presence_decision`) where Chinese slot/presence choices are decided once and English translations inherit them directly.
- Standardize multi-pictogram embedding in `scripts/section2_ghs_policy.py` into a single run and update audit rules in `scripts/audit_openspec_overwrite.py` to recognize drawing runs as non-empty.
- Add an environment shield in `scripts/run_efficiency_workflow.py` and provide clean launch scripts (`run_msds.bat` / `run_msds.ps1`) targeting `py -3.12`.
- Extend telemetry with `timing-stage-ledger.json` to meter active review, tool wait, and repair cycle counts.

**Non-Goals:**
- Relaxing template immutability, locked bold labels, table geometry, or 7-page convergence limits.
- Bypassing preflight, OpenSpec contract validations, or DOCX/PDF release audits.
- Auto-translating text with unreviewed external heuristics: translation must still preserve source-grounded accuracy and reviewed terminology.

## Decisions

### Decision 1: Scaffolding as a separate helper tool, not automatic background bypass
- *Choice*: Create `scripts/scaffold_evidence_packet.py` as an explicit command called by `run_efficiency_workflow.py` or directly by the Agent.
- *Rationale*: Keeps evidence creation distinct from evidence approval. The scaffolded facts model remains marked `status: needs-review` and `build_allowed: false` until the Agent audits the remaining complex items.
- *Alternatives considered*: Modifying `prepare_evidence_packet.py` directly to produce approved facts. Rejected because auto-approving facts violates the fail-closed anti-hallucination principle.

### Decision 2: Semantic Master as an in-memory & file-compatible intermediate representation
- *Choice*: Extend the facts JSON structure with an optional `semantic_master` dictionary, from which both `zh` and `en` models and `output_traceability` are deterministically generated.
- *Rationale*: Avoids breaking legacy consumers that read `zh` and `en` blocks directly, while allowing the Agent to edit only one synchronized list of field entries.
- *Alternatives considered*: Replacing the entire facts JSON schema. Rejected because existing pipeline validators and legacy audit scripts depend on standard keys.

### Decision 3: Single-run pictogram drawing insertion
- *Choice*: When multiple pictograms exist (e.g. Flame + Corrosion), append both `<w:drawing>` elements inside a single `<w:r>` run without spacer paragraphs or extra whitespace runs.
- *Rationale*: Eliminates whitespace audit failures while ensuring Word and WPS render both images side by side within the cell.
- *Alternatives considered*: Separate table cells or separate paragraphs. Rejected because template geometry and row height limits are strictly locked.

### Decision 4: Runtime interpreter probing at entry
- *Choice*: At the very top of `run_efficiency_workflow.py`, inspect `sys.executable` and probe `import tkinter`. If running under LibreOffice embedded Python, attempt to re-exec via `py -3.12` or abort immediately with an actionable warning.
- *Rationale*: Prevents mysterious crashes and saves up to 70s of unhelpful retry loops.

## Risks / Trade-offs

- **[Risk: Auto-scaffolding might incorrectly map ambiguous source fields]** → *Mitigation*: The scaffold explicitly marks ambiguous fields (e.g. multi-endpoint toxicology, complex Section 2 emergency overviews) as `status: needs_manual_review` and triggers preflight blockers if unreviewed.
- **[Risk: Pictogram single-run overflow in narrow cells]** → *Mitigation*: Scale image dimensions proportionally so combined width fits the locked template cell boundary (1.2cm each).
- **[Risk: Stage telemetry overhead]** → *Mitigation*: Simple timestamp deltas written to an in-memory dict and flushed atomically at stage transitions. Machine overhead is <5ms.

## Migration Plan

1. Develop and test `scripts/scaffold_evidence_packet.py` on PU-3011 and unit tests.
2. Update `scripts/section2_ghs_policy.py` and audits for single-run multi-pictogram support.
3. Introduce runtime environment protection in `scripts/run_efficiency_workflow.py` and create launcher scripts.
4. Verify all 304+ pytest tests pass with zero regressions.
