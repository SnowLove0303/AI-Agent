# Safe OOXML / python-docx Editing Patterns

## Why naïve replacement fails
`paragraph.text = value` and `cell.text = value` reconstruct runs/paragraphs and can destroy bold labels, alignment, indentation, tabs, font properties and row behavior.

## Separate label/value cells
Preferred: leave label cell untouched. In the value cell, retain the existing paragraph and replace only non-bold content runs. Do not create extra paragraphs.

## Shared label/value paragraph
1. Identify locked bold run range.
2. Keep those `<w:r>` nodes untouched.
3. Replace/remove only non-bold value runs after the label.
4. If a new value run is required, clone a pre-existing value run or approved exemplar `w:rPr`; never clone the label run.

## Body exemplar
Deep-copy only `w:rPr` from the approved exemplar to value runs. Do not copy `w:pPr` globally.

## Removing unsupported items
Use the smallest safe display unit. Before removing a `<w:tr>`, confirm the row is not carrying another supported independent item and that vertical/horizontal merges will remain valid.

## Compacting
Remove trailing empty value paragraphs while keeping Word's required final cell paragraph. Remove empty non-label runs, tabs and manual breaks only when they are not semantic. Clear artificial row-height constraints only for affected content rows, not globally across the document.

## Recovery
If label XML has been altered, restore it from the untouched template or restart from the template. Do not approximate the old appearance manually.


## Section 2 semantic H/P breaks
The general ban on manual breaks is about visual alignment. Section 2 is an explicit semantic exception. If multiple H/P statements share a value cell, preserve the destination paragraph and add breaks **only between complete statements**. Apply the approved body `w:rPr` to all inserted value runs. Do not touch the bold label cell.

Recommended strategy:
- tokenize the source string by H/EUH/P statement code boundaries;
- keep optional group headings as independent logical lines;
- rebuild only the value paragraph's non-bold runs;
- use a single paragraph with `<w:br/>` between logical statements when paragraph-level styling is sensitive; or use multiple value paragraphs with zero spacing if the template safely supports them;
- never create a break because of character count or visual width.

## Missing-data suppression before OOXML write
Do not write “无数据” and then delete it in a cleanup pass. Classify it as `OMIT_MISSING_DATA` during semantic mapping. This prevents empty-value remnants, accidental row-height artifacts, and template-sample leakage.
