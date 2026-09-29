# Design

## Context

The structured view uses one inline text widget per source cell. Its default width and the source-grid-independent row sizing caused tables to grow beyond their source geometry and left extra vertical space.

## Goals / Non-Goals

**Goals:** Base column widths on source grid measurements and resize cell text widgets after wrapping is calculated.

**Non-Goals:** Recreate Word's full layout engine or change native page rendering.

## Decisions

- Convert source grid widths from twips to screen pixels and clamp each column to a readable range. Keep columns fixed-size so short tables do not fill the entire viewport.
- Give text widgets a minimal requested width; after layout, use Tk's display-line count to set their height. Account for the extra height needed by embedded images.
- Let the grid derive each row height from its tallest cell. This follows wrapped text and merged-cell content without a fixed table-wide row height.

## Risks / Trade-offs

- [Tk wrapping can differ from Word] → The native rendered page remains available for exact layout comparison.
- [Very wide source tables may exceed the viewport] → Retain horizontal scrolling for wide tables.
