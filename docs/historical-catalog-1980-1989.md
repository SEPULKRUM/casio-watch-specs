# Historical catalog extraction: 1980, 1982, 1985, 1989

The owner supplied a 14-page text-only extraction of four Casio catalogs. Import all 263 readable model rows, 14 selected module notes and 56 uncertain readings. This is secondary supplied evidence: original catalog scans have not been independently rechecked. New facts remain pending review.

| Catalog | Readable models | Uncertain readings |
| --- | ---: | ---: |
| 1980 | 26 | 6 |
| 1982 | 43 | 6 |
| 1985 | 166 | 3 |
| 1989 | 28 | 41 |
| Total | 263 | 56 |

The readable set includes 259 watch entries and four clocks (PQ-5, DA-101, DA-106, DQ-300). Clocks are labelled separately. Each model retains its exact identifier, supplied module label when present, printed description, material/finish text and catalog year. Sources record both the extraction PDF page and the original catalog page; these are different locators. The catalog year is not asserted to be a release date.

Preserve two-digit modules, such as 56 and 79, without zero-padding or confusing them with series identifiers. Eleven rows lack an established module; those links remain unknown. There are 91 distinct module identities in the supplied labels, 88 newly represented in this catalog. Only 14 have selected function-table notes; the others carry model-association references, not invented functions. Battery/accuracy columns explicitly left unattributed for module 317 remain unattributed.

Printed materials and finishes are retained in a dedicated field. A material label does not automatically establish whether it describes the case, bezel, band or plating. Numeric water resistance is imported only where explicitly stated in the row. Do not treat every DW model as G-SHOCK or assume a 200 m rating from its prefix.

Historical model results suppress modern prefix/community interpretations, colour heuristics and anniversary decoding. For example, GM-40 remains a historical game-watch identifier. Existing modern records retain their own rules.

The 56 uncertain scan readings, including punctuation and possible module readings, are preserved in a separate review panel and research data. They are not imported as specification models, silently corrected, or used to assign modules. No scanned pages, product photographs, advertisements or image tables are distributed.

Files:

- `research/historical-catalog-1980-1989.json`: source checksum, selected facts, locators, uncertainty list and exact-field evidence claims.
- `research/reference-supplements/historical-catalog-1980-1989-2026-11-15.json`: readable identifier library supplement.
- `historical_catalog_import.py`: reproducible layout-aware parser. Run with the local PDF path and `--output` to produce a structured intermediate file.
- `imports/zzzzzzzzzzzzzzzzzz-historical-catalog-1980-1989-2026-11-15.json`: pending specification candidates.

Catalog totals after import: 459 model records (455 watches and four clocks), 202 module identities/profiles, 3,916 candidate facts; 2,669 research model strings and 169 family prefixes.
