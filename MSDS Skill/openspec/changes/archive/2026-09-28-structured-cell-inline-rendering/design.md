# Design

## Context

The parser now preserves each differently formatted run as a separate ordered segment, but the structured view creates an expanding label for every segment. See proposal.md - Why.

## Goals / Non-Goals

**Goals:** Render all text segments in one cell as inline text, apply supported run properties, and embed image segments at their original positions.

**Non-Goals:** Reimplement Word pagination or full style inheritance; the native rendered page remains the exact layout view.

## Decisions

- Use one Tk text widget per source cell. Insert text segments sequentially with tags for font family, point size, bold, italic, underline, color, and paragraph alignment. Insert each image segment as an inline Tk image at the same insertion position.
- Keep content top-aligned and estimate widget height from wrapped text lines and embedded image heights so long cells remain visible without per-run expansion.
- Remove per-row vertical expansion; rows derive their height from cell content. This avoids distributing excess height across run widgets.
- Keep source table grid, merged spans, and cell backgrounds as currently rendered. The original page tab remains the visual reference for complete Word layout.

## Risks / Trade-offs

- [Tk font metrics differ from Word and may wrap at different positions] → Keep the native page preview available for exact comparison.
- [Some Word properties have no reliable Tk equivalent] → Apply common character formatting and retain all extracted properties in the metadata tab.
