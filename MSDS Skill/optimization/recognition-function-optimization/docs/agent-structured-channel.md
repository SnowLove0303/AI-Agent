# Agent structured recognition channel

Schema version: `agent-recognition-v1`

The channel converts one benchmark item’s `recognition.json` and
`comparison.json` into a source-grounded Agent record. It preserves raw evidence
paths and emits:

- `source`: original name/type/SHA-256/path;
- `quality`: overall status, dimension statuses, warnings, section/table/image counts;
- `sections`: keys `0` through `16` plus `unclassified` when section routing is not explicit;
- `tables`: stable table/row/cell IDs, coordinates, merge spans, raw and normalized text, formatting and segments;
- `images`: stable IDs, image SHA-256, byte size, search metadata and source locator;
- `indexes`: table and segment lookup maps for Agent consumers.

Run the converter after a benchmark:

```powershell
python scripts/agent_structured_output.py `
  --workspace OUT `
  --output OUT/agent-structured
```

`COMPLETE` is reserved for records with no warnings and passing required
content/structure/image/package dimensions. PDF/DOC/render limitations remain
explicitly `PARTIAL`, `BLOCKED`, or `UNAVAILABLE`.
