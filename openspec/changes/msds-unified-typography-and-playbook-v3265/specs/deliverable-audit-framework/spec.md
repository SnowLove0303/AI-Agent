# Specification: Value Typography and Independent Row Separation

## Value Typography Contract
- Every writable value cell MUST have font size strictly equal to 12.0 pt (`w:val="24"`).
- Normal values MUST NOT inherit bold styling from header/label cells.
- Values MUST use Arial for Latin/numbers and 宋体 for Chinese text.

## Independent Row Contract
- Product-level toxicological conclusions and component/polymer specific toxicological data MUST NOT be concatenated into the same table cell.
- They MUST be rendered in distinct independent table rows or paragraphs as governed by `independent_row_playbook.md`.
