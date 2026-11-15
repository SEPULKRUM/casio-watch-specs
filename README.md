# SEPULKRUM Casio Watch Specifications Database

The catalog now contains **172 models, 112 modules and 2,294 source-backed candidate
facts**. It covers G-SHOCK, Pro Trek, historical Pathfinder, Oceanus, Lineage, Wave Ceptor, Standard,
Vintage, Databank, Sports, Dress, Edifice and Baby-G. All newly researched facts are pending
independent review. These coverage counts do not imply a complete Casio catalog.

## Try the private beta

Open **[SEPULKRUM Casio Specifications](https://sepulkrum-casio-specs-beta.miniatureagave.chatgpt.site)**
using the ChatGPT account that owns this Site. The hosted beta is owner-private.

The model prefix decoder works independently of catalog coverage, including
`GWG-B1000` / `GWGB1000` and segmented `PRW-S3100-1JF`. Its 57 family
references include the original decoder’s 53 entries, copied read-only from
[watch-code-decoder](https://github.com/SEPULKRUM/watch-code-decoder/tree/main/prefixes).
The PRW-S3100 Real Material/STN/black interpretation is labelled as the owner’s
established model-specific reference; it is not generalized to other S models.
Unknown modifiers and colors remain unresolved. The actual mountain/red-sun
emblem and black/red/silver branding come from that original project.

Search specifications by model, module or material; filter by family; open a model to inspect
physical specifications, separate module options and field-level sources.
Pending research, unknown measurements, unresolved module references and both
PAW2000 thickness claims remain explicit. The verified-only filter intentionally
returns no results until independently reviewed facts are available.

The bundled snapshot contains the current 172 models and 112 module profiles.
**Refresh data** fetches the latest catalog from this repository's main branch
without republishing the interface. If refresh fails, the bundled catalog stays
available. Download CSV exports the bundled spreadsheet snapshot. No visitor
input writes to the research database.

The interface source lives in `web/`. Package a local static copy with:

```sh
python build_web.py
node tests/web.test.mjs
```

The resulting `build/site` contains HTML, CSS, JavaScript, JSON and CSV with no
runtime package dependencies. Source checks cover search, family counts, shared
module references, both thickness claims, verified filtering and safe source
links. Deployment succeeded; interactive browser QA was unavailable in the
execution environment, so actual browser/device behavior still needs user testing.

## Use the database now

- [Spreadsheet / CSV](data/watches.csv): browse or download all model rows, with
  source links and pending/verified counts. Unknown values are blank.
- [Full JSON database](data/catalog.json): model and module records with evidence,
  uncertainty and status for every field; original legacy data is retained.
- [Coverage report](data/coverage.json): family counts, missing fields and unknown
  module links. There are 137 single-module references (one legacy association and
  136 pending references), plus 21 unresolved shared-manual or historical-listing candidate sets. No model now
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

### Clearer DSE and MTP case-back evidence

[Two follow-up photographs](research/caseback-clarifications-2026-11-14.json)
provide clear readings of **LCW-M100DSE / 5161** and **MTP-1302 / 2784**.
The first directly documents the stainless-steel DSE family, independently of the
earlier titanium LCW-M100TS picture. The second resolves the earlier cropped/faint
MTP reading. The original observations are retained as a historical record; these
clearer photographs resolve those specific evidence qualifications. Full colour
suffixes remain unshown, and catalogue values/statuses are unchanged.

## Module function enrichment

The next additive manual batch adds 31 pending facts to modules 3459, 3461,
3501 and 3569, including alarms, built-in world time, stopwatch, countdown timer,
lighting and power supply. See [the research notes](research/module-functions-2026-11-14.json).
The 3459/3461 guide explicitly names both modules; its common function facts do
not resolve which module an individual model uses. Stopwatch resolution changes
after the first hour on 3459/3461/3501 and is recorded in separate segments.
These additions preserve all earlier facts and owner-provided associations.

## Archived official Casio pages

The first Wayback batch adds three historical US product records: **GW7900B-1**,
**G2900F-1V** and **GW5600J-1**, with separate profiles for their explicitly named
modules **3200**, **2548** and **2924**. It adds 48 pending facts. The page captures
date from December 2019 and March 2013; capture dates are not release dates.
Exact displayed identifiers are retained without guessing regional suffixes.

[Research notes](research/archived-products-2026-11-14.json) retain selected technical
facts; [the discovery report](research/wayback-discovery-2026-11-14.json) records
availability results and exclusions. The GW6900-1 capture lacked detailed
specifications, and G9300-1 was excluded as a punctuation variant of existing
G-9300-1. Empty availability results do not prove that a product was never archived.
Unknown case material, glass and dimensions remain blank. In particular, no
length/width order was inferred from the old GW5600J-1 size string.

Each imported fact records the original official URL, exact Wayback replay URL,
14-digit capture timestamp, access date and SHA-256 of the retrieved replay HTML.
Full HTML files remain local build artifacts; the repository contains technical
notes and citations. Capture-specific facts remain pending independent review and
cannot overwrite existing verified facts or silently resolve later revisions.

Convert a reviewed batch offline using the same separation of model and module
facts as the live-source pipeline:

```sh
python archive_import.py research/archived-products-2026-11-14.json --output build/archived-candidates.json
python catalog.py build --check
```

The adapter detects duplicate and punctuation-variant models, requires explicit
module evidence, and rejects ambiguous source identities. Archive citations must
use a valid dated Wayback URL whose original is on the explicit official Casio
host allowlist; a third-party page inside an archive wrapper is rejected. The live
fetcher is unchanged; this adapter does not crawl Wayback or bypass live-site
access restrictions. Additional historical snapshots can be researched in batches
and supplied through the same JSON format.

### Second archive batch: Pro Trek, Edifice and G-SHOCK

The [second historical batch](research/archived-multiseries-2026-11-14.json) adds
76 pending facts across five exact displayed US identifiers and their explicitly
named modules:

| Model | Module | Capture date |
| --- | --- | --- |
| PRW3500-1 | 3414 | 2017-02-20 |
| EF527D-1AV | 4369 | 2014-12-26 |
| EQS500DB-1A1 | 5123 | 2014-12-18 |
| G9000-1V | 3031 | 2014-12-27 |
| G7710-1 | 3095 | 2012-08-28 |

The G9000-1V source labels its size/weight row **G9000MS**, so both measurements
are excluded. Module 3031 has two stopwatches; ST1's auto-start is not assumed
for ST2. Module 3095's lap and split display limits differ and are kept separate,
as are its two countdown timers. Unlabeled length/width order is not guessed.

The [discovery/retrieval report](research/wayback-multiseries-discovery-2026-11-14.json)
records the inspected captures. EFA120D-1AV and WV200A-1AV were excluded because
the retrieved pages lacked detailed specification sections. Pro Trek sensor
functions outside the current module schema are not imported in this batch.
All historical fields remain pending independent review.

### Third archive batch: Pathfinder and Wave Ceptor

The [third batch](research/archived-pathfinder-wave-ceptor-2026-11-14.json) adds
127 pending fields across eight exact US model identifiers. It introduces seven
module profiles and adds the missing radio-reception field to existing module
3414. Previous specifications remain unchanged. Pathfinder is retained as the
historical official series name.

| Model | Module | Capture date |
| --- | --- | --- |
| PAG240-1 | 3246 | 2011-10-26 |
| PAW1500-1V | 3134 | 2011-10-15 |
| PAW2000-1 | 3172 | 2011-10-19 |
| PRW3000-1A | 3414 | 2016-12-16 |
| WV58A-1AV | 3054 | 2013-01-01 |
| WV200A-1AV | 3140 | 2013-01-01 |
| WVA470J-1A | 5052 | 2013-01-01 |
| WVA430J-1A | 3311 | 2012-03-03 |

Older official navigation used the `wave_ceptor` URL category. Inspecting those
paths recovered the WV200A-1AV technical specifications absent from the later
capture in the second batch. The [discovery report](research/wayback-pathfinder-wave-ceptor-discovery-2026-11-14.json)
records both URL forms and retrieval outcomes.

Source qualifications remain explicit in the research notes: WVA470J-1A has
conflicting colour wording, so colour is omitted; PAW2000-1 advertises two
different thickness values, so dimensions are omitted. Variant weights use the
matching resin row rather than the metal-band row. WV58A-1AV's generic WV58
measurement row is not assigned to the more specific identifier. Module 3311's
stopwatch changes resolution after 60 seconds; modules 3054 and 3140 have different
countdown minimums (one minute and one second). These distinctions are preserved.

Radio-reception profiles retain named signals, frequencies in kHz and documented
receive limits. No radio function is inferred for solar-only PAG240-1. Sensor
functions outside the current schema remain unimported. All new facts remain
historical candidates awaiting independent review.

### Fourth archive batch: G-SHOCK and Baby-G

The [fourth batch](research/archived-gshock-babyg-2026-11-14.json) adds eight
models and 91 pending fields. Four exact module profiles are new; G7700-1 reuses
existing module 3095 without copying or duplicating its facts. Model weights
remain separate: G7700-1 is listed at 58 g, while existing G7710-1 is 56 g.

| Model | Module reference |
| --- | --- |
| G2300B-1V | 2184 |
| G2310R-1 | 3192 |
| G7700-1 | 3095 |
| BG169R-1 | 3189 / 3252 |
| BG5601-1 | 2994 |
| BG1006SA-1 | 3188 / 3288 |
| G100-1BV | 2327 / 5158 |
| G300-3AV | 3750 |

The paired references for BG169R-1, BG1006SA-1 and G100-1BV stay unresolved.
No first module is selected, and shared listing text is not copied into both
module profiles. At that batch stage, six candidate modules still needed module-specific research;
`candidate_module_ids_without_specs` now exposes that gap in the coverage report.
The existing `models_with_ambiguous_manual` key includes these historical
product-listing candidate sets as well as shared-manual references.

The archive adapter accepts `module_candidates` instead of `module_id` for these
listings, requires empty `module_specs`, and produces a model-only proposal.
An exact association can also omit repeated function facts when its module is
already present in the existing catalog; an unknown empty exact profile is
rejected. Both cases have regression tests.

Source qualifications: G2310R-1's measurement row is labeled G2300GR, so its
weight and dimensions are excluded. G2300B-1V has an explicitly described nylon
band and a 2039 calendar endpoint. G300-3AV retains its two SR927W batteries and
2039 calendar. BG1006SA weight uses its own row, not the neighboring BG1005M row.
The [discovery report](research/wayback-gshock-babyg-discovery-2026-11-14.json)
records inspected URLs and captures. All additions await independent review.

## Official manuals for the six paired-listing modules

The [paired-module manual batch](research/paired-module-manuals-2026-11-14.json)
adds 53 pending specification fields across **2327, 3188, 3189, 3252, 3288 and
5158**. Every candidate module now has a researched profile:
`candidate_module_ids_without_specs` is empty. This fills module information,
not exact watch-to-module assignments; the three archived paired references
remain unresolved, and model lookup shows both separate module options.

The official guides establish an important distinction: **2327** accepts dates
from **1995 through 2039**, whereas **5158** has an automatic calendar covering
**2000 through 2099**. Both stopwatch profiles retain the change from hundredths
to whole seconds after the first hour. The 2327 operation-only guide does not
provide accuracy or battery specifications, so those values remain unknown.

The guide headed 3189/3252 explicitly covers both modules; its common facts are
recorded separately for each. Modules 3188 and 3288 each use their own named
guide, including selectable illumination durations and the snooze alarm. No
function facts are inferred from the archived product listing. All previously
imported models, modules and legacy data remain unchanged. All additions require
independent review.

### Fifth archive batch: Sports, Databank and analog watches

The [fifth archive batch](research/archived-databank-sports-2026-11-14.json) and
[AMW module manuals](research/amw-module-manuals-2026-11-14.json) add six models,
seven module profiles and 81 pending fields. Historical Sports and Dress categories
are retained as Casio Sports and Casio Dress.

| Model | Module reference |
| --- | --- |
| AMW320R-1EV | 2701 / 5153 |
| AW80-1AV | 2747 |
| DB36-1AV | 2515 |
| MTP4500D-1AV | 4755 |
| EF503D-1AV | 2328 |
| DW9052-1V | 1659 |

AMW320R-1EV is a source-conflict case: the archived page claims a 24-hour
stopwatch, whereas the official guides for **both 2701 and 5153 specify
59 minutes 59.99 seconds**. The archived function claim is excluded. Both
manual-sourced module profiles are available, but the exact watch association
remains unresolved. The 2701 operation-only guide does not supply accuracy or
battery specifications. Module 5153's calendar fixes February at 28 days; no
leap-year-aware calendar is inferred.

DW9052-1V's archived accuracy symbol is corrupted, so accuracy is omitted. Its
stopwatch lists a change in resolution after one hour alongside a hundredths-based
capacity string; the resolution change is retained, but no maximum display value
is selected. The scanned official 1659 PDF was not transcribed in this batch.
MTP4500D-1AV's band is only described as **Metal**; no alloy or case material is
inferred, and its chronograph capacity remains unknown. DB36-1AV keeps its
historical 2039 calendar endpoint. AW80-1AV uses its resin-row weight rather
than metal or cloth variants.

The [discovery report](research/wayback-databank-sports-discovery-2026-11-14.json)
records archive timeouts separately from empty results. DB360-1A's retrieved
capture lacks detailed specifications and is excluded. All previous records are
unchanged; all new facts remain pending independent review.

## Supplied module 1659 manual clarification

The user-supplied scanned PDF has SHA-256
`8c35703b0de414c4b7fd2b76baa3e11ff2070f9682744b62e319b7148e883584`,
identical to a fresh download of Casio's official 1659 guide. Both rendered pages
were read visually; their text layer omits almost all operational content.
[Research notes](research/module-1659-manual-clarification-2026-11-14.json)
record the file identity and page locations without redistributing the PDF.

The guide resolves the stopwatch maximum at **23:59:59**, with hundredths for
the first 60 minutes and whole seconds thereafter. It also corrects the
countdown start minimum from the archived **one minute** to **one second**,
confirms the date-setting range **1995–2039**, and describes two-second EL
illumination with optional flashing alarm alerts. These replace only pending
function claims for module 1659. Superseded archive claims remain in the
research notes, outside the canonical import, to preserve the discrepancy trail.

The guide contains no accuracy or battery specification. Accuracy remains
unknown; the prior archive-sourced CR2016 claim remains separately attributed
and pending review. No model-specific case properties or module associations
are inferred from the general guide. All verified legacy data is unchanged.

## PAW2000 thickness: retain both Casio section values

As requested, PAW2000-1 now retains both values from the same archived official
Casio page, with their original section labels:

| Casio section | Thickness | Database / CSV field |
| --- | --- | --- |
| Promotional description: Slim Case Design | 11.5 mm | `promotional_thickness_mm` |
| Technical Specs: PAW2000 size/weight row | 11.3 mm | `technical_table_thickness_mm` |

The technical row reads `PAW2000 56.2 x 50.2 x 11.3mm / 69.1g`. Its full text
and the promotional wording are retained as source evidence in the
[research notes](research/paw2000-labeled-thickness-2026-11-14.json) and import.
Both fields are model-specific positive millimetre values with distinct source
locators and explicit discrepancy notes. Neither is chosen as a definitive
measurement; `dimensions_mm` remains unset for PAW2000-1 and its existing CSV
`thickness_mm` cell remains blank. The two labeled columns are included in the
CSV, so both claims are visible in spreadsheet use. All prior fields are unchanged.

## Modules 3261 and 3281: same functions, different LCD polarity

Following the owner's clarification, Casio's shared guide was checked directly.
Page E-3 explicitly distinguishes the displays:

| Module | LCD polarity | Casio description |
| --- | --- | --- |
| 3261 | Positive | Dark figures on a light background |
| 3281 | Negative | Light figures on a dark background |

The separate module profiles now include `display_polarity` and identical
shared function values transcribed from the guide's Specifications section.
[Research notes](research/module-3261-3281-display-2026-11-14.json) retain the
source, page locations and the distinction between display appearance and
functions. Existing accuracy/calendar facts are unchanged. `catalog.py show
G-9300-1` exposes both module options with their polarity, rather than hiding
the reason for the paired guide. The shared model reference itself is preserved;
a particular watch's module can be identified from model-specific evidence.
No modules are merged and no prior facts are overwritten. All new facts remain
pending independent review.

### Sixth archive batch: Riseman, Gulfman, Mudman, Aviation and Pathfinder

The [sixth batch](research/archived-master-g-pathfinder-2026-11-14.json) adds
five models, four module profiles and 78 pending fields.

| Model | Module |
| --- | --- |
| GW9200-1 | 3147 |
| GW9100-1 | 3089 |
| G9000MS-1 | 3031 |
| PAG80-1V | 2894 |
| GW2500-1A | 5064 |

G9000MS-1's official description explicitly specifies a light-on-dark LCD.
`display_polarity` is therefore also permitted at model scope, where this
negative display belongs; the shared module 3031 profile remains unchanged.
The prior 3261/3281 module-level polarity facts are retained because Casio
explicitly distinguishes those module numbers by display polarity. Model-specific
appearance is never copied to every watch sharing a module.

The G9000MS measurement row matches this model and supports 56 g, but its
capture lacks an explicit model-specific water-resistance rating. No rating is
copied from G9000-1V. Titanium case backs/pins on GW9100-1 do not establish
titanium case material. GW9200-1 retains its source's 33-city/29-zone count;
PAG80-1V uses the 78 g resin row, not the 118 g titanium variant. PAG80's
stopwatch maximum is 9:59:59.99, while GW9100's is 999:59:59.99. GW9100's
countdown measurement unit is 0.1 second. These values remain separate.

The [discovery report](research/wayback-master-g-pathfinder-discovery-2026-11-14.json)
retains empty archive results and API timeouts as separate outcomes. Sensor
fields outside the current schema remain unimported. All previous records are
unchanged, and all new facts await independent review.

## Current official G9000MS-1 specifications fill the archive gaps

The user supplied the [current official Casio page](https://www.casio.com/us/watches/gshock/product.G-9000MS-1/),
whose embedded product specification component explicitly supplies:

- Case size **52 × 46.3 × 16.3 mm**, with L/W/H order labeled.
- Case and bezel material **Resin**.
- Glass **Mineral Glass**.
- Water resistance **200 meters**.

These add five pending model fields, including the descriptive and numeric water
ratings. Weight **56 g** and resin band corroborate existing values and are
retained in the [research notes](research/g9000ms-current-official-2026-11-14.json)
without duplicate imports. The archived capture genuinely lacked an explicit
water rating; its historical notes are preserved, while the current official
source now fills that gap. Existing negative LCD, module 3031 reference and all
prior facts remain unchanged.

The current page's structured Product specificationsItemList was inspected because
text-only page retrieval omits the rendered specification component. Its HTML
checksum and selected exact labels are recorded. The generic series fact is
listed under excluded_existing_fields in the notes to avoid importing it twice;
regeneration uses product_import.convert followed by that explicit exclusion.

## Bulk current-page gap filling

A [seven-model batch](research/current-official-gap-fill-2026-11-14.json) adds
27 missing model fields from current official Casio pages: GW7900B-1, G2310R-1,
G2900F-1V, DW9052-1V, AW80-1AV, DB36-1AV and PRW3500-1. These fill explicitly
labeled dimensions, weights, case/bezel materials, band materials and glass
where previously unknown. No prior fact or provenance is replaced. G2310R-1
now has a correctly identified official size/weight source, separate from the
old archive's mislabeled G2300GR row.

`product_import.py` now supports the Product `specificationsItemList` JSON
embedded in official HTML, in addition to existing visible specification headings.
It does not execute JavaScript. It requires the displayed model and product URL
to agree (including regional suffix), rejects malformed or duplicated JSON keys,
and fails on conflicting specification components or visible/embedded values.
`from_snapshots` can therefore use these current pages through the existing
checksum-checked bulk workflow. Original research imports reproduce unchanged.

Explicit per-product `excluded_existing_fields` record which already-known
fields were omitted from the additive batch. Reproduction uses
`product_import.convert` followed by those exclusions. Optional
`field_uncertainty` notes retain source discrepancies on the affected fields.

The [fetch and comparison report](research/current-official-gap-fill-report-2026-11-14.json)
records seven successful source imports and one missing BG169R endpoint.
AW80 and DB36 current dimensions differ from old unlabeled size rows; raw
historical rows and source links remain recorded, and the new dimension facts
explicitly flag historical revision/source-error uncertainty. DB36 current
weight is **27 g**, versus the archived **30 g**. The existing 30 g candidate
is preserved, with the competing current claim retained in research for review.
These claims are not silently combined into one production specification.
All 27 additions remain pending independent review.

### Second current-page gap-fill batch

The [second additive batch](research/current-official-gap-fill-second-2026-11-14.json)
adds 20 missing model fields from current official Casio pages for EF527D-1AV,
WV200A-1AV, WV58A-1AV, G9000-1V, PRW3000-1A and MTP4500D-1AV. No previous
values or source evidence are replaced. In particular, the current G9000-1V page
provides correctly identified size/weight facts, separate from the archived
G9000MS-labeled row that was previously excluded.

WV200A's current page lists **58 g**, while its archived candidate is **40 g**.
The existing 40 g remains unchanged; the competing 58 g claim is recorded for
review. Its current explicit dimensions also differ from the archived size row.
WV58A's current dimensions differ from the older generic WV58 rows; both raw
readings are retained and its new dimensions carry a discrepancy annotation.
These current measurements are not asserted to describe every historical revision.

The current MTP4500D page adds stainless-steel specificity beyond the earlier
**Metal** band wording. Existing band data stays unchanged; the new description
is retained as additional specificity, not classified as a contradiction.
Likewise, Mineral versus Mineral Glass is classified as wording only. The
[comparison report](research/current-official-gap-fill-second-report-2026-11-14.json)
distinguishes these from the numerical weight discrepancy and records four
404 endpoints. Per-product exclusions reproduce the additive import without
duplicate existing facts. All 20 additions remain pending independent review.

## Edifice and Baby-G coverage expansion

The [current official product batch](research/edifice-babyg-products-2026-11-15.json)
adds five models and four separately researched module profiles, totaling 73
pending facts. Edifice coverage rises from four to **six** models; Baby-G rises
from four to **seven**.

| Exact displayed model | Series | Current manual selector |
| --- | --- | --- |
| EFB108D-1AV | Edifice | 5664 |
| EFSS570D-1A | Edifice | 5634 |
| BGD565-1 | Baby-G | 3489 |
| BGD565-7 | Baby-G | 3489 |
| BA110-1A | Baby-G | 5338 |

Each exact-model page embeds an official manual selector explicitly naming its
module; the selector strings, page checksum and page URL are retained in the
notes. These are current official references, not proof of all historical
production revisions. In particular, the BGD565 product selectors explicitly
name 3489. Its shared guide also covers 3229/3421, which does not establish
that those modules were fitted to either BGD565 variant.

The [module research](research/edifice-babyg-manuals-2026-11-15.json) keeps
module-specific distinctions: 3489 uses **CR1616**, not the **CR2016** row for
3229/3421; 5338 uses **two SR726W** batteries. The analog date mechanisms
5664/5634 use a 31-day month and need manual shorter-month adjustment, rather
than a full automatic calendar. Module 5634's one-second chronograph stops at
60 minutes; model sapphire glass and water ratings remain separate from functions.

The [discovery report](research/edifice-babyg-discovery-report-2026-11-15.json)
records five usable pages and five 404 endpoints, without substituting similar
models. All previous model/module records and verified legacy data are unchanged.
All new facts remain pending independent review.

## Square G-SHOCK priority batch · 15 November 2026

Research now prioritizes GW-M5610, GW-M5610U, GW-5000 and GW-5000U in that
order, followed by further important G-SHOCK families and regional Casio
bestsellers. See [collection priorities](docs/collection-priorities.md).

The first pass checked 28 exact product URLs, extracted specifications from 16,
and added 14 models plus 170 fields. Original module 3159 now has a separate
9-field official-manual profile; U/UBC and current HS references retain module
3495. Existing model facts are excluded from replacement. Case, band, mass,
color and release metadata are researched separately for each exact variant.
Japanese-market labels and official image references remain in the research
notes; no third-party images were copied or displayed.

This is not an exhaustive family inventory: 12 product URLs remain unavailable
and further historical discovery is needed. CasioPart returned 403, including
its robots.txt, so its listings were not collected. Casio regional bestseller
pages are confirmed, but no numeric sales rankings were inferred.
