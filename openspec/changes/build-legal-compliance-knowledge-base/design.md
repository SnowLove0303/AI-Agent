## Context

The existing skill reads canonical CSV exports directly and accepts a fixed standards list. The condition document is a Word form whose fields describe market, final use, environment, substrate/finished product, formula identities, measurements, and special requirements. The repository must remain portable, while the user-provided legal data remains outside Git and can change over time.

## Goals / Non-Goals

**Goals:**

- Use SQLite from the Python standard library as the local queryable knowledge base.
- Store regulation metadata and sources separately from derived restriction rows.
- Seed the existing 40 regulations while allowing arbitrary additional catalog entries.
- Resolve applicability before substance matching and persist each run for later review.
- Make feedback auditable and opt-in rather than silently self-modifying.

**Non-Goals:**

- Do not treat the derived SQLite baseline as the legal authority or copy the external EU Toy PDFs into the repository; the baseline database may contain derived CSV rows and must remain refreshable from source hashes.
- Do not infer legal requirements from an opaque customer code without a source document.
- Do not automatically promote reviewer feedback into a rule.
- Do not replace laboratory testing, legal review, or formal product certification.

## Decisions

1. **SQLite working database plus versioned catalog seed.** SQLite is available in Python, supports indexed queries and audit tables, and avoids a service dependency. The catalog JSON defines regulation identity and conditions; a generated baseline database is shipped with the skill and can be regenerated from it and the external data root.

2. **Derived restrictions, authoritative external files.** Restriction rows are stored in the database for fast matching, but every row keeps the canonical source path, source row, hash, version and raw JSON. Refresh is the only supported way to update derived rows, so the database cannot silently become an independent law source.

3. **Condition predicates are data, not code branches.** Each regulation stores a scope mode and token conditions for market/use/environment/substrate/special requirements. The selector evaluates these generic predicates and supports new catalog entries without adding an `if` branch.

4. **Two entry paths.** The CLI supports `--standards` for backward compatibility and `--standards auto --db` for the new condition-driven path. Explicit lists are never silently replaced by automatic selection.

5. **Audit-first feedback.** Feedback is stored with approval state, rationale, and evidence. Only a separate approval operation can convert feedback into catalog/condition data; the initial implementation exposes storage and review data without autonomous rule mutation.

## Data Model

- `regulations`: canonical identity, aliases, jurisdiction, scope mode, status, family and timestamps.
- `regulation_sources`: local files, official URLs, versions, effective dates, hashes and notes.
- `regulation_conditions`: field/operator/value predicates and human-readable rationale.
- `restriction_rules`: normalized CAS/EC/name/group/limit/unit/scope/test method plus raw source row.
- `judgment_runs`: facts hash, facts JSON, mode, selected regulations and timestamps.
- `judgment_results`: per-regulation status, selection reason and result/evidence JSON.
- `feedback`: reviewer correction, evidence, approval state and audit link.

## Risks / Trade-offs

- [Derived DB drift] → Store source hashes and require refresh; reports expose DB/source identity.
- [Over-selection] → Prefer `不适用` with a reason for downstream-only scopes and show every candidate decision.
- [Under-selection after new law registration] → New entries require explicit scope conditions; provide a catalog validation command.
- [Feedback poisoning] → Feedback defaults to unapproved and cannot affect selection until approved.
- [Large EU Toy sources] → Register directory/source documents and ingest structured rows only when available; retain PDF references without copying them.

## Migration Plan

1. Initialize a new working database from the catalog and canonical data root.
2. Run the existing explicit-list workflow unchanged as a compatibility check.
3. Run the new `auto` workflow with the condition-sheet facts and compare the selection matrix.
4. Review and approve any feedback-derived condition additions manually.
5. Roll back by deleting the derived working database and reverting the feature commit; external source files and existing reports remain unchanged.
