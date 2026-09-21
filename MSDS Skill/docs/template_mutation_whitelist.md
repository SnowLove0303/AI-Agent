# Template mutation whitelist

This contract implements the “17节Section 标准骨架结构” baseline supplied in
the Feishu knowledge base. The template is a maintained document skeleton, not
a blank canvas.

## Locked regions

The following are immutable unless a separate, explicitly versioned template
baseline is adopted:

- section titles, parent structure rows and fixed labels;
- sequence and label cell formatting, paragraph properties and run properties;
- table count/order, row/column geometry, grid widths, merges, borders and row heights;
- table-cross-page permission, table layout type, repeating-header settings and each surviving row's `cantSplit` setting;
- paragraph properties and cell/table properties in every surviving writable
  value cell, not only in labels. EN non-bold body-value runs are the sole
  character-format exception: they must use one approved Times New Roman 12-point
  `w:rPr` exemplar from the active EN template; EN labels and sublabels remain
  individually locked;
- the S8.2 top-level header row (`物质 / 依据 / 类型 / 数值`; EN `Substance /
  Basis / Type / Value`), its column order and the one-cell control-parameter
  parent row. Only source-grounded S8.2 data rows are writable; the two
  template example OEL rows must be cleared per the data/placeholder rule;
- header/footer structure and dynamic page-number fields.

The first physical cell of a normal field row is treated as the sequence/label
cell. In structured rows, template-owned sublabel cells retain both their
exact text and formatting; only the final value cell may be written. This
rule applies even when a sublabel is not bold.

Section 2.8 is a composite exception to the simple “second cell is value”
shape. In the maintained two-column CN/EN templates, the second cell already
contains a template-owned route prefix (`吸入：`, `食入：`, `皮肤：`, `眼睛：`,
or `症状和体征：`; EN uses the exact maintained English equivalent). The EN
prefix is a bold Times New Roman 12 pt run. The prefix remains in its original run tree.
The runtime writes
only a value tail after a semantic line break, and clearing the slot restores
the prefix-only cell. If a separately maintained three-column S2.8 layout is
encountered, the middle route cell is locked and only the final cell is
writable.

For Section 11.1 and 11.7 three-column rows, the middle sublabel cell is
always locked template text. The runtime must align facts to the fixed Section
11 endpoint skeleton before evaluating source presence or clearing rows; a
source fact list may not be projected by physical list position. See
`scripts/section11_alignment.py`.

The physical topology is part of the same lock: Section 3 data rows remain
three physical cells, Section 8.2 data rows remain four physical cells, and
their `gridSpan`, `vMerge`, table grid and row boundaries are not editable.
Bold labels/runs are hard locks, and route prefixes or sublabels are also hard
locks because ownership is semantic, not inferred from boldness. In particular,
the EN health-hazard prefix is bold while its writable description tail is
regular Times New Roman 12 pt.

The runtime creates a slot registry from the fresh template clone before it
clears values. Non-empty value objects are writable; blank value objects remain
locked unless an explicit semantic input exception exists (for example the
product-name and emergency-overview inputs). The formal Section 8 `建议 /
Recommendation` value is an explicit source-gated input slot: a reviewed,
substantive source recommendation may be written in its non-bold value cell;
when the source is absent, the value remains blank and is recorded in the
source-presence audit rather than receiving invented text.
Global value typography is also a hard boundary: every non-empty writable
value must be non-bold. The value may inherit its template anchor's font,
size, color, language, spacing and other character properties, but direct
bold and paragraph-inherited bold must be removed or explicitly disabled on
the value run. This applies to ordinary fields, S3/S8.2 data cells, S11 final
endpoint cells, one-cell S15/S16 notes and Section 2.8 value tails. The
pre-bolded template labels, sequence cells, headers, sublabels and route
prefixes remain locked and are not value targets. In Section 15, the bold
structural headings `其它的规定：` and `符合下列法规要求：` (and their exact
English template equivalents) are also locked one-cell headings, not writable
one-cell note values. Their semantic recognition is independent of physical
row index, so approved omission of another Section 15 row can never unlock
them.

The active CN/EN baseline label text is copied exactly. Any tab or other text
present in a label in the approved template is template-owned and is not
cleaned, shortened or normalized during overwrite.

The empty-value rule is mandatory for every source-presence-controlled row:
when no source value matches a template label, suppress the complete dedicated
row before numbering. Never leave an empty value beside a surviving label.
Only the explicit blank product-name, supplier-parent, Recommendation and
structural/header slots are exempt; endpoint-specific exceptions remain those
defined in `requirements_spec.md`. A row being suppressed is not permission to
rewrite its label or formatting.

## Writable regions

Only the following operations are permitted:

1. Write source-grounded facts into existing value cells.
2. Maintain fixed semantic note slots without changing their position.
3. Write S3 data rows as exactly three values: chemical name, CAS number and
   concentration. Every component occupies one physical row.
4. Write S8.2 top-level data rows as exactly four values: substance, basis,
   type and value. If more verified records exist than the template's two
   example rows, clone the existing styled data row in place; never rebuild
   the parent table. With no verified records, remove the complete workplace-
   component block (parent, header and data rows); do not leave a template
   example or synthesize a missing-data placeholder for an absent block.
5. Suppress a complete dedicated row when its value is source-absent,
   unsupported or a pure missing-data sentinel under the section policy. The
   runtime may then renumber only numeric prefixes when that policy requires it.
6. Insert a complete source-backed styled data row only for S3 components,
   S8.2 control records, S9 properties or S15 regulations when existing
   template capacity is insufficient. For a newly inserted S9 row only, the
   source-backed field name may seed the new first cell while inheriting the
   cloned label style; this is not permission to edit any existing label.
7. In Sections 11 and 12, when no endpoint is supported, retain the source
   explanation row only. In other ordinary sections, suppress a source-absent
   template row but retain an explicitly sourced missing value.

Pictogram insertion, company/header/footer overlay, endpoint alias routing and
numeric-prefix renumbering are runtime-controlled operations, not Agent label
or formatting permissions.

## Forbidden operations

The generator must fail if it attempts to:

- write a normal row through the label/sequence cell;
- rebuild label paragraphs/runs or globally normalize locked-cell formatting;
- change paragraph formatting, label/sublabel/prefix run formatting, table geometry,
  merges, widths, borders, row heights or page fields. EN body-value run
  character formatting may change only to the single approved exemplar;
- globally normalize fonts, line spacing, paragraph spacing or indents;
- add fields for missing data or turn source examples into product facts;
- move the mucous-membrane result into `11.10 附加信息` after it has been
  classified into `11.3`;
- add species, method, classification, assessment or similar-product language
  not present in the verified source.

`scripts/template_mutation_whitelist.py` is the single write boundary. The
release audit compares locked-cell XML properties, writable-cell layout
anchors, the approved EN body-value exemplar, label bodies and the cross-page
contract with the fresh-cloned template.
The formal templates allow tables to span pages. Row-level `cantSplit` is
template-owned and may be present when supplied by the active baseline; the
audit fails when an output changes a surviving row's setting. Repeating headers
remain enabled where present. Row omission is allowed only for a dedicated
S2/S9 pure-missing item, a source-absent ordinary field, or the documented
note-only Sections 11/12 policy; no arbitrary row deletion is accepted.

## v3.25.3 semantic and layout gates

Before this mutation boundary is reached, the Section 2 fact router must have
confirmed that each non-empty value belongs to its stable semantic destination.
The emergency-overview value is explicit-source-only; it cannot be assembled
from other Section 2 hazard rows. One fact is exclusive to one target unless a
reviewed `shared` exception lists every target and its reason. This semantic
gate is independent of the locked-label audit and runs before the template is
cloned.

When S8.2 survives, its five-column grid, four logical data cells, `gridSpan`,
widths, parent/header rows and data-row properties must remain inherited from a
fresh clone. When no verified control records exist, the whole S8.2 block may be
removed together. S11.4 cell vertical alignment must also remain inherited from
the fresh clone. These output-only checks block drift; they do not modify the
formal template or perform a global formatting repair.

Section 8 PPE rows are aligned by semantic label before source-presence
suppression. The value cell is authoritative when a source label cell also
contains a tabbed or inline tail; the stale tail is retained only in review
evidence and is never copied into a neighboring label or value. An unmapped
PPE row is a blocking ambiguity. Output labels are compared with the fresh
template skeleton; only a label change relative to that baseline is blocked.
The writer never silently rewrites a template label.
