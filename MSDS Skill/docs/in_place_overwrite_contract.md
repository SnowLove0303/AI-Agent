# In-place overwrite contract

All CN/EN × Guanzhi/Guocai outputs begin as byte-level copies of the authoritative template. No blank-document generation and no table reconstruction are permitted.

Agent-allowed operations are limited to body-value insertion/clearing in
label-associated value cells, source-presence decisions, and necessary
complete styled-row insertion/deletion under the section rule. Numeric-prefix
renumbering, pictogram insertion, company overlay and header/footer model/date
fields are deterministic runtime-controlled operations, not Agent permissions.
The OpenSpec execution record and all release gates are mandatory.

V3.24 makes the business order explicit: full source extraction first,
constraint-based normalization second, fixed-template value-cell overwrite
third, and bounded post-overwrite fine-tuning (hide/insert/renumber) last.
See `openspec/efficiency_contract.md`. The semantic write plan must be
resolved before any value cells are cleared or physical rows are changed.

Forbidden operations: rebuilding tables from scratch, copying geometry from an old product output, EN-specific table redesign, collapsing endpoints into prose, adding/removing columns, changing merges to fit translation, independently deciding item presence in each variant, leaving a blank value row, or writing any value through a sequence/label cell.

Four outputs share one semantic item-presence manifest. Language affects wording only; company affects supplier fields only.
