# Pro Trek and Sea-Pathfinder compilation

The owner supplied **Casio_Pro_Trek_Combined_Model_Specifications_TEXT_ONLY.pdf**, an 11-page text-only consolidation citing two 2017 catalogs, a 2026 product listing, archive-derived SPF-100 information and a comparison graphic. All 79 fully qualified references, 16 family comparison rows, 16 detailed family descriptions, 11 SPF source-comparison rows and the five-key source register are retained. Original underlying sources and graphic/module relationships have not been independently rechecked; all incoming facts remain supplied evidence pending review.

## Coverage

| Family | Qualified references |
| --- | ---: |
| PRX-8000 | 3 |
| PRX-7000 | 1 |
| PRW-7000 | 9 |
| PRW-3510 | 6 |
| PRW-3500 | 3 |
| PRW-2500 | 1 |
| PRW-6100 | 12 |
| PRW-3100 | 14 |
| PRW-3000 | 1 |
| PRG-600 | 7 |
| PRG-270 | 3 |
| PRG-240 | 2 |
| WSD-F20 | 2 |
| PRW-B1000 | 4 |
| PRJ-B001 | 7 |
| SPF-100 | 4 |
| Total | 79 |

This import adds **72 catalog references** and enriches seven existing records. International and Japan-market codes remain separate as printed, following this source’s explicit scope; this is not an assertion that every regional code represents different hardware. Exact record IDs take precedence over aliases in lookup. Sixteen bare family identifiers remain research references rather than extra variant records.

## Source boundaries

- No numeric module IDs or candidate-module assignments are added. The 2017 catalogs do not establish most numeric modules; the eleven current-listing entries have identifiers only. Existing independently recorded library fields remain unchanged, including PRG-270-1 / 3415 and previously recorded PRJ references.
- All dimensions remain scoped family references. No exact `dimensions_mm` field is generated. PRW-3500T’s explicit 14.8 mm thickness footnote is retained separately from the 14.5 mm generic family chart; other titanium-style suffixes do not automatically receive that exception. PRW-3100 sizes are not copied to PRW-3000. PRG-240 size remains unrecorded.
- Nominal water ratings repeated by the model index retain a family-scope uncertainty note. Model-specific band descriptions are retained only where the row explicitly provides them. “Not listed” does not prove absence, and no catalog year becomes a model release date.
- The SPF archive-derived claim is 0.0–80.0 m with 0.1 m steps; the graphic claims 0–60 m. Both remain labelled as a source discrepancy. The archive-derived page describes J/SJ references, not the graphic-only labels.
- Graphic associations SPF-100-1V / 2173 and SPF-100S-1V / 2172 remain unverified reported claims. No fitted module, module-candidate list or new 2172/2173 profile is created. Graphic-only CR2025 / approximately two years, case dimensions and 63 g mass are not promoted to exact model measurements or independently confirmed battery facts.
- Source pagination refers to PDF page positions, not necessarily printed catalog numbers. Consolidated PDF page positions and original source keys/pages are both preserved. No scans, photographs, catalog artwork or comparison image are distributed.

## Files and live access

- `protrek_catalog_import.py`: layout-aware parser for model tables, family paragraphs and source comparisons, runnable against the local supplied PDF with `--output`.
- `research/protrek-combined-specifications-2026-11-15.json`: selected facts, source checksum, register, scope limits and checksum-bound exact-field claims.
- `research/reference-supplements/protrek-combined-specifications-2026-11-15.json`: qualified references and explicitly family-only identifiers, with reading-scope metadata.
- `web/protrek-reference.mjs`: complete browsable source projection. The live reference panel exposes all families, all models, the SPF comparison and source register.
- CSV exports include the source-specific Pro Trek block alongside existing structured specification fields.

Totals after import: **598 catalog models** (594 watches / four clocks), **213 module identities/profiles**, **5,084 candidate fields**, **2,715 research model strings** and **171 family prefixes**.
