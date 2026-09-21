# Locked Format Contract

## Immutable objects
For every surviving bold label, and for every semantically template-owned
prefix or sublabel even when it is not bold, preserve the original template
object rather than recreating it.

Preserve:
- exact text/numbering/punctuation;
- `w:rPr` (fonts, East Asia font, size, bold, color, underline, spacing, language, etc.);
- `w:pPr` (alignment, indents, tabs, line spacing, before/after spacing, keep rules);
- label cell `w:tcPr` (width, margins, vertical alignment, borders, merge state);
- table grid and neighboring cell geometry;
- row layout unless the complete item is intentionally omitted.

The Section 2.8 route prefix is template-owned content inside the current
two-column value cell. CN keeps the maintained Chinese prefix; EN keeps the
maintained English equivalent as a bold Times New Roman 12 pt run. Section 11.1/11.7 middle sublabels are template-owned
content inside three-column rows. Section 3's three-cell rows and Section
8.2's four-cell rows are physical topology, not formatting suggestions.

## Allowed
- edit non-bold value content only in the declared final value cell or value
  tail;
- omit unsupported complete items;
- update supported header/footer metadata while preserving presentation;
- remove non-semantic whitespace artifacts from value areas;
- normalize non-bold value character formatting to approved exemplar.

All writable value tails are non-bold by contract. Their other character
properties inherit from the destination value anchor. Removing or explicitly
disabling bold on a value run is the only permitted character-format
exception; no writable value tail may be emitted bold even if a legacy value
placeholder or paragraph mark in the template is bold. Template-bold labels,
sequence cells, headers, sublabels and composite route prefixes remain
immutable. The bold EN route prefix is not a writable value tail.

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
