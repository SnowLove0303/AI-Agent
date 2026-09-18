# Composition-only baseline screening

## MODIFIED Requirements

### Requirement: automatic runs prioritize substance screening

When the user does not provide an explicit standard list, the evaluator MUST run the composition baseline without filtering by market, final use, environment, substrate, packaging, or customer requirement.

#### Scenario: PU resin facts without market or use scope

- **GIVEN** complete MSDS/TDS-derived component facts and no usable market or final-use classification
- **WHEN** the CLI runs with `--standards auto`
- **THEN** the baseline substance lists are still selected and evaluated

### Requirement: baseline scope is fixed and broad

The automatic composition baseline MUST include REACH SVHC, REACH Annex XVII, REACH Annex XIV trigger screening, EU POPs 2019/1021 trigger screening, RoHS substance screening, HSF 001, BSBL, and 91/338/EC.

#### Scenario: Baseline contains all core entries

- **GIVEN** a complete component list
- **WHEN** baseline selection runs
- **THEN** every named baseline entry appears regardless of market or use fields

### Requirement: substance-only evidence boundary

The evaluator MUST use only substance identity, concentration, and supplied measurement facts for the baseline. It MUST NOT claim to have checked MSDS formatting, packaging, finished-product migration, article homogenous-material status, final use, or market admission.

#### Scenario: No document or packaging audit

- **GIVEN** an MSDS/TDS-derived facts JSON
- **WHEN** a baseline report is generated
- **THEN** the PDF states that it is a composition screen and excludes document, packaging, use, and market conclusions
