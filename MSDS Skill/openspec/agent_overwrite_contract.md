# OpenSpec: Agent-Executed MSDS Overwrite Contract

Status: `ACTIVE`
Spec ID: `MSDS-AGENT-OVERWRITE-001`
Version: `1.2.0`

This OpenSpec is the execution-layer contract for the maintained MSDS skill. It
does not replace the existing requirements documents. It makes their order and
release consequences explicit so an Agent cannot silently skip the rules and
still produce a formal output.

## Authoritative reading set

Before inspecting a source for overwrite, the Agent must read the complete
[SKILL.md](../SKILL.md) and the complete normative files listed below:

- [requirements_spec.md](../docs/requirements_spec.md)
- [locked_format_contract.md](../docs/locked_format_contract.md)
- [in_place_overwrite_contract.md](../docs/in_place_overwrite_contract.md)
- [template_mutation_whitelist.md](../docs/template_mutation_whitelist.md)
- [qa_acceptance.md](../docs/qa_acceptance.md)
- [section_mapping_rules.md](../docs/section_mapping_rules.md)
- [v2_9_inheritance_contract.md](../docs/v2_9_inheritance_contract.md)
- [source_interpretation_contract.md](source_interpretation_contract.md)
- [source_interpretation_contract.json](source_interpretation_contract.json)

The JSON version of this contract is the machine-readable checklist consumed by
`scripts/agent_execution_contract.py`.

## Agent mutation boundary

The Agent has exactly four allowed mutation intents:

1. write a source-grounded value into an existing label-associated value cell;
2. clear a value cell when the source value is absent or unsupported;
3. suppress a complete empty/unsupported dedicated row before numbering; or
4. insert a complete source-backed styled data row only for S3 components,
   S8.2 control records, S9 physical/chemical properties or S15 regulations
   when the existing template capacity is insufficient.

For a newly inserted S9 row only, the source-backed field name may seed the
new first cell while inheriting the cloned label style. This is an insertion
payload, not permission to edit an existing template label.

The Agent may not edit label text, sequence text, boldness, fonts, run or
paragraph properties, cell/table properties, borders, widths, merges, headers,
footers, page fields or global layout. It may not rebuild tables or fill an
empty value with an invented placeholder. Pictogram insertion, company/header/
footer stamping, endpoint alias routing and numeric-prefix renumbering are
deterministic runtime actions, not Agent permissions. The runtime must audit
these actions separately and still preserve the pinned template skeleton.

## Mandatory execution order

The Agent must follow this order:

1. Read the complete contract and record the required acknowledgements.
2. Inventory the complete source and verify every source unit is readable or
   explicitly reviewed as structural content.
3. Extract source facts with source locators, source-unit IDs and the original
   source hash; build the fact ledger before semantic classification.
4. Review every source-to-template field mapping and every output traceability
   record; unresolved mappings block.
5. Decide whether each candidate value is supported, explicitly missing,
   not applicable or absent.
6. Clone the pinned language-specific formal template.
7. Write only approved source-grounded values into approved value cells.
8. Hide empty/unsupported rows before numbering. Never leave a bare label row
   or a visible template example without source support.
9. Reorder the remaining visible main items in semantic order and change only
   their numeric prefixes when the omission policy requires continuity.
10. Run locked-label, bold-format, geometry, source-coverage, field-mapping,
    output-traceability and whitespace audits.
11. Render and inspect every page before release.

## Empty-value row rule

If a template label has no matching source value, the entire dedicated display
row is suppressed. The label is not rewritten, the value is not replaced with a
placeholder unless an endpoint-specific rule explicitly requires one, and the
row is not left as an empty visual line.

After suppression, surviving items retain their original semantic order. For
ordinary numbered sections, only the numeric prefix may be rewritten to close a
gap. The wording, punctuation, bold formatting, run properties, paragraph
properties, cell geometry and table structure remain template-owned.

Intentional exceptions are narrow and explicit: the maintained blank product
name value, the supplier-information parent row, the formal blank
`Recommendation` value, structural parent/header rows, and endpoint-specific
missing-data rules already defined by `requirements_spec.md`.

## Non-negotiable protections

- Sequence and label cells are not generic write targets.
- Every surviving bold label must retain its template text and bold/run/
  paragraph/cell formatting.
- A source fact must be mapped to the correct semantic field before writing;
  positional coincidence is not evidence of a correct match.
- Every extracted source fact must have a stable ID, precise source locator and
  explicit disposition. Every output value must point back to one or more
  source facts or an approved derivation. An Agent confidence statement is not
  evidence and cannot replace the ledger.
- `source_absent`, `source_unreadable`, `mapping_ambiguous` and `mapping_conflict`
  are different states. Only a reviewed source-absence/unsupported decision
  may trigger an empty-row action; unreadable, ambiguous or conflicting source
  content blocks the build.
- Preserve meaningful source line boundaries and convert them to semantic Word
  line breaks inside existing value cells. Blank paragraphs, tabs, repeated
  spaces and slash-only lines are never valid substitutes.
- Body values must use the approved template value formatting and semantic line
  breaks. Tabs, trailing spaces, empty paragraphs and fake spacing are blocked.
- Table count, grid, merges, borders, widths, row properties, headers/footers
  and page behavior are preserved from the fresh clone.
- Any failed gate is a release blocker; the Agent must not deliver a partially
  audited document.
