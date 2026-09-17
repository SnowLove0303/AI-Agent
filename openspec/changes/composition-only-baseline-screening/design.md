# Design

## Routing

`--standards auto` selects the fixed composition baseline from the SQLite catalog. Selection ignores `target_market`, `final_use`, `environment`, `substrates`, and `special_requirements`; those fields remain available as facts but cannot exclude a baseline substance screen. The prior condition-driven selector remains available to callers that explicitly use it or pass an explicit standard list.

## Evidence boundary

The evaluator consumes names, CAS/EC identifiers, concentrations, and measurements supplied in MSDS/TDS-derived facts. It does not validate the MSDS itself, packaging, articles, homogeneous materials, migration, or final use. Missing substances remain absent under strict closed-world mode.

## Source status

The current local source package has structured rows for REACH SVHC, Annex XVII, RoHS, HSF 001, BSBL, and the Annex XVII-linked 91/338/EC entry. REACH Annex XIV and EU POPs are registered with official reference sources as baseline trigger screens; when no structured local rows exist, the report exposes `catalog-only` source status and does not ask the user for another report. This preserves the user-provided information boundary while making the data-coverage limitation visible.

## PDF

The existing mandatory PDF writer labels the run as `composition-only`, lists the baseline selection separately from later condition-driven screening, and shows source status alongside each result.
