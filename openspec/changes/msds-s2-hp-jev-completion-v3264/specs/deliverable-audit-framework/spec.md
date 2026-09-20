# Delta Spec: Deliverable Audit Framework & Section 2 Semantic Completion

## ADDED Requirements

### Requirement: Section 2 Signal Word Recognition
The Section 2 generator SHALL recognize 警告词 as a valid signal word synonym and map it to 警告 (CN) / Warning (EN).

#### Scenario: Parse explicit 警告词
- GIVEN a source Section 2 containing 警告词：警告
- WHEN Section 2 signal word is resolved
- THEN the resolved signal word SHALL be 警告 in Chinese and Warning in English.

### Requirement: Reverse GHS P-Code Completion
When Section 2 precautionary text contains natural language guidance without alphanumeric P-codes, the generator SHALL reverse-search canonical GHS P-codes and prefix each statement with its standard code.

#### Scenario: Complete P-code from natural text
- GIVEN a precautionary statement 操作时穿戴必要的防护用品（手套、防护镜、工作服等）
- WHEN code resolver processes the text
- THEN it SHALL assign P280 and format the statement with standard canonical text.

### Requirement: Physical, Chemical and Environmental Hazard Preservation
When Section 2 contains physical/chemical hazards or environmental hazards, the generator SHALL NOT suppress their respective rows.

#### Scenario: Retain physical and chemical hazard row
- GIVEN a source Section 2 containing 物理化学危险：对水体、土壤可造成一定的污染。
- WHEN Section 2 suppression executes
- THEN row 2.5/2.6 physical and chemical hazards SHALL be preserved in the deliverable.

### Requirement: Section 3 Regulatory Exemption Routing
When Section 3 contains neutralizing amine salt or concentration threshold notes, the generator SHALL route an explanatory notice into Section 2 label elements.

#### Scenario: Route DMEA amine salt note
- GIVEN Section 3 text describing N,N-二甲基乙醇胺 bound as salt below threshold SCL 5%
- WHEN Section 2 label elements are assembled
- THEN an explanatory note explaining why the product does not trigger hazard classification SHALL be included in Section 2.

### Requirement: Multi-Tier Structured Section 11 Toxicology
In Section 11, the generator SHALL preserve primary polymer 无资料 status and qualify reference component toxicology with substance names and CAS numbers.

#### Scenario: Retain polymer no-data and component qualification
- GIVEN Section 11 source stating 羟基聚丙烯酸酯分散体 毒性：无资料 and component data for 二丙二醇丁醚
- WHEN Section 11 is formatted
- THEN both the polymer no-data conclusion and the explicit component identifier SHALL be output.
