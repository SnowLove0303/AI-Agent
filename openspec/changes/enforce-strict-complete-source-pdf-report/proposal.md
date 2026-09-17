# Proposal: enforce strict complete-source PDF delivery

## Why

The skill already treats MSDS/TDS facts as complete in principle, but its runtime can still return `需补证` for an omitted measurement, an unparsed limit, or a source record that is not executable. That contradicts the requested closed-world workflow: the supplied material is the complete information source, and an omitted substance must be treated as absent rather than triggering a request for another report. The CLI also permits JSON/Markdown-only delivery, so a run can finish without the required written PDF report.

## What changes

- Make strict closed-world evaluation the default. Omitted substances are absent, and unresolved matched-rule details resolve to `符合（基于完整资料假设）` unless uncertainty is explicitly enabled.
- Preserve `需补证` only for an explicitly requested uncertainty mode or an explicitly named standard whose source is not executable.
- Keep condition-driven selection broad: evaluate every enabled regulation whose jurisdiction and condition-sheet scope match the supplied facts, including regulations registered after the initial 40-item seed.
- Require every CLI judgment run to create and verify a PDF report. JSON/Markdown remain optional machine-readable intermediates, not final delivery formats.
- Record the uncertainty policy and PDF path in the report metadata and PDF content.

## Scope

In scope: `legal-compliance-judgment-skill` judgment logic, CLI, PDF report generator, documentation, OpenSpec specs, and tests.

Out of scope: changing the source legal-data files, altering the MSDS/TDS overwrite skills, or silently creating a second data repository.
