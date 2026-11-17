# Supplied Casio catalog: extraction and application

The supplied `1983 Casio catalog .zip` contains 24 JPEG images, all visually inspected. The catalog code is **CT0583E**. The supplied year remains an attribution; no publication or model-release date is inferred from the code.

- 78 distinct printed watch references, observed 82 times including four packaging repeats.
- 29 separately stored module profiles.
- Five clocks, separately categorized and excluded from watch counts.
- Dial-availability footnotes retained without inventing variant identifiers.
- A general battery-service summary, packaging mappings and seven source-scope/discrepancy notes retained.

Technical transcription: `research/supplied-casio-1983-catalog-2026-11-17.json`.
Reproducible conversion: `supplied_catalog_import.py`; its import proposal and bounded browser addendum are generated from that transcription. No source images, EXIF, original ZIP, advertisements or contact information are published.

Facts remain pending independent verification. Five scalar claims differ from earlier main values. The application plan preserves those earlier values and retains every incoming claim in `catalog_1983_evidence`; nothing is silently overwritten. All model material/water-resistance claims remain separate from module functions. Clock H/W/D measurements retain their original coordinate meaning. Generic captions do not establish band, crystal, alloy or case dimensions.

The beta uses the rebuilt full catalog and unified index. Production validates its existing base catalog/index/report, composes the source addendum, checks every source identifier and category, and recalculates reconciliation counts. The composite report records both input checksums; it does not claim the old base-index file is the composed index. Existing reviewed fields are preserved. Re-importing the already integrated source does not double-count it.

Reproduce:

```sh
python supplied_catalog_import.py research/supplied-casio-1983-catalog-2026-11-17.json --output imports/zzzzzzzzzzzzzzzzzzzzzzzzzz-supplied-catalog-1983-2026-11-17.json --web-output web/catalog-1983-data.mjs
python catalog.py build
python -m unittest discover -s tests
for test in tests/*.test.mjs; do node "$test"; done
```
