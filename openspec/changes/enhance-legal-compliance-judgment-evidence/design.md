## Context

See `proposal.md` and the existing `add-legal-compliance-judgment-skill` change for the original report-shaped workflow. The current engine already reads the main six CSV exports and resolves basic scope, but its result objects retain raw rows without a stable evidence projection. Its numeric comparison also treats all extracted numbers as dimensionless, which can produce a false pass or an unnecessary evidence gate.

## Goals / Non-Goals

**Goals:**

- Preserve source and version evidence without copying the external data set.
- Normalize only conversions with an explicit, defensible relationship.
- Keep the four result labels and the closed-world assumption unchanged.
- Make the Markdown matrix usable as the direct precursor to the existing PDF report template.

**Non-Goals:**

- Do not infer private customer requirements from an opaque code.
- Do not parse every EU Toy PDF on material-only runs or claim laboratory migration testing from formulation data.
- Do not add a database, web service, third-party package, or changes to MSDS/TDS skills.

## Decisions

1. **Use a source-family metadata map.** Main CSV and companion metadata filenames remain in the local registry. The loader reads metadata only for selected families and stores a compact version summary, avoiding a second data store.

2. **Attach a normalized evidence projection beside the raw row.** Raw fields remain available for audit, while `match_key`, `source_row`, `limit`, `unit`, `test_method`, and `source_version` provide stable report fields. This keeps the report code independent of every CSV schema spelling.

3. **Use a quantity parser with explicit units.** Parse `%`, `ppm`, `mg/kg`, `mg/L`, and unitless values only when the surrounding rule declares the same unit. Percentage-to-ppm and mg/kg-to-ppm conversions are explicit; area, migration, VOC, and formulation units are not silently mixed.

4. **Keep scope rules before matching.** A complete product that is not a toy, EEE, package, wall coating, or wood coating is `不适用` for those downstream standards. A standard remains `需补证` only after scope is active and no structured rule or compatible measurement exists.

5. **Test with a small synthetic fixture plus the canonical data root.** Unit tests exercise conversion and evidence projection without depending on the user's large files; one smoke command reads the actual six CSV families and the EU Toy directory to verify integration and row counts.

## Risks / Trade-offs

- [Ambiguous legal limit text] → Keep the raw rule text and return `需补证` when a safe numeric extraction is not possible.
- [Unit wording varies across CSVs] → Use explicit field aliases and test representative `%`, `ppm`, and `mg/kg` values; do not use a generic dimensionless fallback.
- [Metadata file drift] → Treat the main source file as required, companion metadata as recorded when available, and surface missing metadata in the source summary.
- [Closed-world assumption] → Print it in every report and preserve the existing skill contract; this is an evaluation mode, not a laboratory certificate.

## Migration Plan

1. Add the new change artifacts and update the existing skill in an isolated worktree.
2. Run unit tests, OpenSpec validation, and the canonical-data smoke check.
3. Push only the skill and this change to `origin/main`.
4. Roll back by reverting the single enhancement commit; the previous skill remains usable because its CLI and four labels are preserved.
