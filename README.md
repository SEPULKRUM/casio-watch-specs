# SEPULKRUM Casio Watch Specifications Database

Bulk research and source-backed proposals for G-SHOCK, Pro Trek, Oceanus, Lineage,
Wave Ceptor and other Casio watches. No model-by-model entry is required: tools
accept lists of URLs, document manifests and arrays of candidate records.

## Existing files stay protected

`watches.json` is the original, authoritative legacy dataset. No new command edits
it. The existing `collector.py`, `sources.txt` and collection workflow are retained.
The legacy mixed feature list is preserved verbatim, not guessed into module facts.
`build/catalog.json` is a **proposal**, not a replacement for verified data.

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
series, release date and source-backed `module_id`. Module facts include accuracy, power, alarm, world time,
stopwatch, timer and calendar functions. The validator rejects unknown or wrongly
scoped fields. Values must retain units in the field name or structured value;
module behavior must not be used to infer case properties.

See [the starter module batch](imports/module-3495.json) for a complete example.
It contains seven facts researched from Casio's module 3495 specifications page,
all pending review. It adds no guessed watches and does not independently verify
the legacy model/module association.

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

The separate validation workflow runs offline tests and builds the proposal as an
artifact. The existing daily collector workflow remains intact. This change does
not yet crawl catalogs automatically, extract every manual layout, or claim large
watch coverage. It supplies a tested batch pipeline for subsequent research.

Only `SEPULKRUM/casio-watch-specs` is in scope. The watch-code-decoder repository
is unrelated and is not accessed or modified.
