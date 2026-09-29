# Design

## Context

See proposal.md. The current parser emits normalized Word table records and a per-selection JSON view. It does not export the whole record, preserve paragraph blocks independently, map likely fields to their source cells, or disclose all unnormalized OOXML tags.

## Goals / Non-Goals

**Goals:** Keep the normalized structure easy for an Agent to consume while retaining original Word XML as a recovery/evidence layer. Make field links traceable and uncertainty visible.

**Non-Goals:** Automatically rewrite MSDS content, assert that heuristic field candidates are authoritative, or infer missing PDF semantics.

## Decisions

- Keep the existing record/cell model compatible and add a version marker, paragraph blocks, row gap metadata, raw direct-property maps, and source-coordinate field candidates.
- Preserve readable `word/` XML parts once per document in the exported JSON instead of duplicating raw XML for every cell. This avoids silent loss while limiting repetition.
- Keep normalized fields instead of exporting only raw XML; raw-only data is difficult for an Agent to consume, while cell-level XML duplication would unnecessarily inflate the export.
- Treat bold/colon and adjacent-cell relationships as evidence for field candidates; always include the underlying exact cell text and coordinates.
- Export a copy of imported data without the temporary native-preview path. The source document itself stays read-only.
- For PDFs, report word/table geometry and font evidence when available; when table text extraction is blank, map positioned words to detected rows/cells and mark that fallback explicitly.

## Risks / Trade-offs

- [JSON can be larger because it includes source OOXML] → Preserve XML parts once per document and omit temporary preview data.
- [Label/value heuristics can be ambiguous] → Label them as candidates, include evidence and source coordinates, and leave source cell text unchanged.
- [PDF extraction cannot recover all Word-style formatting or table semantics] → Keep the native PDF preview and surface extraction limits in warning metadata.
