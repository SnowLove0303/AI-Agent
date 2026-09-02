# Section Mapping Rules

## General
Map by meaning, not by source row number or visual position. Preserve source qualifiers and uncertainty.

After unsupported/missing-data items are removed, renumber surviving numbered items **within each section** continuously in visible order. Change only the numeric prefix; preserve label wording and formatting. Unnumbered children do not consume numbers.

## Section 1 — Identification
Use the current Guanzhi identity-placement contract:
- header/title product-code position = source product model/code;
- `1.1 产品名称：` value = blank (do not write the model/code here);
- `中文名称：` value = `source Chinese product name + one ASCII space + source model/code`;
- classification, recommended use/restriction and supplier details map normally;
- footer/MSDS identifier uses the correct model according to template convention.

Example: source model `EP-1704`, Chinese name `水性环氧乳液` => final `中文名称` value `水性环氧乳液 EP-1704`, while the `产品名称` value remains blank. This must be checked automatically before release.

## Section 2 — Hazard identification
Only source-supported classification/label elements. Never inherit template GHS category, pictogram, signal word, H/P statement or environmental claim from a sample product.

Missing-data suppression applies before writing: if a Section 2 field contains only “无数据/无适用资料/暂无数据/无可用数据”等, omit the whole template item. Do not display those placeholders.

### Multi-H / Multi-P formatting
- Hazard statements (`Hxxx`, `EUHxxx`): one complete coded statement per line when multiple statements exist.
- Precautionary statements (`Pxxx`, `Pxxx+Pxxx...`): one complete coded statement per line when multiple statements exist.
- Keep a code and its full Chinese statement on the same logical line; only natural Word wrapping may split it visually.
- Preserve source order.
- Preserve source group headings such as “预防措施：”“事故响应：”“安全储存：”“废弃处置：” on a separate line when present.
- Never concatenate multiple H/P statements into one long paragraph.
- Perform parent `2.x` continuous renumbering after omission. H/P statement lines do not consume additional `2.x` numbers.
- Never insert arbitrary breaks inside a statement for visual alignment.
- Prefer semantic line breaks within the existing destination paragraph when this best preserves template geometry; separate value paragraphs are also acceptable if paragraph spacing is zero and the label/layout remains untouched.

## Section 3 — Composition
Use source chemical names, CAS and ranges exactly. Preserve “商业机密/N/A” when source says so. Do not infer a hidden ingredient.

## Sections 4–7
Map by function. Remove extraction line-wrap artifacts. Keep prose compact. Do not add new safety advice from template sample values.

## Section 8 — Exposure controls/PPE
High-risk fixed structure.
- Source headings such as “控制参数”“暴露控制” are semantic context, not template labels.
- Map respiratory protection -> existing respiratory label.
- Map hand/glove information -> existing hand/glove labels.
- Map eye/face -> existing eye label.
- Map body protection -> existing body label.
- If the source has exposure-limit text but the template has no safe corresponding item, omit it rather than relabeling “工程控制”.
- Never generate composite labels like `8.2 暴露控制 / 呼吸系统防护：`.

## Section 9 — Physical/chemical properties
Map property by property. **Properties whose source value is only a missing-data placeholder must disappear as whole dedicated rows before write.** Do not leave a blank visual slot. Then renumber the surviving visible Section 9 properties continuously in their original semantic order; change only the numeric prefix. Preserve substantive values such as `不适用` / `Not applicable`, measured values and source-supported `其他信息` / `Other information`. Existing “其他信息” may compactly hold source-only technical parameters such as MFFT/Tg/hydroxyl content when semantically appropriate.

## Section 10 — Stability/reactivity
Map only equivalent concepts. If source lacks “应避免条件/禁配物”, those items disappear rather than showing empty values.

## Section 11 — Toxicology
Highest-risk section.
- Preserve template endpoint labels and ordering.
- Map oral/dermal/inhalation acute toxicity separately.
- Map skin irritation, eye/mucosal irritation, sensitization, mutagenicity, carcinogenicity, reproductive toxicity, STOT and aspiration only when source supports each endpoint.
- Preserve “类似产品的风险评估数据” as a qualifier; do not convert it into direct product-test evidence.
- Unsupported endpoints disappear.
- **Section-level availability statement exception:** if the source states a complete product-level sentence such as `该产品无可用的毒理学研究。`, preserve that sentence beneath the Section 11 heading even when all endpoint rows are unsupported. Keep it unnumbered; do not map it into an endpoint and do not invent toxicology conclusions. A bare placeholder such as `无数据` is still omitted.
- A short value such as `无刺激` must be a compact single content paragraph with no hidden blank paragraphs below it.

## Section 12 — Ecology
Map ecotoxicity, persistence/degradability and other adverse effects independently. Remove hidden blank paragraphs after short values.

## Section 13 — Disposal
Keep continuous prose compact. Do not make every sentence a separate paragraph unless the source/template explicitly requires it.

## Section 14 — Transport
Map road/rail, sea, air and special precautions independently. Do not force temperature/food/acid/base precautions into separate manual lines; natural wrapping is preferred.

## Sections 15–16
Do not silently modernize or substitute regulations/disclaimer text. Follow explicit user/company policy. If none exists, source-only factual scope applies.


## Section 1 company-profile overlay (v2.6)
After source mapping and product-identity placement, apply a company-profile overlay. For `CN_国彩`, set exactly:
- 供应商名称：英德市国彩精细化工有限公司
- 供应商地址：广东省英德市白沙镇太平村更古坑凯迪工业园区
- 电话：86-763-2811205
- 传真：86-763-2811024
- footer company name：英德市国彩精细化工有限公司
No other section or product value may change solely because the company variant changes.
