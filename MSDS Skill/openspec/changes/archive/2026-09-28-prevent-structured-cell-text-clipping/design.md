# Design

## Context

The structured table view uses Tk text widgets sized from Tk's display-line count. The existing range stopped before Tk's terminal newline and undercounted the rendered lines.

## Goals / Non-Goals

**Goals:** Include the final rendered line when computing text widget height and cover the reported Section 12 case.

**Non-Goals:** Change table extraction, source widths, typography, or native page rendering.

## Decisions

Count display lines from the start of the widget through `end`, which includes Tk's mandatory terminal newline. Retain the current image-height addition and adaptive sizing callback. Extend the existing GUI smoke check to ensure the Section 12 final text line has visible display information.

## Risks / Trade-offs

The terminal newline is part of Tk's text model; counting it provides the complete display-line count and may add one line only when the content actually occupies it. Existing short-row checks guard against excess height.
