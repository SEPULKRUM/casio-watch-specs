# Consolidated model and module reference import

The owner supplied **Casio_Combined_Model_Specifications_TEXT_ONLY.pdf**, a 12-page consolidation of nine PDFs and one AWG-M520UA packaging photograph. All 29 selected tables, source keys and cautions are preserved as structured supplied evidence. The original underlying documents have not been independently rechecked; these are pending secondary claims, not newly verified Casio facts. No photographs, scans, logos or recreated product images are distributed.

## Coverage and deduplication

74 canonical catalog identities in this import add 67 new model records and enrich seven existing Oceanus models. Twelve module groups add eleven new profiles; 5347 already existed. The supplied source register S1–S10 and original page ranges remain attached to evidence, alongside the consolidated PDF page locators.

Included: four DW-H5600 models; three GBX-H5600 models and seven battery scenarios; four BESIDE BMS-500 models; one AWG-M520UA collaboration plus eight separately described historical collaborations/platform references; three GWR-B3000 variants; 19 Oceanus 2024.SS references; six T1000, eighteen T2600 and four T2610 references; DW-290 generations and reported variants; five DW-285 variants. Four T2600 entries overlap the Oceanus catalog table and are not counted twice.

The reference library records 94 source designations: 74 canonical model identifiers, five regional/short aliases, six chart-only Oceanus family labels and nine incomplete/excluded/shortened references. References may already exist from prior research; their new observations supplement earlier provenance. Only the canonical catalog set receives specification records from this import.

## Scope limits retained in the interface

- DW-H5600 module 3516 is cited through the S2 cross-reference; its own brochure does not print the module. It is distinct from GBX-H5600 / 3586. No dimensions or part interchangeability are inferred between them.
- AWG-M520UA is indexed to photographed designation AWG-M520UA-1EJR, not counted as another variant. The cited UNITED ARROWS 13.1 mm and Casio base AWG-M520 15.3 mm thickness claims remain labelled separately, with no single selected dimensions value.
- BMS-500 product-page SR927SW and operation-guide SR927W cell claims remain a source discrepancy. Neither is silently chosen as the replacement cell.
- The three GWR Japan suffixes are supplied regional aliases of the three international references; they do not add three watches.
- Oceanus comparison dimensions, mass exceptions and platform features remain labelled family-level. Six bare family labels do not become exact colour variants. Modules are not guessed for S-series or T6000; 5347 is associated with T2600/T2610 only through the detailed reference. Variant finish, band, date, weight and limited-edition claims remain separate; approximate / unverified values are retained as such.
- DW-290 preserves 1219 → 1189 → 3231 chronology. DW-290G-9V has the supplied 1219/1189 alternatives only. Modern 3231 dimensions/functions do not become vintage measurements/functions. The DW-290-1 alias is explicitly scoped to the second-era reference within the combined designation history.
- DW-290B-2V retains an unconfirmed module claim rather than an asserted fitted module. Fitment-only / unreliable identifiers and the unspecified B&Y collaboration SKU remain research references. No DW-290G-1V is inferred from G-9V ownership evidence. The unverified T2600TA-8AJF and shortened T2600-7AJF are not additional watches.
- DW-285 imagery in the cited study is described as catalog-style recreation. No image is copied or treated as proof. Its -VS meaning remains unassigned.

## Implementation and verification

`combined_catalog_import.py` reproducibly parses the table columns and wrapped rows from a local supplied PDF. `research/combined-model-specifications-2026-11-15.json` preserves selected facts, source register, caution notes and checksum-bound exact-field claims. `web/combined-reference.mjs` provides the complete browsable reference. Model/module fields and CSV exports retain structured source scope. Earlier facts are preserved unchanged; incoming duplicate fields are not substituted for existing provenance.

Totals after this import: **526 catalog models** (522 watches / four clocks), **213 module identities/profiles**, **4,549 candidate fields**, **2,699 research model strings**, **170 family prefixes**.
