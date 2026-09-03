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
- child-table headers, column order and page-number fields;
- header/footer structure and dynamic page-number fields.

The first physical cell of a normal field row is treated as the sequence/label
cell. In structured rows, the sublabel cell retains the template's formatting;
only its approved source-grounded subvalue may be written.

## Writable regions

Only the following operations are permitted:

1. Write source-grounded facts into existing value cells.
2. Maintain fixed semantic note slots without changing their position.
3. Write S3 data rows as exactly three values: chemical name, CAS number and
   concentration. Every component occupies one physical row.
4. Write S8.2 data rows without changing its five-column header or topology.
5. Insert a source-provided GHS pictogram into the existing pictogram value slot.
6. Remove a complete dedicated S2/S9 row only when its value is a pure missing
   data sentinel. After that operation, change only the numeric sequence prefix.
7. Apply an approved semantic alias to an existing endpoint. For example,
   `主要粘膜刺激性` maps to `11.3 主要眼睛刺激性`; the source value itself is
   preserved and no additional conclusion is generated.

## Forbidden operations

The generator must fail if it attempts to:

- write a normal row through the label/sequence cell;
- rebuild label paragraphs/runs or globally normalize locked-cell formatting;
- change table geometry, merges, widths, borders, row heights or page fields;
- add fields for missing data or turn source examples into product facts;
- move the mucous-membrane result into `11.10 附加信息` after it has been
  classified into `11.3`;
- add species, method, classification, assessment or similar-product language
  not present in the verified source.

`scripts/template_mutation_whitelist.py` is the single write boundary. The
release audit compares the output's locked-cell XML properties and label bodies
with the fresh-cloned template. S2/S9 row omission is allowed only as an
explicit whole-row exception; no arbitrary row deletion is accepted.
