# Tasks

## 1. Runtime Environment Shield

- [x] 1.1 Add Python interpreter detection and Tkinter probing in `scripts/run_efficiency_workflow.py`, verified by running unit tests and checking that unsuited interpreters raise an actionable warning.
- [x] 1.2 Create launcher scripts `run_msds.bat` and `run_msds.ps1` targeting `py -3.12`, verified by invoking them from PowerShell.

## 2. Preflight Evidence Scaffolding

- [x] 2.1 Implement `scripts/scaffold_evidence_packet.py` to auto-generate default 1:1 slot mappings, compliant SOP stages, and candidate fact ledger from `evidence-packet.json`, verified by running against PU-3011 evidence packet and checking blocker reduction.
- [x] 2.2 Wire scaffold generation into `run_efficiency_workflow.py` as `--auto-scaffold`, verified by checking preflight execution on scaffolded inputs.

## 3. Controlled Semantic Master Intermediate Model

- [x] 3.1 Implement `SemanticMaster` data structure and parser in `scripts/extract_source_facts.py` to bind source facts to template slots, Chinese values, English translations, and presence decisions into one synchronized ledger.
- [x] 3.2 Add translation inheritance logic where English values inherit reviewed slot IDs and fact linkage from the Chinese semantic master, verified by running bilingual parity tests.

## 4. Multi-Pictogram & Layout Hardening

- [x] 4.1 Update `scripts/section2_ghs_policy.py` to embed multiple hazard pictograms into a single text run without blank spacers or extra runs, verified by multi-image fixture tests.
- [x] 4.2 Update `scripts/audit_openspec_overwrite.py` and whitespace checks to accept drawing runs in pictogram cells as non-empty, verified by running tests on multi-pictogram fixtures.

## 5. Active Stage Telemetry & Verification

- [x] 5.1 Implement stage timing recorder in `run_efficiency_workflow.py` outputting `timing-stage-ledger.json` with active agent seconds, tool wait, and repair cycle telemetry, verified by verifying ledger file emission.
- [x] 5.2 Execute complete test suite (`pytest`) and verify all tests pass with zero regressions.
