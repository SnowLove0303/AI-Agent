## Why

The existing compliance report is useful as a human-readable template, but its conclusions stop at “cannot determine” even when the user explicitly states that the MSDS and TDS are complete and authoritative. The repository needs a reusable legal/compliance judgment skill that combines the existing product facts with the maintained local restriction datasets and produces deterministic, traceable results.

## What Changes

- Add a standalone legal-compliance judgment skill in a new repository folder.
- Add a closed-world complete-facts mode: MSDS/TDS facts are treated as exhaustive; omitted substances and omitted uses are not treated as unknown.
- Read the existing REACH SVHC, REACH Annex XVII, EU RoHS, HSF-001, BSBL, and AfPS GS 2019:01 PAK CSV exports without copying the canonical datasets.
- Register the EU Toy Safety source files and resolve toy requirements by applicability rather than returning a generic manual-review result for the current PU-1002 leather/plastic coating use.
- Match product components by CAS, EC, normalized names, group members, and controlled aliases.
- Emit a report-shaped result matrix using the approved PU-1002 PDF report structure, including result, rationale, matched source rows, limits, source version, and assumptions.
- Reduce indeterminate outcomes to four explicit results: `符合（基于完整资料假设）`, `不符合`, `不适用`, and `需补证`.
- Add deterministic unit tests and evaluation prompts for exact matches, no-match passes, use-scope exclusions, limits, group entries, and unidentified customer specifications.

## Capabilities

### New Capabilities

- `legal-compliance-judgment`: Deterministic material and product-use compliance screening against the maintained local legal/regulatory restriction sources and the report template.

### Modified Capabilities

- None.

## Impact

- Adds one self-contained skill folder under the repository root.
- Adds one OpenSpec capability and its implementation tests.
- Reads external canonical data from `F:\APP Location\Guanzhi Tong\法律法规物质清单` through a configurable data-root setting; no second copy of the legal datasets is created.
- Does not modify the existing MSDS Skill, TDS Skill, templates, release archives, or the user's existing uncommitted changes.
