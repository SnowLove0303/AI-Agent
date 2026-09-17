# Design

## Decision flow

1. Load the complete facts and the condition-driven regulation selection.
2. Evaluate the selected regulations against the supplied component list and source rows.
3. Use `strict_closed_world` by default. No component match is a pass; a matched rule with no comparable measurement, no structured limit, an unparsable limit, or incompatible units is also a pass under the declared complete-facts assumption, with a traceable closed-world detail.
4. If `allow_uncertainty` is set in facts or by CLI, unresolved matched-rule details become `需补证`. An explicitly named opaque standard remains `需补证` because the user directly requested a standard whose current rule source is absent; condition-driven runs do not introduce that uncertainty by default.
5. Persist the run to SQLite when a database is supplied.
6. Render the structured report to DOCX, convert it with the installed LibreOffice CLI, and verify that the resulting PDF has at least one page and extractable report text. A conversion or verification failure is a non-zero run failure.

## PDF implementation

Use the already-installed `python-docx` package to create the temporary DOCX and LibreOffice (`soffice --headless`) to convert it. Use `pypdf` to verify the output. No new package or service is required. The temporary DOCX is outside the repository and is removed after conversion; only the caller-provided PDF path is a deliverable.

## Compatibility

Existing callers can still request JSON or Markdown through `--format`, but must also pass `--output-pdf`. Existing programmatic `judge()` calls continue to work with strict mode as the default; `allow_uncertainty=True` is an opt-in parameter.
