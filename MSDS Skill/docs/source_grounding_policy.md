# V3.25 source-grounding policy

This policy closes the failure mode in which a template example is mistaken
for a product fact. The source MSDS/SDS is the only authority for product
facts. The formal template is an authority for structure, labels, sequence,
formatting and geometry only.

## Required evidence chain

Before any template clone, the Agent must complete the full source inventory,
fact ledger, reviewed source mapping and output traceability required by the
source-interpretation contract. Every non-empty output value must be one of:

1. an exact or normalized source-grounded fact;
2. a reviewed professional translation of a source-grounded fact;
3. a narrowly documented derivation that preserves the source evidence; or
4. an approved company overlay or controlled runtime value, such as the
   selected supplier profile or localized revision date.

The value's evidence must be recorded in `output_traceability`. A value that
appears only in the template, a previous output, an Agent's general
knowledge, or a guessed field mapping is unauthorized and blocks release.

`output_traceability.output_values` is not evidence by itself. A written trace
must bind `source_fact_ids` and use one of the reviewed evidence types:
`exact_source`, `approved_translation`, `approved_derivation` or
`company_overlay`. An English translation additionally requires
`translation_reviewed: true`; a derivation requires a named
`derivation_rule_id`. This is a global gate shared by all sixteen Sections,
not a Section 2-only rule.

For Chinese output, the default is source-verbatim: after removing only
template labels, field prefixes and semantic line-break changes, the value
must be locatable in the original source. Section-specific routing may move a
fact to a different template slot, but may not rewrite a correctly matched
source sentence. For English output, translation is allowed only through the
reviewed translation evidence path; a trace item cannot authorize a free
paraphrase.

## Source reading and reconciliation

Read all paragraphs, tables, nested tables, headers/footers, images and
non-numbered source content before semantic classification. Record each
candidate with a stable fact ID and precise source locator. If two source
regions disagree, or a region is unreadable, mark the candidate as conflict or
unreadable and stop the formal build until it is reviewed. Do not silently
choose the first occurrence. If a source endpoint is absent, record an
explicit reviewed absence; absence is not permission to copy the template's
example value.

`scripts/source_grounding.py` performs a second mechanical check. It verifies
ledger anchors in the original source and rejects every non-empty semantic
payload that is absent from the ledger, output traceability or an explicit
approved overlay. Its report is written to `matrix-report.json` so the final
package carries the same evidence used by the pre-clone gate.

## Controlled semantic exceptions

The non-hazard GHS fallbacks are allowed only when the original source
explicitly concludes that the product is not hazardous/not classified:

- CN signal word: `无信号词`; CN pictogram statement:
  `无危险的象形图警示性说明`.
- EN signal word: `No signal word`; EN pictogram statement:
  `No hazard pictograms or precautionary statements`.

Section 2.2 `标签要素` is label-ingredient explanation, not signal word. Keep
the complete source explanation in the template's label-elements value cell,
with meaningful line breaks. The signal-word slot may contain only the
controlled source vocabulary. Never use the label-elements explanation as a
signal word merely because both appear in Section 2.

Section 8 `建议 / Recommendation` is source-gated. Its fixed label and value
cell formatting remain locked; only a reviewed substantive recommendation may
be written into the non-bold value cell. An absent recommendation stays empty.

## Section 2 semantic routing

Section 2 is not a free-form summary area. The reviewed facts file must carry a
stable `section2_routing` record. Its default is one source fact to one semantic
target: `emergency_overview`, `ghs_classes`, `label_elements`, `signal_word`,
`hazard_statements`, `precautionary_statements`,
`physical_chemical_hazards`, `health_hazards`, `environmental_hazards` or
`other_hazards`. The visible number may change after omission, so positional
targets such as `s2.row[1]` are rejected.

The emergency overview can be populated only by an explicit source Section 2
emergency-overview fact. H/P statements, physical/chemical hazards, health
hazards and other hazards may not be summarized into 2.1. A fact reused across
different Section 2 targets requires a reviewed `shared` item, a complete
`approved_targets` list and a reason; otherwise the build fails before cloning.
The router checks the source mapping, output traceability and both language
semantic rows, so a globally similar string cannot silently move to another
field.

## Output layout preservation

The formal template remains the sole layout authority. The release audit checks
S8.2's five-column grid, four logical data cells, `gridSpan`, widths, parent and
header rows, and data-row properties. It also checks S11.4 vertical alignment
against a fresh template clone. The complete S8.2 block may be hidden only when
no verified control records exist; no partial block or global formatting repair
is allowed.

## Final mutation boundary

Source grounding does not expand Agent permissions. The Agent may write only
approved value cells, decide source-absent/unsupported hiding, and request the
necessary complete styled row insertion/deletion expressly allowed by the
section rule. Labels, sequence, boldness, three-/four-column topology, merges,
widths, borders, paragraph/run properties and page layout remain immutable.
