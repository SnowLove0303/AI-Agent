# Design

## Context

The DOCX parser currently extracts all cell text and images independently. The structured renderer then emits the complete text followed by every image, losing their original positions. Native page preview already preserves Word's visual layout.

## Goals / Non-Goals

**Goals:** Preserve in-cell paragraph breaks and the relative order of text and embedded images in the structured view; remove generated duplicate pictogram labels.

**Non-Goals:** Recreate Word typography in the grid view or change native page preview and search behavior.

## Decisions

- Walk each table cell's XML descendants in document order and create a short sequence of text and image segments. This reuses the existing relationship/image handling and is less complex than a separate image-positioning model.
- Render those segments sequentially in each cell. Pictograms are block widgets in the grid view; the default native page view remains the exact layout reference.

## Risks / Trade-offs

- [Inline formatting between adjacent text runs is not recreated in the grid] → Preserve the original page preview for precise formatting; this change focuses on text/image order.
