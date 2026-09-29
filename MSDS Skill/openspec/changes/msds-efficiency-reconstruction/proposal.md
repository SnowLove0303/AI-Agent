# Proposal

## Why

In MSDS Skill v3.27.16, timing studies on real source documents (such as PU-3011) revealed that while mechanical operations take only ~15 seconds, the total wall-clock duration reaches ~42 minutes with an unmeasured 28:52 observation gap. This efficiency bottleneck stems from three root causes:
1. Lack of scaffolding tools leading to 280+ initial Preflight blockers and 5-7 rounds of manual JSON repair.
2. Duplicate manual labor where Chinese and English fields are independently mapped from scratch without a controlled semantic master intermediate layer.
3. Fragile edge cases in multi-pictogram embedding, whitespace audits, and runtime Python interpreter resolution (e.g. LibreOffice embedded Python collision).

This change refactors the workflow around automated scaffolding, single-decision semantic master mapping, runtime environment protection, and fine-grained telemetry to radically improve end-to-end efficiency without weakening locked templates or fail-closed release gates.

## What Changes

- **Runtime Environment Shield**: Add startup interpreter validation to detect and bypass unsuited embedded Python interpreters (such as LibreOffice without Tk) and guarantee standard Python 3.12+ execution.
- **Evidence Scaffolding Generator**: Add `scripts/scaffold_evidence_packet.py` to automatically pre-populate deterministic 1:1 section/table slot mappings, compliant SOP stages, and candidate scaffolds from extracted units, reducing initial Preflight blockers from 280+ to <10.
- **Controlled Semantic Master Intermediate Layer**: Introduce `semantic_master` model (`source_fact_id -> template_slot_id -> zh_value -> en_value -> presence_decision`) allowing one-time semantic choice on Chinese content while English incrementally inherits mapped slots, eliminating bilingual duplicate decision-making.
- **Multi-Pictogram and Layout Robustness**: Standardize Section 2 GHS multi-pictogram embedding into a single run, prevent spacer whitespace audit failures, and align audit checks with image-bearing cells.
- **Active Stage Telemetry**: Implement fine-grained stage ledger (`timing-stage-ledger.json`) tracking active review time, tool wait intervals, and repair cycles to eliminate the 28:52 invisible time window.

## Capabilities

### New Capabilities
- `msds-efficiency-workflow`: Automated evidence scaffolding, single-decision semantic master routing, runtime environment shield, multi-pictogram layout hardening, and active stage telemetry for end-to-end MSDS generation.

### Modified Capabilities
<!-- No requirement changes to existing msds-table-search or msds-tds-batch capabilities -->

## Impact

- **Affected code**: `scripts/run_efficiency_workflow.py`, `scripts/extract_source_facts.py`, `scripts/section2_ghs_policy.py`, `scripts/audit_openspec_overwrite.py`, `scripts/audit_field_mapping_and_whitespace.py`, new `scripts/scaffold_evidence_packet.py`, new launcher scripts.
- **Backward compatibility**: Zero breaking changes to formal templates, locked skeletons, 16-section structures, or final 4 DOCX + 4 PDF deliverable criteria.
- **Verification**: Fully covered by unit tests, Preflight verification on PU-3011, and end-to-end matrix builds.
