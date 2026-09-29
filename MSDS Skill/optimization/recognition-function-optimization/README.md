# Recognition Function Optimization

This folder contains the reusable programs, tests, manifests, reports, and
replay instructions for the MSDS GUI recognition optimization.

The source corpus is intentionally not included. All evidence references the
read-only corpus root and its SHA-256 manifest.

## Layout

- `programs/` — packaged copies of the batch benchmark and maintained reader.
- `tests/` — focused recognition/hash/VML-image regression tests.
- `schema/` — versioned Agent import schema.
- `examples/` — representative structured Agent record.
- `manifests/` — corpus, environment, sample and regression-ledger evidence.
- `reports/` — smoke analysis and the provisioned mixed-format benchmark.
- `docs/` — replay and maintenance instructions.

## Current environment

- Python 3.12.10
- `pdfplumber` 0.11.10
- `pywin32` 312
- `pypdfium2` 5.13.0
- Word COM 14.0 available
- WPS COM 14.0 available

Native Word/WPS rendering passes for the DOCX smoke sample. Some legacy DOC
files can still fail native PDF export even when their content conversion
passes; those files remain explicitly blocked in the report.

## Replay

From the `MSDS Skill` directory:

```powershell
python scripts/recognition_benchmark.py `
  --source-root "F:\MSDS覆写\MSDS\TDS MSDS (2)" `
  --workspace OUT `
  --seed 20260929 `
  --sample-size 30 `
  --extensions docx,doc,pdf `
  --timeout-seconds 180
```

To replay one explicitly selected MSDS while keeping the same evidence format:

```powershell
python scripts/recognition_benchmark.py `
  --source "F:\MSDS覆写\MSDS\TDS MSDS (2)\path\to\sample.docx" `
  --workspace OUT `
  --seed 20260929 `
  --extensions docx
```

Use `--dry-run` to regenerate only a deterministic sample manifest. Never use
the corpus directory as `--workspace`.

After a benchmark, emit Agent records with:

```powershell
python scripts/agent_structured_output.py `
  --workspace OUT `
  --output OUT/agent-structured
```

The structured converter takes the original SHA-256 and path from the benchmark
sample manifest, so `source.sha256` is the actual input-file digest rather than
a hash of the filename or recognition JSON. The `agent-recognition-v1` schema
preserves Section 0–16 records, stable
table/cell/segment/image locators, raw evidence references, hashes, warnings,
and completeness status. A 100-item structured import manifest is included in
`manifests/agent-import-manifest-100.json`.

## Verification boundary

The benchmark proves recognition evidence and regressions. It does not claim a
customer MSDS/TDS eight-file release; source-grounding, template-lock and
DOCX/PDF delivery gates remain separate.
