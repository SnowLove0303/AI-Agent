# EP-1704 regression policy expectations

This source is included to exercise v2.1 policy only; it is not an approved output reference.

## Missing-data suppression
The following Section 9 source values are pure missing-data placeholders and their complete template items must not display:
- 9.2 嗅觉阀值：无数据
- 9.3 pH值：无数据
- 9.7 蒸发速率：无数据
- 9.10 相对蒸气密度：无数据
- 9.13 表面张力：无数据
- 9.14 辛醇/水分配系数的对数值：无数据
- 9.16 引燃温度：无数据

`不适用` values are not automatically removed by this rule; they are applicability conclusions unless company policy says otherwise.

## Section 2 semantic wrapping
Source precautionary statements:
- P273 禁止排入环境。
- P501 将本品或其容器送至有资质的废物处理厂处置。

In the standardized 2.6 value, P273 and P501 must appear on separate logical lines, in that source order. They must never be concatenated into a single continuous line/paragraph.

Source H412 is a single hazard statement, so 2.5 should not receive an artificial extra break.


## Continuous numbering expectation
After any EP-1704 missing-data items are suppressed, surviving numbered items in each section must be renumbered continuously. In Section 2, removed items must not leave gaps; H412/P273/P501 remain content inside their corresponding parent items and do not consume extra `2.x` numbers.

- Section 11 must retain the source sentence `该产品无可用的毒理学研究。` as an unnumbered explanatory line; endpoint rows remain omitted because the source provides no endpoint-specific results.


## v2.6 dual-company expectations
Default EP-1704 release produces both `EP-1704_MSDS_CN_冠志.docx` and `EP-1704_MSDS_CN_国彩.docx`. Guocai must use the approved Guocai supplier/contact values and footer company name, while every product/safety fact remains the same as the Guanzhi output.
