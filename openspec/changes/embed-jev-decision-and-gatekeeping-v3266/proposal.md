# Change Proposal: Embed Jev System One Decision Engine & Dual-Path Gatekeeper (v3.26.6)

## Problem
In chemical document overwriting (MSDS & TDS), rule-based systems are deterministic and fast, but fail on ambiguous texts, complex chemical nuances (e.g. amine neutralizers bound into salts, SCL thresholds, non-standard TDS property names, multi-tier toxicology distinctions, and independent-row necessity). Pure generative LLMs risk hallucinations and style degradation.

## Proposed Resolution
1. **Core Jev Client (`scripts/jev_engine.py`)**:
   - Resilient TypeSafe System One client using environment variable `ZEN_API_KEY` / `JEV_API_KEY` or `~/.jev/zen.key`.
   - Guaranteed zero-stop graceful fallback on network timeout or server errors.
   - Comprehensive `DecisionLedger` logging every query and decision to `jev_decision_ledger.json`.
2. **Domain Decision & Gatekeeping Adjudicator (`scripts/jev_domain_adjudicator.py`)**:
   - GHS Signal Word arbitration (`adjudicate_ghs_signal_word`).
   - Cross-section fact routing for amine salts/SCL (`adjudicate_cross_section_fact`).
   - Independent row splitting arbitration (`adjudicate_row_splitting`).
   - TDS non-standard technical indicator mapping (`adjudicate_tds_slot_mapping`).
   - Pre-release semantic consistency auditing (`audit_semantic_consistency`).
3. **Dual-Path Strategy**:
   - 0ms fast-path for unambiguous local patterns; on-demand Jev arbitration for fuzzy/borderline cases.
