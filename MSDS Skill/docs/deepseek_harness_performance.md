# DeepSeek Harness performance runbook

## V3.26 efficiency path

The optimized overwrite path preserves the business sequence:

`full source extraction -> constrained information normalization -> fixed
structure template overwrite -> post-overwrite fine-tuning`.

The main runtime improvement is reuse of deterministic mechanical work and
one in-memory read-only audit index per staged DOCX. It does not merge or
remove release gates. The formal output remains four audited DOCX plus four
PDFs, and each PDF is converted only from its saved final DOCX.

The matrix report now separates measured machine time from optional external
review/wait time. For example, a Harness may supply
`--agent-review-seconds 120` and `--human-wait-seconds 30`; omitted values are
reported as `not-supplied`, not guessed. `--retry-count` records retry state
without changing the gate result. These are measurements, not an SLA.

For a non-publishing comparison, use:

```text
python scripts/benchmark_efficiency.py --source SRC.docx --facts MODEL.json \
  --docx-only --worker-counts 1,2,3 --runs 2
```

Remove `--docx-only` to include WPS PDF conversion. The benchmark creates its
own temporary cache and matrix roots and deletes them at exit; it never writes
the requested formal `OUT` directory. If WPS is unavailable or unstable, the
failure is recorded in the benchmark report rather than hidden by a fallback
converter.

## What changed in 3.25.0

V3.25 closes the remaining source/template leakage and slow-run failure modes:

- `source_grounding.py` rechecks every non-empty semantic output against the
  original source, reviewed traceability or an approved overlay, and records
  the evidence in `OUT/MODEL/matrix-report.json`.
- The final matrix is isolated at `OUT/MODEL/WORD` and `OUT/MODEL/PDF`; only
  those directories are formal output. This prevents stale or concurrent model
  files from colliding in one flat output directory.
- The WPS adapter owns and reaps its converter process after a timeout before
  temporary files are removed, bounding the WinError 32/office-hang path.
- S15/S16 one-cell rows, Section 2 label-elements semantics, Section 11
  aliases and the S11.4 short-row exception are explicitly audited.

## What changed in 3.24.0

V3.24 makes the business flow explicit:

1. **Full source extraction:** inventory all source paragraphs, tables,
   nested tables and images and bind the evidence to the original source hash.
2. **Constrained information normalization:** review semantic mapping,
   omission/取舍, derivations and CN/EN traceability before touching a DOCX.
3. **Fixed-structure template overwrite:** clone the pinned template, resolve
   the complete S1-S16 semantic write plan, then write only approved value
   cells. S11/S12 alignment and S9/S15 capacity are decided before XML rows
   move.
4. **Post-overwrite fine-tuning:** suppress empty/unsupported rows, insert only
   authorized source-backed styled rows and repair visible numeric prefixes;
   then run every release gate.

`matrix-report.json` now records low-overhead stage events and aggregate
durations. The diagnostics include expected/actual/diff/hint information for
locked-format failures, so a Harness can repair the actual mismatch instead of
repeating a blind full run. These controls are observability and planning
improvements; they do not skip final QA or authorize label/format changes.

## What changed in 3.22.0

The Section 2 semantic boundary is now enforced before template cloning. Source
`2.2 标签要素` is treated as the label-ingredient explanation and maps to the
template `2.3 GHS标签要素` value cell. The template `2.4 信号词` value is
restricted to the controlled source vocabulary `危险` / `警告` or `Danger` /
`Warning`, `无信号词` / `No signal word`, `无` / `None`, or `Not applicable`.
A label-ingredient explanation or unresolved free text in the signal-word slot
blocks the run with an actionable error instead of producing a plausible but
incorrect MSDS.

## What changed in 3.21.0

The source/evidence stage is now resumable. `prepare_evidence_packet.py`
extracts a source once into a hash-bound packet containing source coverage,
fact-ledger entries and the review queue. Legacy Word conversion results are
also persisted under `.msds_cache` and invalidated automatically when source
bytes or the adapter contract changes. The packet is never approved by
itself; it remains `needs-review` until the Agent completes the OpenSpec
review.

Use the non-mutating preflight before the production command:

```text
python scripts/build_eight.py --source SRC.docx --facts MODEL.json \
  --model MODEL --preflight-only --preflight-report OUT/preflight.json
```

It reports all facts/OpenSpec blockers in one pass and does not clone a
template, resolve WPS or start PDF conversion. Fix the complete list, rerun
until `PREFLIGHT_PASS`, then run the production build once.

The resumable execution order is:

```text
prepare_evidence_packet -> complete source mapping/traceability review
-> build_eight --preflight-only -> build_eight production matrix
```

Use `--cache-dir OUT/.msds_cache` when the output workspace is not the desired
cache owner. The evidence command reports `EVIDENCE_PACKET_READY` or
`EVIDENCE_PACKET_REUSED`; the production matrix records the prepared adapter
and cache root in its timing evidence. A packet remains `needs-review` with
`build_allowed: false` and cannot be supplied as the approved facts JSON.

## What changed in 3.20.0

The former matrix loop completed one language/company DOCX, converted its PDF,
and only then moved to the next variant. WPS discovery and version probing also
repeated for every PDF. A slow or unavailable office process therefore made a
20-minute run look as if no MSDS had been produced, even when earlier DOCX
work was already complete.

The maintained path now has three observable phases:

1. Validate the selected source, the reviewed facts model, the OpenSpec/source
   evidence records and both locked templates once.
2. Build and audit all four DOCX masters first. These are the authoritative
   semantic/layout masters. An optional preview directory exposes these files
   before PDF conversion, but it is not a release directory.
3. Resolve and version-check WPS once, then convert the four final DOCX files
   as a bounded PDF batch. The final matrix is promoted only after all eight
   files and all release gates pass.

The scheduling change does not relax any gate and does not permit template,
label, sequence, bold-format, geometry or source-evidence changes.

## Recommended command

```text
python scripts/build_eight.py --source SRC.docx --facts MODEL.json --out OUT \
  --pdf-workers 2 --progress-file OUT/matrix-progress.json \
  --docx-preview-dir OUT/_docx_preview --cache-dir OUT/.msds_cache \
  --agent-review-seconds REVIEW_SECONDS
```

The Harness should call this once per reviewed facts model. It should not ask
the Agent to create four independent documents or render pages after each
field edit.

## Runtime controls

- `--pdf-workers 2`: default bounded parallel conversion. Use `1` if the WPS
  host serializes office processes or shows instability. Keep the bound small;
  more workers do not repair a missing converter.
- `--wpscli PATH`: explicit WPS CLI path when automatic discovery is not
  reliable in the Harness environment.
- `--progress-file PATH`: atomically updated JSON file containing the latest
  phase, variant and timing event. Standard output also emits each event as a
  line beginning with `MSDS_PROGRESS `.
- `--docx-preview-dir DIR`: copies the four individually audited DOCX masters
  after DOCX completion and before PDF conversion. Choose a directory such as
  `OUT/_docx_preview`; this directory is excluded from source discovery.
- `--cache-dir DIR`: persistent source/evidence cache root. If omitted, the
  runtime uses `OUT/.msds_cache`; every legacy conversion and evidence packet
  remains bound to source bytes and active adapter/schema contracts.
- `--agent-review-seconds S` and `--human-wait-seconds S`: optional externally
  supplied durations written only to telemetry. They do not alter semantic
  facts, output values or release decisions.
- `--retry-count N`: optional Harness retry count for telemetry. Retries never
  downgrade a failed gate.
- Final output is not flat: after all gates pass, DOCX files are promoted to
  `OUT/MODEL/WORD` and PDFs to `OUT/MODEL/PDF`. The matrix report is written to
  `OUT/MODEL/matrix-report.json`.
- `--no-pdf`: diagnostic DOCX-only mode. It is useful for isolating semantic
  or template work, but it is not an eight-file release.

The release audit also short-circuits its DOCX text scan when recursive matrix
discovery already finds a missing or duplicate slot. Keep only one canonical
copy of each of the eight final files under the package root; stale `WORD/`,
`PDF/` or copied deployment subtrees will fail immediately with the duplicate
slot error instead of consuming minutes in a redundant scan.

The cache and fast checkpoints reduce repeated mechanical work only. They do
not approve facts, skip source mapping, or replace the final semantic,
template, geometry, whitespace, lineage, PDF and render gates.

## Failure interpretation

If no progress event is reached, inspect source/facts/OpenSpec validation. If
the last event is `pdf_preflight_started`, check WPS login/session state and
the preflight error text. If `docx_ready` events appear, DOCX construction is
working and the preview directory can be inspected. If the run reaches
`pdf_converter_ready` but stops during `pdf_batch_started`, lower
`--pdf-workers` to `1` and inspect the converter's own error output.

LibreOffice, `soffice.exe`, ReportLab and PDF-only authoring are intentionally
not bundled or used as fallbacks. A missing WPS converter must fail clearly;
it must never be hidden by an unapproved alternate PDF path.

## Quality boundary

The performance profile only changes scheduling, caching and observability.
The Agent still must complete the full source-coverage/fact-ledger/mapping/
traceability read and review contract before cloning a template. The runtime
still allows only source-grounded value-cell writes, empty-value hide/show
decisions and the explicitly permitted complete styled-row insertions or
deletions. Formal output remains exactly four DOCX plus four corresponding
PDFs, with no promotion if any semantic, format, geometry, lineage or render
gate fails.
