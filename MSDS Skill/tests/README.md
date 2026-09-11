# Current regression tests

The package contains only current template baselines, source-reading fixtures,
OpenSpec contracts and tests that exercise the active runtime. Historical
approved output documents, rollback templates, generated caches and task-local
`_task_work` generators are intentionally excluded.

## Template baseline

`template_snapshot.json` and `template_snapshot_en.json` are the only shipped
template snapshots. They are pinned to the current formal CN/EN baselines:

- `examples/template_reference.docx`
- `examples/template_reference_en.docx`

Regenerate the active snapshot only after an intentional user-approved template
replacement. A stale or substituted snapshot is a release failure.

## Source interpretation

`test_source_interpretation_contract.py` verifies complete source coverage,
stable fact provenance, explicit source-only decisions, traceability and hard
blocking for unreadable or conflicting evidence. The source fixtures under
`examples/regression_*_source.docx` are test inputs only; their product facts
must never be copied into another product.

## Release behavior

Run the applicable tests with the bundled Python runtime after loading
`python-docx`. The production entry point is `scripts/build_eight.py`; frozen
task-local generators are not production inputs.

- `test_numbering_policy.py`: verifies gaps created by omission are detected and surviving items are renumbered continuously.

- `test_company_profile_policy.py`: validates Guocai profile literals, output naming, footer construction, and company-identity leakage checks.
