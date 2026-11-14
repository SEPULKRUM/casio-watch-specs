# SEPULKRUM Casio Watch Specifications Database

The catalog now contains **41 models, 3 modules and 342 source-backed candidate
facts**. It covers G-SHOCK, Pro Trek, Oceanus, Lineage, Wave Ceptor, Standard,
Vintage, Databank, Edifice and Baby-G. All newly researched facts are pending
independent review. These coverage counts do not imply a complete Casio catalog.

## Use the database now

- [Spreadsheet / CSV](data/watches.csv): browse or download all model rows, with
  source links and pending/verified counts. Unknown values are blank.
- [Full JSON database](data/catalog.json): model and module records with evidence,
  uncertainty and status for every field; original legacy data is retained.
- [Coverage report](data/coverage.json): family counts, missing fields and unknown
  module links. At this stage 39 models lack a confirmed module association.

Download/clone this repository, then use Python 3.10 or newer; no Python packages
are required for catalog use:

```sh
python catalog.py search --series "Oceanus"
python catalog.py search "titanium"
python catalog.py show GA-B2100-1A
python catalog.py coverage
python catalog.py build
```

`show` returns model and linked module separately. `search --verified-only`
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
Each source needs HTTPS `url`, ISO `accessed` date, `locator` (page or section),
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
