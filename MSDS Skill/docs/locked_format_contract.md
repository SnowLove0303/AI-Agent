# Locked Format Contract

## Immutable objects
For every surviving bold label, preserve the original template object rather than recreating it.

Preserve:
- exact text/numbering/punctuation;
- `w:rPr` (fonts, East Asia font, size, bold, color, underline, spacing, language, etc.);
- `w:pPr` (alignment, indents, tabs, line spacing, before/after spacing, keep rules);
- label cell `w:tcPr` (width, margins, vertical alignment, borders, merge state);
- table grid and neighboring cell geometry;
- row layout unless the complete item is intentionally omitted.

## Allowed
- edit non-bold value content;
- omit unsupported complete items;
- update supported header/footer metadata while preserving presentation;
- remove non-semantic whitespace artifacts from value areas;
- normalize non-bold value character formatting to approved exemplar.

## Forbidden
- relabel/renumber/reorder surviving labels;
- merge two labels into one;
- split a label into newly created runs merely to reproduce appearance;
- use spaces/tabs to imitate alignment;
- copy body paragraph formatting onto labels;
- globally normalize table/paragraph formatting.

## Important distinction
“Do not change template format” does **not** mean every sample row must remain visible. The approved policy is: unsupported items disappear, while every surviving item's label/layout remains template-authentic.


## Controlled exception: continuous renumbering
The label's numeric prefix (`N.x`) is not immutable after omission. Once display decisions are final, it may be replaced solely to make surviving numbered items continuous within that section. All characters after the numeric prefix and all run/paragraph/cell formatting remain locked. No other label rewrite is permitted.
