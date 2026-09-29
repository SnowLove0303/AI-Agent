# Spec Delta

## Purpose

Provides automated evidence scaffolding, single-decision semantic master mapping, runtime Python environment shielding, multi-pictogram layout hardening, and fine-grained stage telemetry to maximize end-to-end MSDS generation efficiency without relaxing locked template or fail-closed release gates.

## ADDED Requirements

### Requirement: Guard runtime Python interpreter environment
The application SHALL verify that the executing Python interpreter satisfies all core dependency requirements and is not an embedded third-party environment lacking required standard GUI or document processing libraries. When an unsuited interpreter (such as LibreOffice embedded Python lacking Tkinter) is detected, the workflow SHALL redirect to the standard system Python 3.12+ interpreter or fail fast with actionable guidance.

#### Scenario: Intercept unsuited embedded interpreter
- **WHEN** the workflow is launched from an embedded interpreter lacking Tkinter or document dependencies
- **THEN** the system prevents execution failure by redispatching to standard Python 3.12+ or returning a clear configuration error before extraction begins

#### Scenario: Pass valid standard Python runtime
- **WHEN** the workflow is executed under a standard Python 3.12+ environment with required libraries
- **THEN** the runtime guard passes cleanly without added latency

### Requirement: Generate automated Preflight evidence scaffold
The application SHALL provide a scaffolding tool that converts raw source-unit coverage into a pre-structured facts model containing fact ledger entries, default 1:1 section mapping bindings, output traceability records, and compliant execution SOP states.

#### Scenario: Scaffold cold-start evidence packet
- **WHEN** raw source extraction completes with verified source units
- **THEN** the scaffolding tool populates draft fact ledger entries and maps deterministic section slots
- **AND** sets compliant preflight SOP stages (`lock_input`, `inventory_source`, `build_fact_ledger`, `semantic_route`, `normalize_structure_only`, `review_mapping_and_traceability`, `plan_template_mutations`) to reviewed/completed while subsequent build stages remain pending

#### Scenario: Suppress trivial preflight blockers
- **WHEN** an extracted source is scaffolded and tested against preflight rules
- **THEN** initial trivial blockers related to missing trace skeletons, unlinked standard labels, and incomplete SOP stages are reduced to fewer than 10 actionable items

### Requirement: Provide controlled Chinese semantic master intermediate model
The application SHALL support a unified semantic master intermediate record binding each verified `source_fact_id` to its target `template_slot_id`, approved Chinese text, approved English text, and presence decision. English outputs SHALL inherit the reviewed slot mapping and source provenance directly from the locked Chinese semantic master.

#### Scenario: Inherit slot mapping for English translation
- **WHEN** a field's Chinese value, template slot, and omission/presence decision are approved in the semantic master
- **THEN** the English translation entry inherits the same slot ID and source fact ID without requiring independent slot re-mapping or re-disposition

#### Scenario: Maintain independent bilingual fact traceability
- **WHEN** bilingual values are populated into destination templates
- **THEN** both Chinese and English outputs independently trace back to the same verified source fact ID

### Requirement: Standardize Section 2 multi-pictogram layout and whitespace audit
The application SHALL embed multiple GHS pictograms into a single text run within the Section 2 label element value cell, without artificial whitespace runs, blank spacer paragraphs, or lost images. The release audit SHALL recognize drawing runs as valid non-empty cell content.

#### Scenario: Embed multiple pictograms in single run
- **WHEN** a source document contains multiple GHS hazard pictograms
- **THEN** all pictograms are inserted into one continuous run in the designated template cell
- **AND** no extra blank spacer runs are emitted between or after images

#### Scenario: Audit pictogram-only cell
- **WHEN** a Section 2 cell contains only embedded pictogram drawings
- **THEN** the whitespace and empty-value audits recognize the drawing content and pass without raising empty-cell or missing-value errors

### Requirement: Record fine-grained active stage telemetry
The application SHALL record distinct timestamps and durations for individual workflow stages, including extraction review, Chinese semantic mapping, English translation, preflight repair cycles, and visual QA.

#### Scenario: Log sub-stage timings in ledger
- **WHEN** an end-to-end or preflight workflow cycle is executed
- **THEN** the timing ledger records start time, end time, active duration, tool wait duration, and blocker repair counts for each completed phase
- **AND** distinguishes automated machine execution time from active human/agent review intervals
