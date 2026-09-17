# Proposal: composition-only baseline screening

## Why

The current automatic route uses the condition sheet to decide which regulations are applicable before testing. That is the wrong first step when the available evidence is limited to MSDS/TDS composition facts. The first report should screen the important substance lists as broadly as possible; market, use, packaging, and customer information are not available or are intentionally out of scope.

## What changes

- Add a composition-only baseline route that always evaluates the core substance lists without jurisdiction, final-use, packaging, or customer filters.
- Make the baseline include REACH SVHC, REACH Annex XVII, REACH Annex XIV as an authorization trigger screen, EU POPs 2019/1021, RoHS substance screening, HSF 001, BSBL, and 91/338/EC.
- Keep the existing condition-driven route for later, explicit special-use screening; it is no longer the default for `--standards auto`.
- Mark catalog-only baseline entries clearly when the local knowledge base has no structured restriction rows. Do not turn that source limitation into a request for additional user documents.
- Update the PDF and skill instructions to describe the report as a substance-composition screen, not a document, packaging, product-category, or market-admission audit.

## Scope

In scope: baseline selection, catalog metadata, PDF/report labels, tests, and OpenSpec documentation.

Out of scope: checking MSDS formatting or correctness, packaging, finished-product migration testing, customer standards, or market-entry conclusions.
