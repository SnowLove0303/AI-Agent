## 1. Skill contract and source registry

- [x] 1.1 Create the new skill folder and write `SKILL.md` with trigger conditions, complete-facts mode, four result labels, and the PDF-report-shaped output contract; verify the frontmatter and required sections parse successfully.
- [x] 1.2 Add the external data-source registry and configurable data-root resolution; verify all six CSV families and the EU Toy directory are detected without copying data.
- [x] 1.3 Add a concise report-template reference matching the approved PU-1002 PDF sections; verify every output section is named in the template.

## 2. Judgment engine

- [x] 2.1 Implement CSV loading with UTF-8/GB18030 fallback, source metadata capture, and required-file validation; verify row counts against the inspected canonical exports.
- [x] 2.2 Implement component normalization and CAS/EC/name/group matching; verify exact, alias, group-level, and no-match cases.
- [x] 2.3 Implement closed-world applicability resolution for market, final use, environment, substrate, and special requirements; verify PU-1002 leather/plastic use excludes downstream-only scopes.
- [x] 2.4 Implement the four result labels, evidence objects, source traceability, and unidentified-standard gate; verify no complete no-match path returns `需补证`.
- [x] 2.5 Implement the report-ready JSON/Markdown matrix output and CLI options for data root, product facts, requested standards, and output path; verify the matrix preserves all requested items.

## 3. Tests and evaluation

- [x] 3.1 Add unit tests covering exact CAS match, no-match pass, group restriction, scope exclusion, limit hit, and unidentified customer code; verify the test command passes.
- [x] 3.2 Add skill evaluation prompts for a PU-1002 report, a toy-use variant, and an opaque customer standard; verify the eval file uses the skill-creator schema.
- [x] 3.3 Run the engine against PU-1002 facts and the supplied 40-item list; verify results contain 40 rows, source evidence, and no accidental second data root.

## 4. OpenSpec, review, and delivery

- [x] 4.1 Run OpenSpec validation and review the diff for scope; verify only the new skill folder and this change are staged.
- [x] 4.2 Run the full targeted test command and a clean CLI smoke test; verify the generated report matrix is readable and deterministic.
- [ ] 4.3 Commit the isolated change on the repository's current `main` line and push only the new commit to `origin/main`; verify remote HEAD equals the pushed commit and report the commit hash.
