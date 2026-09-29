# Tasks

## 1. Runtime gates

- [x] 1.1 Add registry SHA-256, variant identity, media, and header-indent validation; verify all four active templates pass their registered contracts.
- [x] 1.2 Add cross-section source-clause leakage detection and keep Chinese source/output fidelity fail-closed; verify with a regression case for application-to-description leakage.
- [x] 1.3 Add atomic replace-or-retain handling for DOCX and PDF output; verify a simulated permission error leaves the original unchanged and writes a `.pending` file.

## 2. Layout and delivery preflight

- [x] 2.1 Add `lint_tds_docx.py` and invoke it from DOCX audit; verify body expansion inherits template layout and illegal line breaks fail.
- [x] 2.2 Stop English vertical budgeting from changing body line spacing or line rules; verify the overflow regression preserves `300/auto` body spacing.
- [x] 2.3 Update manifest, documentation, version metadata, and changelog; verify the package contains exactly the manifest entries and no MSDS paths.

## 3. Verification

- [x] 3.1 Run `pytest -q TDS Skill\\tests` and require all tests to pass.
- [x] 3.2 Run `openspec validate --all` and record the validated change set before delivery.
