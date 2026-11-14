# SEPULKRUM Casio Watch Specifications Database

The catalog now contains **118 models, 71 modules and 1,394 source-backed candidate
facts**. It covers G-SHOCK, Pro Trek, Oceanus, Lineage, Wave Ceptor, Standard,
Vintage, Databank, Edifice and Baby-G. All newly researched facts are pending
independent review. These coverage counts do not imply a complete Casio catalog.

## Use the database now

- [Spreadsheet / CSV](data/watches.csv): browse or download all model rows, with
  source links and pending/verified counts. Unknown values are blank.
- [Full JSON database](data/catalog.json): model and module records with evidence,
  uncertainty and status for every field; original legacy data is retained.
- [Coverage report](data/coverage.json): family counts, missing fields and unknown
  module links. There are 101 single-module references (one legacy association and
  100 pending references), plus 17 shared-manual candidate sets. No model now
  lacks a reported module reference. Seventeen single-module mappings were supplied
  by the repository owner and still await official model-to-module confirmation. Single current support references do not establish all
  historical production revisions.

Download/clone this repository, then use Python 3.10 or newer; no Python packages
are required for catalog use:

```sh
python catalog.py search --series "Oceanus"
python catalog.py search "titanium"
python catalog.py show GA-B2100-1A
python catalog.py coverage
python catalog.py build
```

`show` returns model and linked module separately. Shared guides return
`module: null`, a list of `module_candidates` and separate `module_options`,
rather than selecting the first candidate. `search --verified-only`
returns only records with verified facts and hides pending fields. The current
new facts are all pending, so that search is intentionally empty. A preserved
legacy association is explicitly labeled `legacy_preserved`, not reverified.
CSV rows include pending facts; always inspect their status and sources before
publishing them as verified specifications.

The research batch uses exact model names displayed by the official regional
page: Japanese `JF` suffixes and the displayed `A168WA-1W` are preserved. Similar
variants are separate records; equivalent regional identifiers are not guessed.

Bulk fetching, document manifests, and JSON import arrays avoid model-by-model
entry. The included research and generated exports are committed, so using the
catalog does not depend on being able to fetch Casio from your computer.

## Existing files stay protected

`watches.json` is the original, authoritative legacy dataset. No new command edits
it. The existing `collector.py`, `sources.txt` and collection workflow are retained.
The legacy mixed feature list is preserved verbatim, not guessed into module facts.
`data/catalog.json` and `build/catalog.json` are **proposals**, not replacements
for the protected legacy file.

## Bulk workflow

1. Research official Casio product pages and module manuals. Discover and review
   source lists in batches, not arbitrary guessed module/model ranges. Do not infer
   which module belongs to a model from a shared manual or a similar model name.
2. For permitted automated access, run `python gather.py sources.txt`. Downloads
   and failures appear in `build/snapshots/fetch-report.json`. The new fetcher uses
   explicit official domains, checks robots, rejects redirects before following,
   spaces requests and stops an origin after 401/403/429. Robots errors fail closed.
   The original collector remains available but does not gain these protections.
3. Supply a document manifest for downloaded HTML/text/PDF snapshots and run
   `python specs.py extract manifest.json --output build/extracted.json`. PDF
   extraction requires the system `pdftotext` utility (Poppler). A missing utility,
   image-only PDF or ambiguous regex fails the batch; OCR is not silently guessed.
4. Combine any number of JSON batches:
   `python specs.py build imports/*.json build/extracted.json --output build/catalog.json`.
   For the included starter batch alone, use
   `python specs.py build imports/*.json --output build/catalog.json`.
5. Resolve reported conflicts, review evidence in batches, and commit imports plus
   optional review decisions to a branch/PR. No tool pushes or merges automatically.

JSON candidates contain `kind` (`model` or `module`), `id`, and `specs`.
Each spec contains `value`, `uncertainty` (explicit string), and nonempty `sources`.
Each web source needs HTTPS `url`, ISO `accessed` date, `locator` (page or section),
short `evidence`, and `permission`: `official_public_reference`, `licensed`, or
`permission_granted`. Permission labels document a basis; they do not establish
scraping permission. Automated fetching is restricted to official domains.
Do not add ShockBase data without prior permission; this version rejects it.

Model facts include dimensions, weight, water resistance, materials, color,
series, release date and source-backed `module_id`. Dimensions are an object with
positive `length`, `width` and `thickness` in millimetres. Numeric metre ratings,
bar ratings and generic descriptive ratings remain distinct; the importer does
not assign depth to “Water Resistant” or convert bar to metres. `case_finish`
is separate from case material. Module facts include accuracy, power, alarm, world time,
stopwatch, timer and calendar functions. The validator rejects unknown or wrongly
scoped fields. Values must retain units in the field name or structured value;
module behavior must not be used to infer case properties.

See [the starter module batch](imports/module-3495.json) for a complete example.
It contains seven pending facts from Casio's module 3495 manual. The additional
module batch covers 3513 and 5689; product facts and explicit module links live
in separate import batches. None independently reverify the legacy association.

### Document manifest example

```json
{
  "documents": [{
    "path": "snapshots/manual.html",
    "kind": "module",
    "id": "3495",
    "source": {
      "url": "https://support.casio.com/global/en/wat/manual/3495_en/UQIDSYgokejxbm.html",
      "accessed": "2026-11-14",
      "locator": "Alarm",
      "permission": "official_public_reference"
    },
    "rules": [{
      "field": "alarm_count",
      "pattern": "Alarms: (?P<value>[0-9]+)",
      "type": "number"
    }]
  }]
}
```

Paths resolve relative to the manifest. Rules require exactly one match and a
named `value` capture. Extraction records the snapshot SHA-256 and matching text.
A manifest can contain many documents and rules. Layout-specific adapters are
explicit so website changes cannot silently manufacture specifications.

### Verification and conflicts

Candidates start `pending_review`. A separate JSON array of decisions can approve
whole candidate records: `candidate_sha256` (from `specs.digest(record)`),
`reviewed_by`, and `note`. Pass it with `--reviews reviews.json`. Hashes bind review
to exact evidence and values; stale decisions fail. Reviewer names are an audit
trail, not authenticated signatures; protect review files through GitHub review.
Keep all approved batches and decisions under version control for every rebuild.
The first value wins; later conflicting values are reported and cause exit 2.
Even a later verified candidate cannot silently replace an earlier fact. Identical
candidates/values are reported as duplicates; evidence is not automatically merged.
Review decisions should target the first canonical record for duplicate facts.
Resolve conflicts in a PR before treating the generated catalog as publishable.
Original verified legacy records always remain verbatim in `legacy_watches`.

## Validation

`python -m unittest discover -s tests -v`

The separate validation workflow tests the pipeline, checks that the committed
JSON/CSV/coverage outputs reproduce exactly, and uploads them as an artifact.
The existing daily collector workflow remains intact. There is no unbounded
network crawler or promise that all Casio layouts are supported.

Only `SEPULKRUM/casio-watch-specs` is in scope. The watch-code-decoder repository
is unrelated and is not accessed or modified.

## Expand in batches

Discover product links from a permitted local catalog HTML or sitemap snapshot:

```sh
python discover.py catalog.html --base-url https://www.casio.com/intl/watches/ --output build/discovered-sources.txt
python gather.py build/discovered-sources.txt
python product_import.py --snapshots build/snapshots/fetch-report.json --accessed 2026-11-14 --output build/new-products.json
```

Discovery removes tracking parameters, deduplicates URLs and excludes external
hosts. Sitemap indexes are not followed automatically; feed approved child
snapshots as additional inputs. The fetcher remains subject to robots and access
restrictions. The HTML adapter reads product h1/h4 headings and selected physical
specifications in English or Japanese. It rejects missing or ambiguous identities
and malformed units, checks snapshot hashes, skips unsuccessful downloads, and
never infers module assignments. Generic Casio pages are classified `Casio` until
research establishes the more specific family. Layout failures stop extraction
for review. Manuals still use the explicit document-manifest extractor above.

The committed product batch can be regenerated without network access:

```sh
python product_import.py research/products-2026-11-14.json --output imports/official-products-2026-11-14.json
python catalog.py build
python catalog.py build --check
```

The date supplied to `--accessed` must be the actual snapshot retrieval date.
Research notes retain selected technical fields, source URLs and exact displayed
model names, rather than entire pages. Module notes are concise transcriptions
with section locators. The GA-B2100-1A → 5689 link has its own official support
citation; no links are copied to other variants automatically.

`catalog.py build` refuses conflicts and compares all previously verified facts
and legacy data in the committed catalog before writing outputs. Changing or
removing a verified value, evidence, reviewer or status fails the rebuild. Keep
approved import batches and `reviews.json` under version control. GitHub review
must still protect those files: local reviewer names are not authentication.

Remaining coverage gaps are explicit in `data/coverage.json`. Absence of a field
means unknown, not that a watch lacks the feature. The DBC-32-1A page does not
supply a water-resistance rating; MTP-1302D-1A1V gives a case finish rather than
underlying material. New facts remain candidates until reviewed. No ShockBase
content is included.

## Manual associations and module research

The initial manual batch adds 27 official support/manual reference records and 29 module
specification records. Original product imports are unchanged. References are
established from exact-model official support pages and their primary linked
manuals, rather than matching a similar product name. Model-specific support and
manual URLs are both retained as evidence. All facts remain pending review.

Some guides explicitly cover several modules. For example, the AE-1200WH-1AV
support page links a guide covering 3198/3299; CA-53W-1 links a guide covering
437/438/3208. These are **shared-guide candidates, not confirmed alternatives for
every manufactured watch**. No exact module is chosen automatically. Even a
single support endpoint describes the current official reference, not a guarantee
about all past production revisions. The GMW-B5000D-1 reference currently points
to 3539; its evidence date and revision uncertainty remain attached.

Shared-guide specifications are read carefully per module: 437/438 calendar rows
end at 2079, while 3208 runs through 2099; module 438 uses a different battery
from 437/3208. These facts remain in separate module records. The generic guide
linked for F-91W-1 and A158WA-1 also explicitly discusses a Module 1271 exception,
so those model references remain conservative candidate sets. Nothing is inferred
from the physical case specifications.

`data/coverage.json` distinguishes `models_with_single_module_reference`,
`models_with_ambiguous_manual`, and `models_without_any_module_reference`.
`models_without_module_link` retains its earlier meaning: no single module link,
including shared-guide records. CSV adds `module_candidates` and
`module_link_status`; its `module` cell stays blank for ambiguous cases.

Research notes can be reimported in batches without network access:

```sh
python manual_import.py research/module-associations-2026-11-14.json --output imports/support-module-associations-2026-11-14.json
python manual_import.py research/manual-specifications-2026-11-14.json --output imports/manual-specifications-2026-11-14.json
python catalog.py build
python catalog.py show AE-1200WH-1AV
python catalog.py show GA-2100-1A1
```

`research/module-associations-2026-11-14.json` also records unavailable pages and
regional model-name mismatches. A168WA-1W is not assigned the module from an
A168WA-1 support heading. The five European Lineage records remain without module
links rather than inheriting a Japanese-suffix model's association.

For future permitted snapshot batches, use:

```sh
python manual_import.py --support-manifest support-snapshots.json --output build/manual-links.json
```

The manifest has `accessed` (retrieval date) and a `documents` array. Each document
contains `model`, `support_url`, `support_path`, `manual_url`, and `manual_path`.
Paths are relative to the manifest. The adapter requires one exact model heading,
checks that the manual URL actually occurs as a link on that support snapshot,
checks official domains and module identity, and records SHA-256 hashes of both
snapshots. PDFs require `pdftotext`; HTML/text are also supported. Empty/image-only
manuals and conflicting headers fail for review. Shared titles and module-specific
exceptions are retained as candidates. This parser is a candidate generator, not
an independent factual verification service. It makes no network requests;
`gather.py` remains responsible for permitted downloads and now also recognizes
the official `support.casio.jp` host, with the same robots/access-denial rules.

## Expanded official-source catalog

The expansion batch contributes 77 additional model records, 72 support/manual
references and 33 module profiles. Current family coverage is G-SHOCK (33),
Lineage (17), Oceanus (22), Pro Trek (11), Wave Ceptor (20), plus Standard,
Vintage, Databank, Edifice and Baby-G. All specification fields remain candidates pending
independent review; record count is not a claim of complete specifications.

The product importer now retains cloth, leather and composite-band descriptions.
It continues to preserve exact regional model identifiers. Japanese Lineage
identifiers with `JF` remain separate from earlier European identifiers; a module
reference established for one is not silently copied to the other. Unavailable
support pages do not inherit a sibling model's module assignment.

Manual research preserves the stated accuracy and its conditions. For example,
5575/5643 and 5644 specify ±30 seconds per month when radio correction is
unavailable; this is not defaulted to the ±15 seconds common in other modules.
Sparse module records contain only the selected facts supported by the source.
`module_field_coverage`, `module_profiles_by_fact_count`, and
`modules_with_sparse_profiles` in the coverage report expose that incompleteness.
Unknown functions are not assigned false or zero values.

Reproduce the new batches with:

```sh
python product_import.py research/products-expansion-2026-11-14.json --output imports/official-products-expansion-2026-11-14.json
python manual_import.py research/module-associations-expansion-2026-11-14.json --output imports/support-module-associations-expansion-2026-11-14.json
python manual_import.py research/manual-specifications-expansion-2026-11-14.json --output imports/manual-specifications-expansion-2026-11-14.json
python catalog.py build
python catalog.py build --check
```

The research files retain selected technical facts, official URLs, retrieval date,
and section/page locators. The retrieval report also records unsuccessful product
and older support-page checks. Retrieval failures do not mean a product or feature
does not exist. Original imports, verified legacy data, and the original collector
remain preserved.

## Repository-owner supplied mappings

The 17 previously missing model/module mappings supplied by SEPULKRUM are recorded
verbatim in [the user research batch](research/user-module-mappings-2026-11-14.json).
They are imported as `pending_review`, with explicit `user_provided` provenance.
An official manual for a module does not independently establish which watch
model uses it. The supplied mapping and the manual's function facts remain
separate records.

JSON lookup and CSV now include `module_link_provenance`. User citations appear
in `source_references` as a committed research-file path; `source_urls` continues
to contain actual web citations. User evidence has no invented HTTPS URL. It
requires `kind: user_provided`, `reference`, `provided_by`, `source_sha256`, date,
locator, evidence and `permission: user_provided`. Web-source URL and permission
rules still apply to web citations. `catalog.py build` checks the citation's file
hash, attribution and exact model/module pair; stale or unrelated citations fail.

Reproduce the supplied batch and supporting module profiles with:

```sh
python user_import.py research/user-module-mappings-2026-11-14.json --output imports/user-module-mappings-2026-11-14.json
python manual_import.py research/supplied-module-manuals-2026-11-14.json --output imports/supplied-module-manuals-2026-11-14.json
python catalog.py build
```

The official manuals add selected facts for 3298, 2888, 1572, 2784, 3415 and
3476. Operating-only documents produce sparse profiles: unsupported accuracy and
battery figures are left unknown. The scanned 1572 operation chart was inspected
visually; the generic analog guide's date-setting group explicitly lists 2784.

Coverage lists the 17 owner-supplied mappings separately in
`user_provided_module_references`. The 17 shared-guide candidate sets are a
different group and are unchanged. No earlier import batch, legacy watch record
or verified fact is replaced by the supplied mappings.

## Follow-up case-back photographs

[Case-back observations](research/caseback-observations-2026-11-14.json) record
visual transcriptions of the 11 photographs subsequently supplied by SEPULKRUM.
They corroborate visible family/module pairs such as WV-58R/3476,
WV-59R/3476, PRJ-B001/5732, PRG-270/3415, GD-010CE/3569, F-105/1572,
DBC-32/2888 and A168/3298. The MTP-1302 engraving is partly cropped/faint;
its reading is explicitly lower confidence.

The Lineage pictures show LCW-M170T/5161 and LCW-M100TS/5161. The latter
is a titanium-family marking and is not used to establish the separate
LCW-M100DSE stainless-steel association. Case backs generally omit colour and
regional suffixes, so these pictures do not independently verify every complete
catalogue identifier in the supplied list. Associations retain their existing
user-provided provenance and pending-review status.

The observation file references conversation attachment order. Original image
files were not available in the execution workspace and are not archived in this
repository; no image hashes or public source URLs have been invented.
