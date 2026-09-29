# Design

## Context

The existing importer returns records containing labels, section/table identifiers, rows, cells, ordered text/image segments, and native-preview page mappings.

## Goals / Non-Goals

**Goals:** Preserve every value returned by the importer in the Markdown output, including empty cells and image markers.

**Non-Goals:** Correct, infer, translate, or supplement source content that the importer did not return.

## Decisions

- Call the existing `read_file()` path and generate the report only from its returned records. This keeps the report tied to the program under test.
- Write each table row and cell explicitly and render image segments as markers in their recorded positions; do not copy or reinterpret source content separately.

## Risks / Trade-offs

- [Text-only Markdown cannot embed the original pictogram pixels] → Record the recognized image metadata and order while leaving visual appearance to the importer's native page preview.
