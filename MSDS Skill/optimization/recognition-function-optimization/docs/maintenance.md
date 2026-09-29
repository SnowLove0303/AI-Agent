# Maintenance and replay notes

1. Keep `manifests/corpus-manifest.json` as the source immutability baseline.
2. Reuse the recorded seed and sample manifest when comparing recognition
   fixes. A changed corpus file must be investigated before accepting results.
3. Keep raw per-item benchmark caches outside Git. Commit summaries, manifests,
   focused tests and actionable diffs only.
4. If PDF or DOC prerequisites are unavailable, preserve `BLOCKED` evidence;
   do not convert it to a partial or passing result.
5. When a fix changes `scripts/msds_table_search.py`, update the focused test,
   rerun the same smoke sample, then rerun the larger mixed sample.
