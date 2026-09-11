# OpenSpec: MSDS Source Interpretation and Traceability Contract

Status: `ACTIVE`
Spec ID: `MSDS-SOURCE-INTERPRETATION-001`
Version: `1.1.0`

This contract prevents the Agent from treating an incomplete extraction or a
semantic guess as an approved MSDS fact model. It is an evidence gate between
source reading and template overwriting. It complements, and does not replace,
the locked-template and value-cell-only contract in
`agent_overwrite_contract.md`.

## Mandatory intermediate records

An approved facts JSON must contain all four records below:

1. `source_coverage`: the source inventory and reading-completeness result;
2. `fact_ledger`: one stable-ID record for every extracted source fact;
3. `source_mapping`: a reviewed disposition for every fact and every S1-S16
   section;
4. `output_traceability`: a reviewed record connecting every written value or
   hidden row to its source fact, approved derivation, or explicit absence
   decision.

The build is blocked before a template is cloned when any record is absent,
stale, incomplete or inconsistent with the original source hash.

## Source coverage gate

The source reader must inventory every relevant source unit. A source unit is a
non-empty paragraph/line in a table cell, a non-empty source paragraph, an
embedded image region, or another supported source object. Each unit has a
stable `unit_id`, source locator, raw text or image name, and a processing
status.

`source_coverage.status` may be `ready` only when:

- the original source SHA-256 matches the selected source;
- every discovered source unit has been extracted or explicitly marked as a
  reviewed structural unit;
- `unmapped` and `unreadable` are empty;
- every detected image/scan/table continuation has a review result;
- the reported counts agree with the installed unit list.

Nested tables are source units, not formatting noise. The reader must recurse
through every table cell and inventory each nested table, its header cells and
its data cells. A nested four-column control-parameter table in Section 8.2
must be represented as complete records in `s8_control_parameters` before the
source can be marked ready. Reading only `cell.text` from the outer table is
not a complete read and cannot be used to justify an omitted engineering-
control block. The coverage ledger should report both
`nested_table_count` and `nested_source_unit_count`; these counts must agree
with the nested source units whose IDs begin with `SRC-NESTED-`.

`source_absent` means the source was read and the field was not present. It is
not interchangeable with `source_unreadable`, `unmapped` or `mapping_ambiguous`.
The latter states block the build; they must never be converted silently into
an empty output row.

## Fact ledger and evidence rules

Each fact must preserve:

- a unique `fact_id`;
- the original source section and precise locator;
- the relevant source text, including units, ranges, qualifiers, negatives and
  meaningful line boundaries;
- the normalized value that will be used by the semantic model, without
  dropping factual qualifiers;
- one or more `source_unit_ids`;
- an `evidence_type` of `explicit`, `derived` or `translated`;
- a pending or reviewed mapping status; and
- the semantic `line_break_policy` that will be used when the value is
  rendered inside the existing value cell.

The Agent must extract first and classify second. It must not write a template
value directly from a paragraph-level impression. For a derived value, the
record must identify the source facts and the approved transformation. A
translated value must point to the same normalized source fact; translation is
not new evidence.

The following facts may not be invented: CAS/EC numbers, concentrations, GHS
classes, H/EUH/P codes, toxicology/ecology results, exposure limits, transport
classifications, regulatory conclusions, company legal names or unsupported
test methods/species/qualifiers.

Structured endpoints require skeleton alignment before rendering. Section 11
must be aligned to the maintained physical rows by endpoint and locked
sublabel, including the separate oral/inhalation/dermal rows under 11.1 and
the fertility/teratogenicity/in-vitro-genotoxicity rows under 11.7. A compacted
source list must never be written by physical list position. The middle cell
in these three-column rows is a template sublabel, not a value; it must not be
cleared, counted as source evidence or replaced by an acute-toxicity result.
An absent route is an absent value for that route and its complete row may be
suppressed only after semantic alignment and merge-safe row handling.

Section 9 `NCO含量` / `NCO content` is an independent physical/chemical
property. If it occurs inline in `其他信息`, it must be split into its own
source-backed fact and dedicated property row before mapping. It may not be
buried in generic other information or discarded during normalization.

## Mapping and取舍 rules

Every fact must be disposed as exactly one of:

- `mapped`: a registered semantic target section and target slot are approved;
- `omitted`: deliberately excluded with a reason;
- `not_applicable`: excluded by a documented field rule with a reason;
- `source_only`: present in the source but not represented by the formal
  template, with a reason and no invented substitute;
- `duplicate`: the same fact is already represented by a canonical fact ID;
- `conflict`: contradictory source evidence, which blocks until resolved;
- `unresolved`: insufficient evidence or ambiguous classification, which blocks.

取舍 means choosing the correct supported representation in the fixed template;
it does not mean making an unsupported fact disappear. If the source contains
more information than the template field can hold, preserve the factual
meaning in the registered value cell using semantic lines or an allowed
source-backed row. Do not compress unrelated facts into one line merely to fit.

If the source contains less information than the template, clear or hide only
the permitted value row according to the existing omission policy. Do not fill
the gap with a generic placeholder unless the section-specific contract
requires that exact placeholder.

## Output traceability and line breaks

Every populated output target must have an `output_traceability` item with:

- `target_section` and `target_slot`;
- `decision: written` or `merged`;
- one or more source `fact_id` values, or an approved derivation record;
- the reviewed CN and EN output values in `output_values`;
- a line-break policy such as `preserve_logical_lines`,
  `structured_field_lines` or `transport_field_lines`.

Every hidden/cleared target must have a traceability item with:

- `decision: hidden` or `not_written`;
- `reason`;
- a source-absence, explicit-missing, unsupported or not-applicable status.

Line breaks are semantic. Keep field/value pairs together, keep structured
study fields together, keep transport fields on separate logical lines, and
use Word line breaks within the existing paragraph/value cell. Do not use blank
paragraphs, tabs, repeated spaces or slash-only lines as layout devices.

## Release decision

The only acceptable path is:

`source coverage ready -> fact ledger complete -> mapping reviewed ->
ambiguity/conflict gate clear -> output traceability reviewed -> template
clone -> value-cell overwrite -> locked-format and render audits`.

Any failed source interpretation gate blocks the entire matrix. The Agent may
ask for review or report the exact evidence gap; it may not compensate by
rewriting labels, changing the template structure, guessing a field, or
delivering a partially interpreted document.
