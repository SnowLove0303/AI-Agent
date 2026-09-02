# DOCX-to-PDF converter adoption

## Decision

The MSDS publication chain uses the bundled `scripts/convert_docx_to_pdf.py`
adapter. It invokes LibreOffice headless with an isolated user profile and a
temporary output directory. The adapter converts one already-audited DOCX to
one same-basename PDF, then writes conversion evidence containing both file
hashes, the converter version, page count and timing.

The adapter is intentionally small and dependency-light. It adopts the
headless conversion pattern used by the GitHub project [Guki125/dconv](https://github.com/Guki125/dconv)
without vendoring an unrelated CLI, package installer, or PDF-to-DOCX path.
The local environment has LibreOffice available and does not have Microsoft
Word, so this is the verified primary path for this Skill.

## Alternatives evaluated

- [AlJohri/docx2pdf](https://github.com/AlJohri/docx2pdf) uses Microsoft Word
  automation on Windows. It requires Word to be installed, so it is not the
  primary path on the current host.
- [documents4j/documents4j](https://github.com/documents4j/documents4j) can
  delegate to native Microsoft Word, but it inherits Office installation,
  activation, process-state and service-context constraints. It remains a
  documented alternative for a future Office-equipped worker, not a hidden
  runtime dependency.

## Non-negotiable publication order

```text
semantic model
  -> final DOCX generation
  -> DOCX semantic/geometry/terminology QA
  -> DOCX render QA
  -> convert_docx_to_pdf.py
  -> PDF preflight and page-count check
  -> PDF full-page render QA
  -> eight-file release gate
```

The adapter never independently authors or edits a PDF after conversion, never
creates a PDF content branch, and never uses a PDF to repair or regenerate a DOCX. A conversion
failure or a locked destination is a release blocker; the adapter writes to a
temporary file first so an existing customer file is not partially replaced.
