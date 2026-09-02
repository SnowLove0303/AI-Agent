# Lessons Learned from PA-4817 Iteration

1. Treating the source's headings as replacement labels distorted Section 8. Fix: source headings are semantic inputs only; template labels remain immutable.
2. Rebuilding Section 11 to match source ordering destroyed the approved fixed structure. Fix: endpoint-by-endpoint mapping into existing labels.
3. Leaving unsupported template fields blank created empty labels. Fix: unsupported items must disappear.
4. Clearing a paragraph and writing everything into the first run changed label formatting/alignment. Fix: preserve label XML and edit only value runs.
5. Empty-looking cells still produced tall rows because hidden `<w:p>`, empty `<w:r>`, breaks/tabs and row-height properties remained. Fix: OOXML-aware compaction plus render QA.
6. Global row-height clearing/format normalization is risky. Fix: clean only affected content rows/paragraphs and preserve template anchors.
7. Non-bold body text drifted across sections. Fix: one approved body-text exemplar for run character formatting.
8. XML checks alone missed WPS/Word-visible spacing defects. Fix: final PNG rendering and page-by-page inspection is mandatory.
9. Repeated patching of a damaged output compounds layout errors. Fix: once structure is damaged, restart from untouched template and reapply the semantic mapping.

10. Showing literal “无数据” values made the standardized document noisy and contradicted the desired display policy. Fix: classify missing-data placeholders before mapping and omit the entire item; do not write the placeholder.
11. Multiple H/P statements in one continuous paragraph reduce readability and make Section 2 inconsistent. Fix: parse statement codes and insert semantic breaks so every complete H/EUH/P statement starts on its own line while preserving source order and keeping code+text together.


## Omission can create broken numbering
Failure mode: correctly suppressing `无数据` rows but leaving original numeric prefixes produces visible gaps (for example `2.1, 2.2, 2.4`). This is structurally untidy and violates the approved output convention. Correct sequence: decide visibility first, delete unsupported items, then run a numeric-prefix-only renumber pass. Never renumber child labels or H/P statement lines.


## Section 11 general-study statement exception
A full sentence such as `该产品无可用的毒理学研究。` carries section-level meaning: it tells the reader why endpoint data are absent. Suppressing it as though it were a bare `无数据` cell removes supported source information. Preserve the sentence under Section 11, while still deleting unsupported endpoint rows and never inventing endpoint results.


## v2.6 lesson: company identity must be a whitelisted overlay
For sister-company MSDS outputs, do not duplicate the whole mapping workflow. Build one normalized content model and apply a narrow company-profile overlay. This prevents silent divergence between variants and makes parity auditable.

## v2.9 — 不能只依赖 Word 自动换行
长正文即使能自然折行，也不等于符合公司阅读规范。标准化时必须主动按完整句号/分号切分语义行；同时不能用空段落换行，否则会重新引入大块空白和异常行高。ASCII 句点存在小数/缩写歧义，因此不能简单 `split('.')`。
