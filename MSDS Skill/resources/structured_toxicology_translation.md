# Structured Toxicology Translation Rules

## Parsing before translation
Do not split Section 11 on punctuation first. Detect endpoint and study blocks, then fields.

Example source block:
- 测试种类：沙门氏菌/微粒体试验（Ames试验）
- 代谢活化：有/无
- 结果：阴性
- 方法：OECD化学品测试指南471
- 对类似产品研究

Professional output:
- Test type: Salmonella/microsome assay (Ames test)
- Metabolic activation: With/without
- Result: Negative
- Method: OECD Test Guideline 471
- Study on a similar product.

## Field rules
- Keep `Field: value` together on one logical line.
- A colon is not a generic line-break point.
- A semicolon may separate two structured fields only after parsing; convert those fields to separate logical lines.
- A period ends a sentence but does not create a blank paragraph.
- Do not merge two tests merely because they share the same endpoint.

## Standard scientific wording
- 大鼠 → Rat
- 家兔 → Rabbit
- 豚鼠 → Guinea pig
- 小鼠 → Mouse
- 阴性 → Negative
- 阳性 → Positive
- 轻微刺激 → Slight irritation
- 无皮肤刺激 → Not classified as irritating to skin / No skin irritation, according to source context
- 无眼睛刺激 → Not classified as irritating to eyes / No eye irritation, according to source context
- 粉尘/烟雾 → Dust/mist
- 半数致死剂量(LD50) → LD50
- OECD化学品测试指南423 → OECD Test Guideline 423

Do not translate `classification` conclusions more strongly than the source.
