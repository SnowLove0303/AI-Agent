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

Do not write `见2.4-2.6`, `See 2.4-2.6`, or any other customer-facing cross-reference. Signal word, hazard statements and precautionary statements remain in their own visible rows.

## Pictograms

If the source DOCX contains an embedded GHS pictogram, extract and insert the source image into the cloned template's existing GHS pictogram cell. Preserve the image as an image; do not replace it with `无数据`, `None`, alt text, or a textual description. If no image is supplied, a pictogram may be resolved only from explicit, verified GHS classifications and the resolution must be recorded in the audit; do not infer from a vague prose hazard.

## Omission and numbering

After all Section 2 values and the pictogram are written, remove a whole dedicated row when its value is only `无数据` / `No data available`, including `眼睛：无数据` / `Eyes: No data available`. Keep substantive conclusions such as `无刺激`, `不适用` and `无危险反应`. Renumber surviving unique `2.x` items in original semantic order; repeated child rows keep the same number. The pictogram row is unnumbered and remains when the image exists.

## Evidence boundary

The skill must not invent H/EUH/P codes, signal words or hazardous ingredients. The label block is populated only from verified source facts or an explicitly approved semantic payload.
