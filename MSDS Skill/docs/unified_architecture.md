# Unified four-format architecture

## Single semantic source of truth
Never create four documents by independently editing four copies. Parse the source once into a normalized semantic model. Apply omission and section mapping before language/company rendering.

## Rendering matrix
| Language | Guanzhi | Guocai |
|---|---|---|
| CN | CN language layer + Guanzhi overlay | same CN content + Guocai overlay |
| EN | EN professional language layer + Guanzhi overlay | same EN content + Guocai overlay |

## Drift prevention
- Numbers, CAS, concentrations, OECD methods, classifications and qualifiers are immutable fact tokens across language layers.
- Company overlays execute after language rendering and may touch only whitelisted company fields.
- Section 11 structure is language-neutral and must be resolved before translation.
