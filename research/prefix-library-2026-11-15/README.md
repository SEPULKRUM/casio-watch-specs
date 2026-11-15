# Extracted prefix and model-reference library

This intake extracts **identifiers**, not new specification records, from the supplied research ZIP and the six supplied PDFs (219 compilation pages). It adds 72 prefix patterns to the existing 57, producing **129 prefix patterns**. New entries carry either secondary-source or unverified status; none introduces an official letter expansion.

The deduplicated library contains **2,325 model/series strings**:

- **58 index-checked identifiers:** selected IDs visually checked in compilation index pages 2–4. These remain secondary observations; underlying advertisements, exact variants and features are not thereby verified.
- **155 supplied transcriptions:** retained from the handoff's watch records without a matching checked index observation. Their standalone originals were not received; compilation pagination is not assumed equivalent.
- **2,112 machine candidates:** earlier mention-index results, OCR candidates and automatically extracted research-note examples. These can include series-only, truncated, misread or nonexistent model strings and remain explicitly unverified.

The supplied watch-record file contains 162 distinct strings; some overlap the checked IDs. A final pass also extracts explicit model examples from the ZIP notes, adding seven strings not found elsewhere. The earlier mention index contains 1,691 distinct strings; overlaps with the other inputs are deduplicated by exact identifier. Punctuation variants and regional suffixes are retained separately; compact searching can return multiple matches. A source title containing “verified” does not establish verification: all such underlying dossiers remain unavailable and unverified here.

The extractor rejects 189 **occurrences**, not necessarily 189 distinct models, for malformed/unresolved readings or possible battery/OCR noise. Battery-like OCR prefixes are excluded. Suspicious but syntactically plausible strings remain visibly flagged candidates, not established models. Arbitrary OCR-only prefixes are not automatically activated: new prefix entries require a checked index observation, supplied watch transcription, earlier indexed research reference or explicit model example in a research note.

Every retained observation points to its source filename and declared page. For the six received PDFs it also preserves compilation page and uploaded-part local page. Original source filenames/checksums are provenance only; neither their page claims nor prior “verified” filenames are promoted to independent verification.

## Behaviour

Search the model-reference library from the decoder input; it is separate from the specification table. Matching rows show review status and page references. The JSON download contains all identifiers and provenance. Exact research matches also show their review status in the decoder, outside the expandable library.

Numeric-leading identifiers such as `110QS-37B` remain historical references with no invented alphabetical prefix or module mapping. Historical GM, GMW, GD, GG and BA references do not inherit modern G-SHOCK/BABY-G family features. Unknown letter meanings stay unverified, and historical reference-only identifiers do not receive generic colour-code guesses.

The **195-model, 113-module, 2,496-field specification catalog is unchanged**. Library string counts must never be advertised as verified watch counts. Existing scope-specific GW-M5610U parsing and specification filters remain intact.

## Rebuild

With the private extracted intake available locally:

```sh
python reference_import.py --intake /path/to/local/intake
```

The intake requires the handoff JSON/JSONL, received-source summary and OCR page registry prepared earlier. The generated public files are `data/model-references.json` and `web/research-prefix-data.mjs`. The public regression tests can validate source linkage, generated prefix entries and candidate boundaries without the private originals.

Only model identifiers, source filenames/checksums, page references, review labels and original explanatory notes are published. No source PDFs, photographs, OCR transcripts, original handoff tables, prices or advertising prose are included. This is a newly deduplicated factual identifier index, not republication of the uploaded research bundle.
