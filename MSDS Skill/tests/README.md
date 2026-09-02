# Regression Test

Use the packaged PA-4817 triplet only as a regression example:
- `examples/template_reference.docx`
- `examples/nonstandard_source_PA-4817.doc`
- `examples/approved_PA-4817.docx`

Expected behavior demonstrated by the approved file:
- source-only PA-4817 facts;
- unsupported template items omitted;
- bold labels preserve template alignment/format;
- Section 8/11 are mapped without structural relabeling;
- non-bold text is consistent;
- Sections 5.4, 6.1, 11.2, 12.2, 13, 14 are compact without hidden vertical blanks.

Never copy PA-4817 product facts into another product.

## v2.1 regression additions
Run `python tests/test_section2_policy.py`.
Also use `EP-1704_policy_expectations.md` to verify:
- pure “无数据/无适用资料” fields are omitted entirely;
- multiple P statements are one complete coded statement per line;
- a single H statement is not artificially split.

## Template baseline
`template_snapshot.json` is pinned to the bundled latest `examples/template_reference.docx`. Regenerate it after any intentional template replacement; a stale snapshot is a release failure.

- `test_numbering_policy.py`: verifies gaps created by omission are detected and surviving items are renumbered continuously.

- `test_company_profile_policy.py`: validates Guocai profile literals, output naming, footer construction, and company-identity leakage checks.
