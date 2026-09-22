# Section 2 customer-facing policy

Section 2 is read by the customer as a complete hazard-label block. It must not expose internal drafting navigation.

## Label elements

When the source supplies a label ingredient, write it directly in the `GHS label elements` value cell using separate lines:

```text
必须列在标签上的有害成分：
亲水脂肪族聚异氰酸酯
```

The English equivalent is:

```text
Hazardous ingredients required to be listed on the label:
Hydrophilic aliphatic polyisocyanate
```

The source heading `2.2 标签要素` selects the maintained template's `2.3 GHS标签要素` value slot. It is not a signal-word field. Keep the label-ingredient explanation in this slot, and keep the separate `2.4 信号词` value limited to the explicit source signal word `危险` / `警告` or `Danger` / `Warning`. Never move `必须列在标签上的有害成分` or its ingredient into the signal-word slot.

The normal label-elements shape is exactly two logical lines: the attention
heading, followed by the explanation. A specific concentration limit belongs
to the explanation line and must not be emitted as a standalone third line.

When Section 2 reports no product-level classification but a reviewed Section
3 component fact contains an explicit GHS classification/H-code, route that
fact into Section 2.1. Keep every classification/H-code pair on its own line.
For known source typos, correct only when the same fact supplies the governing
H-code; for example, `依然液体` + `H226` is corrected to `易燃液体` + `H226`.
Do not run an unconstrained spell-check over MSDS values.

Do not write `见2.4-2.6`, `See 2.4-2.6`, or any other customer-facing cross-reference. Signal word, hazard statements and precautionary statements remain in their own visible rows.

Section 2.5 H/EUH statements and Section 2.6 P statements are logical-line
values: each coded statement occupies its own line, while the controlled
group heading remains a separate first-level line and detail lines use the
template's hanging indentation.

Health-hazard routing is per exposure route, never a single on/off switch.
Compare Section 2.5 H/EUH text with inhalation, ingestion, skin, eyes and
symptoms/signs independently: suppress only the route already covered by the
H/EUH text, retain every uncovered route and every additional source line from
the source Section 2.7/2.8 block, and preserve its wording. Route-labelled
first-aid lines inside Section 2.6 remain in the response group and must not be
promoted into a health-hazard row.

## Pictograms

If the source DOCX contains an embedded GHS pictogram, extract and insert the source image into the cloned template's existing GHS pictogram cell. Preserve the image as an image; do not replace it with `无数据`, `None`, alt text, or a textual description. If no image is supplied, a pictogram may be resolved only from explicit, verified GHS classifications and the resolution must be recorded in the audit; do not infer from a vague prose hazard.

## Omission and numbering

After all Section 2 values and the pictogram are written, remove a whole dedicated row when its value is only `无数据` / `No data available`, including `眼睛：无数据` / `Eyes: No data available`. Keep substantive conclusions such as `无刺激`, `不适用` and `无危险反应`. Renumber surviving unique `2.x` items in original semantic order; repeated child rows keep the same number. The pictogram row is unnumbered and remains when the image exists.

## Evidence boundary

The skill must not invent H/EUH/P codes, signal words or hazardous ingredients. The label block is populated only from verified source facts or an explicitly approved semantic payload.
