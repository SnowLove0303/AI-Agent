# Unified four-format architecture

## Single semantic source of truth
Never create four documents by independently editing four copies. Parse the source once into a normalized semantic model. Apply omission and section mapping before language/company rendering.

## V3.24 business-stage boundary

The complete workflow is ordered as:

`全量抽取源文件信息 -> 基于约束的信息归纳 -> 基于固定结构的模板覆写 -> 微调（不显示/重排序等）`

Source inventory and fact extraction finish before constrained mapping and
取舍. The fixed-template stage resolves a semantic write plan before clearing
value cells or inserting rows. Only the final fine-tuning stage may apply the
authorized empty-row suppression, source-backed styled-row insertion, merge
repair and prefix-only renumbering. The active details are maintained in
`openspec/efficiency_contract.md`.

## Rendering matrix
| Language | Guanzhi | Guocai |
|---|---|---|
| CN | CN language layer + Guanzhi overlay | same CN content + Guocai overlay |
| EN | EN professional language layer + Guanzhi overlay | same EN content + Guocai overlay |

## Drift prevention
- Numbers, CAS, concentrations, OECD methods, classifications and qualifiers are immutable fact tokens across language layers.
- Company overlays execute after language rendering and may touch only whitelisted company fields.
- Section 11 structure is language-neutral and must be resolved before translation.
