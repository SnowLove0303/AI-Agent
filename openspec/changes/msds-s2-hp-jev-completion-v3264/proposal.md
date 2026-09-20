# Change Proposal: MSDS Section 2 H/P Completion, Jev System One Integration & Deep Skill Optimization (v3.26.4)

## Why
In standardizing products such as PA-3337A, four critical defects were identified:
1. Signal Word Misclassification: Source explicit 警告词：警告 was overridden to 无信号词 due to rigid coupling with GHS危险性类别: 无. Under GHS and GB 13690, 警告词 is legally the Signal Word (警告 / Warning).
2. Aggressive Section 2 Suppression: When source documents provide natural language precautionary and hazard statements without alphanumeric Pxxx / Hxxx codes, previous versions blindly deleted the entire hazard statements, precautionary statements, physical/chemical hazards, and environmental hazards rows instead of reverse-searching and populating standard GHS codes.
3. Cross-Section Regulatory Intelligence Gap: Source Section 3 contained critical regulatory exemption evidence (neutralizing amine N,N-DMEA bound as salt, <2.0%, below SCL >= 5%), explaining why the product does not trigger hazard classification while retaining warning precautions. This was dropped as Section 3 trivia rather than routed to Section 2 label elements and notes.
4. Section 11 Toxicology Coarseness: Section 11 omitted the primary polymer's explicit 无资料 (no data) status and cited reference component data without identifying the chemical name (二丙二醇丁醚 / CAS 29911-28-2).

## What Changes
1. Intelligent Signal Word Recognition: Parse 警告词 as 信号词 and preserve 警告 / Warning faithfully.
2. Reverse GHS H/P Code Search & Completion Engine:
   - Provide a built-in semantic lookup engine mapping natural language precautions to standard GHS P-codes (P280, P264, P270, P271, P304+P340, P302+P352, P305+P351+P338, P301+P330+P331, P370+P378, P391, P403+P235, P410, P501).
   - Format statements as canonical [Code] [Statement].
3. Section 2 Full Skeleton Preservation:
   - Retain 2.1 Category, 2.2 Signal Word, 2.3 Label Elements/Notes, 2.4 Hazard Statements, 2.5 Precautionary Statements, 2.6 Physical/Chemical Hazards, 2.7 Environmental Hazards, 2.8 Other Hazards.
4. Jev System One (TypeSafe System One) Integration:
   - Integrate C:\Users\Administrator\.jev\jev.py for automated intelligent routing and confidence scoring:
     - Routing Section 3 amine salt exemptions to Section 2 label elements;
     - Disambiguating signal words and boundary classifications.
5. Section 11 Structured Multi-Tier Toxicology:
   - Preserve polymer 无资料 statements;
   - Explicitly qualify component reference data with CAS and substance names.
6. PA-3337A Regeneration:
   - Regenerate all 16 deliverables (8 MSDS + 8 TDS) meeting 100% of quality contracts.
7. Version Bump to v3.26.4:
   - Bump version, update contracts, pass all unit tests, sync to Antigravity global config, and push to remote.
