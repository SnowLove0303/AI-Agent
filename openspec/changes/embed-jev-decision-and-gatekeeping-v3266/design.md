# Design: Jev System One Dual-Path Decision Architecture

## Dual-System Flow
- Fast-Path (System 2): Deterministic regex/hash lookups for standard labels (0ms).
- Slow-Path (System 1): On-demand Jev System One query with prompt contextualization and confidence scoring.
- Fail-Safe Layer: Catch network exceptions and fall back to conservative deterministic defaults.
- Audit Trail: Log every transaction into `GLOBAL_LEDGER` exported to `jev_decision_ledger.json`.
