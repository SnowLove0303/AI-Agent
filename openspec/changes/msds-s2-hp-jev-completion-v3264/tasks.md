# Implementation Tasks

## Phase 1: Engine & Resolver Implementation
- [x] 1.1 Implement scripts/ghs_code_resolver.py mapping natural language precautions and hazards to GHS P/H codes
- [x] 1.2 Implement scripts/jev_dispatcher.py wrapping C:\Users\Administrator\.jev\jev.py with safe fallbacks
- [x] 1.3 Update scripts/section2_ghs_policy.py to support semantic completion and full skeleton preservation
- [x] 1.4 Update scripts/audit_section2_release.py to validate completed P-codes, signal words, and physical/chemical hazard rows

## Phase 2: Unit Testing & Verification
- [x] 2.1 Add test_section2_code_completion.py covering natural language P-code mapping
- [x] 2.2 Add test_jev_dispatcher.py validating Jev routing and fallback behavior
- [x] 2.3 Verify all existing MSDS Skill unit tests pass cleanly

## Phase 3: PA-3337A Regeneration
- [x] 3.1 Regenerate 4 MSDS DOCX files for PA-3337A with full Section 2 skeleton and completed P-codes
- [x] 3.2 Regenerate 4 TDS DOCX files for PA-3337A with 6 technical indicators and 3 features
- [x] 3.3 Convert all 8 DOCX files to 8 PDF files via kwpsconvert
- [x] 3.4 Validate all 16 deliverables with release audits

## Phase 4: Skill Release & Version Bump
- [x] 4.1 Bump VERSION.txt to 3.26.4
- [x] 4.2 Update CHANGELOG.md, SKILL.md, and README.md
- [x] 4.3 Package clean distributable zip msds_unified_eight_deliverable_skill_v3.26.4-full-package.zip
- [x] 4.4 Synchronize to Antigravity global config skill
- [x] 4.5 Stage, commit, and git push to remote main
