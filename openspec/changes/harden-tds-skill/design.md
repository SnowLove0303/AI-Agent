# Design

## Context

The current TDS pipeline already clones each active template and performs source-fidelity checks, but the checks are distributed across overwrite and audit code. The optimization keeps the existing template-driven pipeline and places the missing gates in shared primitives plus one standalone preflight linter.

## Goals / Non-Goals

**Goals:**

- Fail before PDF conversion when template identity, company assets, inherited body layout, or source evidence is invalid.
- Preserve active template binaries and all approved paragraph/run formatting.
- Make locked-output failures recoverable without silently reporting success.

**Non-Goals:**

- Redesigning any DOC/DOCX template, fonts, margins, table geometry, or company branding.
- Adding an independent PDF renderer or semantic machine translation system.
- Copying product outputs into the skill source tree.

## Decisions

- Use the existing registry SHA-256 values as the template identity authority; do not infer the active template from a previous output.
- Store company-specific media and header-indent expectations beside each variant in the registry, then validate both the pristine template and generated package behavior through the same contract.
- Implement the linter as a small standalone script and invoke it from the existing DOCX audit path, so direct linter use and normal CLI builds share checks.
- Preserve body line and line-rule XML during vertical budgeting. Only registered before/after spacing may be adjusted for English overflow.
- Centralize atomic replacement in `tds_common.replace_or_retain`; both DOCX assembly and PDF conversion use it, avoiding two lock-handling implementations.
- Use exact source clauses for section-isolation detection. This is intentionally conservative and avoids a translation or NLP dependency; professional translation remains an Agent judgment recorded in the mapping.

## Risks / Trade-offs

- [Risk] Existing historical mappings may lack normalized-model source evidence. → The new cross-section guard is inert for legacy mappings, while the existing source-fidelity gate remains unchanged.
- [Risk] A locked target leaves a sibling `.pending` file requiring manual replacement. → The command fails with the exact retained path instead of claiming delivery or destroying the baseline.
- [Risk] A template's intentional company asset change requires a registry update. → SHA and asset-contract changes remain explicit and reviewable; binaries are not silently accepted.

## Migration Plan

1. Run the existing TDS test suite and the strict OpenSpec validation.
2. Build the `1.3.25` package from `manifest.txt` and verify its version, entry count, and absence of MSDS files.
3. If a target is locked in production, use the reported `.pending` file after review; no rollback migration is needed for unlocked outputs.
