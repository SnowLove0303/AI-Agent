# Section Translation Rules

- S1: product identity and supplier details; translate addresses for international readability without changing factual components.
- S2: GHS terminology; coded H/P statements use canonical English wording when codes are present.
- S3: chemical names should use established English chemical nomenclature; CAS and concentration remain unchanged.
- S4: concise first-aid imperatives; avoid conversational English.
- S5: use extinguishing media, unsuitable extinguishing media, hazardous combustion products, protective equipment for firefighters.
- S6: use personal precautions, environmental precautions, methods and material for containment and cleaning up.
- S7: use precautions for safe handling and conditions for safe storage.
- S8: use exposure controls and PPE terminology; preserve EN standards.
- S9: preserve numerical values, inequality signs and units; translate property names only.
- S10: use stability/reactivity vocabulary; preserve negative conclusions.
- S11: structured toxicology parser is mandatory; punctuation-only translation is prohibited.
- S12: use ecotoxicology vocabulary and preserve OECD guideline evidence qualifiers.
- S13: professional waste/disposal wording; do not invent waste codes.
- S14: preserve transport mode and source regulatory acronyms; do not infer UN number/class/packing group.
- S15: translate listed regulations/titles conservatively; preserve Chinese standard identifiers such as GB/T and GB.
- S16: translate disclaimer faithfully without expanding legal effect.

## V3.26.2 English MSDS hard rules

- Section 1.1 `Product name` must use the reviewed professional English name
  from the approved facts layer and append the model with one ASCII space;
  never derive a name from the model or a template example.
- Section 2 health-hazard route prefixes use the maintained English forms
  `Inhalation:`, `Ingestion:`, `Skin:`, `Eyes:` and `Signs and symptoms:`.
  The prefix is locked bold Arial 12 pt; only its source-grounded description
  tail is writable regular Arial 12 pt.
- English MSDS value text must preserve approved XML value prototypes: Arial
  12 pt, no bare `cell.text`, no default `add_run()`, no 10.5 pt fallback and
  no unintended bold. The TDS EN Times New Roman 12 pt rule is recorded as an
  external follow-up because this repository contains no TDS production mapper.
