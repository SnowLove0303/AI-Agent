# Baseline and rollback evidence

- Baseline revision: `3e5eef903da06b249bce3b4fbd43f49b3e97b087`
- Baseline backup: `C:\Users\52882\AppData\Local\Temp\msds-s24-precautionary-group-preservation-baseline-20260917`
- Existing unrelated dirty worktree changes were preserved; this change does not use reset/checkout or delete any package.
- Baseline check: `git diff --check` completed with no whitespace errors. Git emitted only existing LF/CRLF normalization warnings.
- Rollback: copy only the affected files from the backup directory back to the worktree, then rerun the focused Section 2 tests, `git diff --check`, and the OpenSpec validation.

## Affected-file baseline SHA256

| File | SHA256 |
|---|---|
| `MSDS Skill/scripts/extract_source_facts.py` | `8AEEE358077A728D9ADB305D410C88514934CBA222AF7C0DE15B6750033F28AD` |
| `MSDS Skill/scripts/section2_hp_policy.py` | `0521FA6B094BC6D041063B1F821DCEA2DB3D3205BD336D299016D95C1D838622` |
| `MSDS Skill/scripts/section2_ghs_policy.py` | `BFDD37445B7FF15A798546FE5103CA8417368BB1CC9A95143F545F3C13199BFD` |
| `MSDS Skill/scripts/section2_fact_router.py` | `37A786EE515067F6F1B0371784B04DE252E8B09DC13C83633F0254AB6719DA41` |
| `MSDS Skill/scripts/source_interpretation_contract.py` | `7C9CA97AED65B845E28440C6B018CB0175ADDAB72DD915F5727317791CAF578E` |
| `MSDS Skill/scripts/draft_en_facts.py` | `0EF2D1AEC5FE861CE1103438EB931A82C44D2A979D52F5C35C0A3C4E0812DEBB` |
| `MSDS Skill/scripts/audit_section2_release.py` | `D54DB6975F2D35D2A1AB432F5F0856A9FB481A9F9C9EA8D89EF93351DFA1A686` |
| `MSDS Skill/scripts/audit_openspec_overwrite.py` | `3598A33ED16192FD660079AAA89442AFDB0DFED9AD50E803221B26D4D0E37600` |
| `MSDS Skill/tests/test_extract_source_facts.py` | `4601C726AD3DB63A9268B9ABA1A5E36BFC89CF6BDFD113673067053E2AD65260` |
| `MSDS Skill/tests/test_section2_policy.py` | `B479F1D36223D91548E6DC4D0503CB54881FBFA0BDDB37A48064A368C6724B81` |
| `MSDS Skill/tests/test_section2_ghs_policy.py` | `F6A4E992042B0C8414C5A396C71405CDE6A2C7104A938EA4A592A03C99C49E3E` |
| `MSDS Skill/tests/test_section2_fact_router.py` | `BC9CEA44EF6894F57D43D9A73B0776FD1183FD412638701E42C2A653BFAC3D8C` |
| `MSDS Skill/tests/test_v3253_regressions.py` | `6E0B3139400775BE7AFB85A700F120B7A54E1122B20F7B93A048543063132330` |
