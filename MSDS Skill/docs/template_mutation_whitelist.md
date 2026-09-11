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
  character-format exception: they must use one approved Arial 12-point
  `w:rPr` exemplar from the active EN template; EN labels and sublabels remain
  individually locked;
- the S8.2 top-level header row (`物质 / 依据 / 类型 / 数值`; EN `Substance /
  Basis / Type / Value`), its column order and the one-cell control-parameter
  parent row. Only source-grounded S8.2 data rows are writable; the two
  template example OEL rows must be cleared per the data/placeholder rule;
- header/footer structure and dynamic page-number fields.

The first physical cell of a normal field row is treated as the sequence/label
cell. In structured rows, the sublabel cell retains the template's formatting;
only its approved source-grounded subvalue may be written.

The runtime creates a slot registry from the fresh template clone before it
clears values. Non-empty value objects are writable; blank value objects remain
locked unless an explicit semantic input exception exists (for example the
product-name and emergency-overview inputs). The formal Section 8 `建议 /
Recommendation` value is not an input slot and remains blank. A source-absent blank slot remains blank and is
recorded in the source-presence audit, rather than receiving invented text.
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
   the parent table. With no verified records, remove the second example row
   and write the exact missing-data placeholder (`无数据` / `No data
   available`) into the value column of the single remaining data row.
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
- change paragraph formatting, label/sublabel run formatting, table geometry,
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
