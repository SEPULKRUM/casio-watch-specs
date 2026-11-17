# Model-specific prefix blocks

The 2026 master already supplied segmented model-code interpretations, but the interface added them only as guide notes. The visible token blocks still used the generic parser, combining numeric series and edition suffixes (for example, 240EAC).

`scoped-breakdown.mjs` validates each supplied tokenization against the complete exact model reference before using its segments. Both supplied schemas and the explicit component-list fallback are supported. AQ-240EAC-3A becomes AQ / 240 / EAC / 3A, with EAC linked to the source's A.P.C. collaboration association; no literal expansion of E, A or C is invented. Documented regional references append their market token. Base-reference queries use only complete source segment boundaries and identify the documented example. Unrelated model families and unsupported partial strings do not inherit these interpretations.

Both the earlier worldwide source and the revised 2026 master can provide scoped blocks; the current master takes precedence. Invalid tokenizations retain the existing decoder and source notes. Whole family codes remain together. Source-specific uncertainty remains explicit.

Tests reconstruct all 203 current master codes, exercise the screenshot's full, compact, base and regional queries, and reject invalid source splits and unrelated model-number matches. Model identities, physical facts, module profiles and counts are unchanged.
