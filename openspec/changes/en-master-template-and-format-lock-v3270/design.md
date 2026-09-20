# Design: Standard EN Master Template Integration & Bold Preservation

## Architecture
- **Template Geometry**: Update Table 7 row count from 16 to 12. Standard EN geometry is `[9, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2]`.
- **Run-Level Bold Protection**: All section headings, field labels, toxicological endpoint prefixes, and regulatory clauses remain bold. Only value cells receive dynamic data with non-bold typography.
- **WPS Rendering Stability**: Trailing empty paragraph height set to 1pt (<w:spacing w:line="20" w:lineRule="exact"/>), eliminating 8th blank overflow page.
- **Hygiene Gate**: Zero-tolerance audit for Chinese characters in English deliverables.
