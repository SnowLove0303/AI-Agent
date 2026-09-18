# OpenSpec: V3.24 Efficiency and Four-Stage Overwrite Contract

Status: `ACTIVE`  
Spec ID: `MSDS-EFFICIENCY-001`  
Version: `1.0.0`

This contract makes the business workflow explicit. It optimizes repeated
source extraction, semantic planning, DOCX construction and feedback without
relaxing the locked-template or fail-closed release contract.

## Business workflow

The Agent/runtime must treat the following sequence as one ordered pipeline:

1. **全量抽取源文件信息** — inventory every readable source unit, including
   paragraphs, all tables and nested tables, images and content outside the
   numbered sections. Produce the source hash, coverage record and candidate
   fact ledger before classification. No template mutation is allowed.
2. **基于约束的信息归纳** — normalize and classify the ledger under the
   source-interpretation, section-mapping and translation rules. Review
   ambiguity, conflict, omission, derivation and CN/EN traceability. No DOCX
   mutation is allowed.
3. **基于固定结构的模板覆写** — clone the pinned CN/EN formal template,
   precompute a semantic section write plan, then write approved values through
   the value-cell boundary. Labels, sequence, bold label formatting, layout
   and geometry remain template-owned.
4. **微调（不显示/重排序等）** — after fixed writes, apply only the active
   row-level policies: suppress empty/unsupported dedicated rows, insert an
   authorized source-backed styled row when capacity is insufficient, repair
   vertical merges where required, and rewrite numeric prefixes only for
   surviving visible items. Run every release audit afterward.

The fourth stage is not permission to rewrite the template. It is a bounded
runtime operation on the clone, governed by `agent_overwrite_contract.json`.

## V3.24 target points

- **EFF-01 — full source packet reuse.** A source packet may be reused only
  when the original source bytes, source format, extractor contract and active
  OpenSpec inputs match. Nested and non-table content must already be in the
  packet; a cache hit never means “skip review.”
- **EFF-02 — semantic write planning.** Section payloads are resolved before
  value cells are cleared or rows are inserted. Section 11 is aligned by
  endpoint and locked sublabel; Section 12 note slots are aligned before
  endpoint rows; S9/S15 capacity changes are calculated before the registry is
  rebuilt. Fixed writes consume this plan, not a list whose physical indexes
  are changing underneath it.
- **EFF-03 — planned post-overwrite mutations.** Suppression, authorized
  insertion and prefix-only renumbering are represented as a post-overwrite
  policy result. Empty rows are hidden before numbering. A table is never
  reconstructed, and a blanket `w:hidden` strategy is not a production
  substitute for the maintained row policy.
- **EFF-04 — diagnostic gate diffs.** A format or skeleton blocker should say
  where it occurred, what the expected template signature was, what the output
  signature was, what differs and what the Agent should inspect. Diagnostic
  detail improves repair speed but does not alter pass/fail semantics.
- **EFF-05 — stage timing and fast feedback.** Low-overhead stage timings are
  recorded for the source/semantic/template/fine-tuning workflow and exposed
  in progress/report data. `--preflight-only`, `--no-pdf` and an audited DOCX
  preview remain available for short iteration loops. They are checkpoints,
  not release replacements.
- **EFF-06 — evidence-safe reuse.** A product fact or ontology may validate or
  suggest a candidate mapping, but it cannot fill a missing source fact. Any
  derivation must retain provenance; ambiguity and conflict remain blockers.

## Invariants and non-goals

The following are hard invariants, not optimization choices:

- The pinned formal templates are the structure, label and format authority.
- The source is the fact authority. Empty, unreadable, ambiguous and
  conflicting source states stay distinct.
- The Agent may write value cells, clear value cells, suppress complete rows,
  and insert only authorized source-backed styled data rows. It may not edit
  labels, sequence wording, boldness, run/paragraph/cell formatting, geometry,
  headers or footers.
- Final semantic, source-coverage, traceability, locked-format, whitespace,
  geometry and render gates remain blocking.
- No knowledge-base auto-fill, global template sanitizer, whole-table rebuild,
  blanket soft-hide or fixed-duration promise is introduced by V3.24.

The measurable performance baseline must be collected from comparable Harness
runs. The contract deliberately does not turn the historical report's rough
percentages into a false SLA.

## V3.26 efficiency addendum

V3.26 keeps the same four-stage order and adds bounded reuse/measurement:

- The formal CLI accepts `--cache-dir`; source-adapter cache entries are bound
  to the original source hash, format and adapter contract. A cache hit only
  avoids repeated mechanical preparation. It never approves facts or skips
  source mapping, traceability or release gates.
- A read-only `AuditContext` is constructed once per staged DOCX after save.
  Compatible locked-skeleton, value-typography, value-whitespace, empty-row
  and numbering observations may reuse it. Persisted DOCX/ZIP, terminology,
  PDF-lineage and final matrix checks remain independent saved-file gates.
- `matrix-report.json` records additive `timing.cache`, `timing.pdf`,
  `timing.time_categories`, per-variant wall times and final artifact hashes.
  Machine time is measured by the pipeline; Agent/manual review and human
  wait time are `null` unless explicitly supplied by the caller.
- WPS conversion remains bounded threaded execution, with `--pdf-workers 1`
  as the conservative serial fallback and `2` as the default. Process pools
  and resident COM/WPS sessions are not enabled by default until comparable
  stability evidence exists.
- Run `python scripts/benchmark_efficiency.py --source SRC.docx` for a
  non-publishing cold/warm evidence-cache measurement. Add `--facts MODEL.json`
  to compare DOCX-only or PDF-enabled matrix runs at worker counts `1,2,3`
  (or another explicit list). All benchmark output is temporary and is
  removed before the command returns.

The benchmark output is evidence, not a guaranteed duration or speedup. A
converter failure is reported as a failure sample and cannot be reclassified
as a successful release.
