# Specification: Jev System One Decision Engine

## Requirements
- The system MUST support on-demand invocation of Jev System One for ambiguous chemical classifications and cross-section routing.
- The system MUST never crash or block the overwrite pipeline if the remote Jev endpoint is unavailable; it MUST fall back gracefully to deterministic conservative rules.
- The system MUST record all decisions into an auditable ledger.
