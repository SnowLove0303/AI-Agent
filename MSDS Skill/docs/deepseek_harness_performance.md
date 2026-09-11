# DeepSeek Harness performance runbook

## What changed in 3.20.0

The former matrix loop completed one language/company DOCX, converted its PDF,
and only then moved to the next variant. WPS discovery and version probing also
repeated for every PDF. A slow or unavailable office process therefore made a
20-minute run look as if no MSDS had been produced, even when earlier DOCX
work was already complete.

The maintained path now has three observable phases:

1. Validate the selected source, the reviewed facts model, the OpenSpec/source
   evidence records and both locked templates once.
2. Build and audit all four DOCX masters first. These are the authoritative
   semantic/layout masters. An optional preview directory exposes these files
   before PDF conversion, but it is not a release directory.
3. Resolve and version-check WPS once, then convert the four final DOCX files
   as a bounded PDF batch. The final matrix is promoted only after all eight
   files and all release gates pass.

The scheduling change does not relax any gate and does not permit template,
label, sequence, bold-format, geometry or source-evidence changes.

## Recommended command

```text
python scripts/build_eight.py --source SRC.docx --facts MODEL.json --out OUT \
  --pdf-workers 2 --progress-file OUT/matrix-progress.json \
  --docx-preview-dir OUT/_docx_preview
```

The Harness should call this once per reviewed facts model. It should not ask
the Agent to create four independent documents or render pages after each
field edit.

## Runtime controls

- `--pdf-workers 2`: default bounded parallel conversion. Use `1` if the WPS
  host serializes office processes or shows instability. Keep the bound small;
  more workers do not repair a missing converter.
- `--wpscli PATH`: explicit WPS CLI path when automatic discovery is not
  reliable in the Harness environment.
- `--progress-file PATH`: atomically updated JSON file containing the latest
  phase, variant and timing event. Standard output also emits each event as a
  line beginning with `MSDS_PROGRESS `.
- `--docx-preview-dir DIR`: copies the four individually audited DOCX masters
  after DOCX completion and before PDF conversion. Choose a directory such as
  `OUT/_docx_preview`; this directory is excluded from source discovery.
- `--no-pdf`: diagnostic DOCX-only mode. It is useful for isolating semantic
  or template work, but it is not an eight-file release.

## Failure interpretation

If no progress event is reached, inspect source/facts/OpenSpec validation. If
the last event is `pdf_preflight_started`, check WPS login/session state and
the preflight error text. If `docx_ready` events appear, DOCX construction is
working and the preview directory can be inspected. If the run reaches
`pdf_converter_ready` but stops during `pdf_batch_started`, lower
`--pdf-workers` to `1` and inspect the converter's own error output.

LibreOffice, `soffice.exe`, ReportLab and PDF-only authoring are intentionally
not bundled or used as fallbacks. A missing WPS converter must fail clearly;
it must never be hidden by an unapproved alternate PDF path.

## Quality boundary

The performance profile only changes scheduling, caching and observability.
The Agent still must complete the full source-coverage/fact-ledger/mapping/
traceability read and review contract before cloning a template. The runtime
still allows only source-grounded value-cell writes, empty-value hide/show
decisions and the explicitly permitted complete styled-row insertions or
deletions. Formal output remains exactly four DOCX plus four corresponding
PDFs, with no promotion if any semantic, format, geometry, lineage or render
gate fails.
