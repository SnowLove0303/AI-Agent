# PDF publication contract

The PDF layer is strictly derivative from the four final audited DOCX masters. It must not introduce an independent content, translation, layout, or company branch. The only permitted path is `final audited DOCX -> deterministic conversion adapter -> PDF preflight -> full-page render QA`. Convert each DOCX one-to-one to the same basename `.pdf`, then preflight and render every PDF page for visual QA. Any PDF defect blocks the eight-file release. v2.9 DOCX overwrite requirements remain fully binding upstream.

The maintained conversion entry point is `scripts/convert_docx_to_pdf.py`. It
uses an isolated LibreOffice headless profile, converts through a temporary
directory, atomically writes the target PDF, and records source/target hashes,
converter version and page count in an evidence JSON file. The adapter is
invoked only after the corresponding DOCX has passed semantic, geometry and
render QA. It must not be replaced with independent PDF authoring or a PDF
post-edit step.
