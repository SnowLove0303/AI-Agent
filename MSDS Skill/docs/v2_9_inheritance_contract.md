# v2.9 Full-Inheritance Contract

`MSDS_Word_Standardizer_Skill_v2.9` is the immutable Chinese overwrite baseline.

## Non-regression rule
Every v3.x release MUST preserve every v2.9 requirement, overwrite rule, program, test fixture, approved example, and QA gate. New four-format or English behavior is additive only.

The following may be enhanced only when the enhancement is stricter and does not remove legacy behavior:
- `SKILL.md` and `CHANGELOG.md` (version wrapper/documentation);
- sentence-boundary processing, where Section 11 structured toxicology has higher priority than generic punctuation splitting.

All other legacy files must be byte-identical to v2.9 unless an explicit migration record, compatibility test, and rollback copy are included.

## Required release gate
Run `python scripts/audit_v29_inheritance.py --v29-zip <MSDS_Word_Standardizer_Skill_v2.9.zip> --skill-root <candidate>`.
Any missing legacy file or unapproved change is release-blocking.
