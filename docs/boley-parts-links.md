# Boley parts links and supplier module observations

Boley's public Casio case-parts sitemap is a model discovery source. The site is an independent supplier, not official Casio specification evidence. Links lead to Boley's own part-number listings; the application does not republish its parts tables, images, prices, stock or availability.

## Exact model matching

Read `https://boley.de/robots.txt` before collection. The rules retrieved on 15 November 2026 permit the public sitemap and case-parts listings but disallow search queries and account paths. The collector uses sitemap listing URLs, never the prohibited search endpoints. It refuses redirects, checks robots for each listing and stops the batch on 401/403/429.

The Casio sitemap contains model-specific numeric listing IDs. Match only unambiguous exact identifiers (allowing hyphen formatting differences), then verify the fetched page's Casio model heading against both the catalog model and URL slug. Never remove regional suffixes, substitute a sibling variant, or invent a numeric listing ID. Missing listings stay unlinked; the UI offers a clearly labelled general Casio directory link.

`data/parts-links.json` is separate from `data/catalog.json`. Each checked link retains the listed model, URL, retrieval date and page checksum. Discovery candidates and unavailable/ambiguous listings are explicitly recorded. The link UI loads independently, so a failed parts-file fetch does not block watch specifications. Refresh requests the latest parts links alongside the catalog and retains a working snapshot if the remote parts request fails.

## QW references

Capture explicit QW codes from the model's listing tables, including forms such as `QW3159-01`, `QW-1556-05` and `QW-2327YC-03TK`. Preserve the entire supplier code. Extract only the 3–4 digit core as a module observation; letters and trailing assembly codes do not establish module functionality, display polarity or compatibility. Do not infer what `-01` means or equate it with an official manual revision.

Compare supplier module observations with the catalog's recorded reference. Agreement is corroboration, not independent verification. Disagreement is flagged for review; no official model/module assignment or verified fact is replaced. Module observations on models absent from the catalog remain discovery leads until researched.

## Reproduce

Download the public Casio sitemap to a local snapshot, then run:

```sh
python parts_links.py discover --sitemap /tmp/boley-casio-sitemap.xml --output research/boley-discovery-2026-11-15.json
python parts_links.py collect --manifest research/boley-discovery-2026-11-15.json --output data/parts-links.json
python -m unittest discover -s tests -q
node tests/web.test.mjs
python build_web.py
```

Collection is explicit and rate-limited, and saves local snapshots under `build/boley-snapshots` for parser review. Inspect link failures and QW disagreements before proposing a branch/PR. Site publication retains the existing audience.
