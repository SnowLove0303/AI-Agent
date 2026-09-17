## Context

The repository already contains mature MSDS/TDS skills and an older Section 2 evidence-policy pattern, but it has no standalone legal-compliance judgment skill. The canonical legal data is maintained outside this repository under `法律法规物质限制清单_CSV导出` and `欧盟玩具`. The new skill must not duplicate those datasets or touch the dirty MSDS/TDS worktree.

## Goals / Non-Goals

**Goals:**

- Make the complete MSDS/TDS assumption explicit and deterministic.
- Reuse the existing CSV exports as the only legal-material source.
- Resolve direct material restrictions and downstream-use applicability separately.
- Preserve evidence and generate the same information hierarchy as the approved PDF report.
- Keep the implementation dependency-free apart from Python's standard library.

**Non-Goals:**

- Do not copy or normalize the legal datasets into the Git repository.
- Do not infer a customer's private standard from an opaque code.
- Do not replace formal laboratory testing or legal advice when a user supplies a different evidence mode.
- Do not modify the existing MSDS Skill, TDS Skill, or their dirty files.

## Decisions

### 1. Use a repository-local skill folder with an external data-root override

The skill will live in `legal-compliance-judgment-skill/`. Its registry will default to the current canonical path but accept `--data-root` and `GUANZHI_TONG_LEGAL_DATA_ROOT`. This keeps the pushed skill portable while preserving one canonical dataset.

Alternative rejected: copying CSV/PDF data into the repository. That would create a second regulatory source, increase drift risk, and violate the one-source rule.

### 2. Use a closed-world default for this skill

The report must reduce “cannot determine” outcomes under the user's explicit assumption. The engine will therefore treat the supplied MSDS/TDS facts as complete, mark absent substances as absent for list screening, and classify omitted downstream uses as not applicable. The output will visibly record this assumption so the result is not mistaken for a laboratory certificate.

Alternative rejected: inheriting the older unknown/manual-review policy unchanged. It is correct for uncertain SDS inference but does not meet this skill's declared complete-facts contract.

### 3. Use a small normalized row adapter instead of a database migration

The engine will read CSV files with encoding fallback, normalize headers and identities, and keep raw rows in evidence objects. It will not introduce SQLite, a web service, or a new package for the initial skill.

Alternative rejected: rebuilding the old database stack. The task is a skill with deterministic local execution, and the supplied CSV exports are already the intended source artifacts.

### 4. Separate applicability from substance matching

Each request will first resolve market/use/substrate scope, then run exact and group-aware substance matching. This allows the PU-1002 leather-coating case to return `不适用` for toy-only or architectural-only standards while still screening direct material lists.

### 5. Keep opaque customer standards as explicit evidence gates

Codes without a resolvable source remain `需补证`. The engine will provide a precise reason and required fields rather than guessing a standard title or limit.

## Risks / Trade-offs

- [Closed-world false-positive risk] → Print the assumption in every report and keep the mode configurable for future evidence modes.
- [External data path risk] → Require the data root to exist, validate required filenames, and fail loudly instead of falling back to another copy.
- [Regulatory scope drift] → Store source versions and file hashes in the report; refresh the local exports deliberately rather than silently scraping the web.
- [Large EU PDF cost] → Use the existing EU Toy PDFs as registered reference sources and activate them only when toy applicability is selected; the first implementation does not reparse 2,000+ pages on every material-only run.
- [Dirty repository risk] → Implement in a clean detached worktree and stage only the new skill folder plus the OpenSpec change.
