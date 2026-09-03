# DOCX-to-PDF converter adoption

## Decision

The MSDS publication chain uses the bundled `scripts/convert_docx_to_pdf.py`
adapter. It invokes the host's native WPS/Word-compatible `word2pdf` exporter
through `kwpsconvert.exe`/`wpscli.exe` and a temporary output directory. The
adapter converts one already-audited DOCX to one same-basename PDF, then writes
conversion evidence containing both file hashes, the converter version, page
count and timing.

The adapter is intentionally small and dependency-light. It uses one
conversion entry point and does not create a PDF content branch, independently
redraw a table, or post-edit the PDF. The WPS exporter is selected because the
approved templates are authored in a WPS/Word-compatible layout; using another
office engine can materially change pagination, inherited paragraph spacing and
table appearance.
The temporary-output and atomic-replacement pattern follows the verified
headless conversion pattern from [Guki125/dconv](https://github.com/Guki125/dconv)
without vendoring an unrelated CLI or PDF-to-DOCX path.

## Alternatives evaluated

- [AlJohri/docx2pdf](https://github.com/AlJohri/docx2pdf) uses Microsoft Word
  automation on Windows. It is not used because the maintained worker has one
  WPS/Word-compatible conversion entry point and must not create a second
  renderer branch.
- [documents4j/documents4j](https://github.com/documents4j/documents4j) can
  delegate to native Microsoft Word, but it inherits Office installation,
  activation, process-state and service-context constraints. It remains a
  documented alternative for a future Office-equipped worker, not a hidden
  runtime dependency.
- LibreOffice was rejected for this layout baseline after visual regression:
  the same final DOCX produced materially different page counts, whitespace,
  word spacing and table pagination from the supplied WPS/Word reference.

## Non-negotiable publication order

```text
semantic model
  -> final DOCX generation
  -> DOCX semantic/geometry/terminology QA
  -> DOCX render QA
  -> convert_docx_to_pdf.py (WPS word2pdf)
  -> PDF preflight and page-count check
  -> PDF full-page render QA
  -> eight-file release gate
```

The adapter never independently authors or edits a PDF after conversion, never
creates a PDF content branch, and never uses a PDF to repair or regenerate a DOCX. A conversion
failure or a locked destination is a release blocker; the adapter writes to a
temporary file first so an existing customer file is not partially replaced.
