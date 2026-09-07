## 1. Regression fixtures and contract tests

- [x] 1.1 Register the user-provided PU-1001 source, legacy output, and formal CN template as read-only regression inputs; verify their paths and SHA-256 values are recorded without modifying any of the three files
- [ ] 1.2 Add PU-1001 assertions for `掬泉路`, the complete Section 2 ingestion text, all FKM/IIR/NBR glove parameters, blank Section 8 recommendation, absent Section 8.2 prose, absent Section 10.4/10.5 fields, note-only Sections 11/12, and fixed `Version：V1.0`; verify the focused test module fails against the known legacy output

## 2. Template slot contract

- [ ] 2.1 Implement a template-derived slot registry in the existing MSDS pipeline that records section, physical row/cell identity, merged-cell identity, field key, lock state, writable state, and special policy; verify registry generation is deterministic for the pinned CN/EN template hashes
- [x] 2.2 Classify ordinary blank value objects as non-writable and classify Section 8.2 data rows as the only ordinary table-data exception; verify the registry rejects a Section 8 recommendation write and accepts an approved Section 8.2 record
- [ ] 2.3 Add a persisted-output mutation audit for blank-slot writes and fixed header/label changes; verify the audit reports a blocking error with the target slot and source field

## 3. Source states and missing-data policy

- [ ] 3.1 Add the `SUPPORTED`, `EXPLICIT_MISSING`, `NOT_APPLICABLE`, and `ABSENT` source-field states with source-position provenance; verify state classification preserves exact source text
- [x] 3.2 Implement Section 9 pure-missing row suppression and continuous renumbering while retaining `不适用` and substantive values; verify PU-1001 Section 9 output has no pure missing rows and continuous numbering
- [x] 3.3 Implement Section 11/12 note-only reduction when no valid endpoint exists, and partial-data handling that suppresses source-absent template fields; verify PU-1001 retains only each source explanation row
- [x] 3.4 Implement the other-section rule that retains an explicitly sourced missing field as the exact customer-facing placeholder but suppresses a template-only field; verify Section 10.4/10.5 are absent for PU-1001

## 4. Controlled overwrite integration

- [x] 4.1 Replace positional ordinary-row projection with registry-authorized value writes while preserving fresh-clone template geometry; verify existing geometry and locked-label audits still pass for CN and EN
- [x] 4.2 Route Section 8.2 exclusively through its dedicated parent/header/data-row writer and prevent cross-section prose synthesis; verify a source without 8.2 data emits no generated engineering-control text or illustrative OEL fact
- [x] 4.3 Preserve source text by default and record any approved semantic normalization or alias mapping; verify address and Section 2 regression values are byte/text-equivalent after normalization
- [x] 4.4 Reuse one approved semantic model for the four language/company variants; verify company-only fields differ by approved overlay and product facts remain equivalent

## 5. Audit and release gates

- [ ] 5.1 Extend source-fidelity and section-specific audits for blank-slot writes, source-value drift/loss, template-example leakage, Section 8 parameters, and Section 11/12 note-only behavior; verify each failure is B1-or-higher and fail-closed
- [ ] 5.2 Update the machine-readable evidence records with source field, target slot, state, and review evidence; verify every required rule has exactly one result and a usable evidence path
- [x] 5.3 Run the focused PU-1001 tests and then `py -m pytest -q "MSDS Skill/tests"`; verify all tests pass
- [x] 5.4 Run the four-variant DOCX-first build, all template/semantic/company audits, PDF lineage checks, and visual QA; verify no template/source file changed and the final report is `RELEASE_PASS` only when all blockers are clear

## 6. Measured efficiency pass

- [ ] 6.1 Measure extraction, model preparation, four DOCX builds, audits, PDF conversion, and total runtime before optimization; verify the timing report is stored with the PU-1001 replay evidence
- [ ] 6.2 Eliminate repeated source extraction, template registry construction, and redundant DOCX parsing without weakening the final persisted-file audit; verify the optimized run produces identical semantic outputs and no new audit failures
