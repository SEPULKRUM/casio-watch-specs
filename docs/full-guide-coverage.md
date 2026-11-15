# Multi-line guide coverage

The supplied five-page **Casio Multi-Line Model Reference Guide v3** is secondary evidence. The decoder presents its readings as guide / community interpretations, never as an official universal Casio acronym key. The original PDF and artwork are not distributed.

| PDF page | Implemented information | Location |
| --- | --- | --- |
| 1 | Family, base series, material / feature, colour, variation and market structure; LCW-M100TSE-1AJF, MDV-106B-2AV, MTP-E735AR-2A2V, CMK-100TCC-8AER | Decoder segments and interpretation rules |
| 2 | WV/WVA/WVQ radio reception, transmitter systems, case options; LCW/LIW/LIN Lineage trims and examples; BG/BGA/BGD/BGS/BLX/MSG traits and examples | Whole-prefix meanings and contextual guide notes |
| 3 | Classic F/A/W/LA/CA/DB/DBC/MQ/LQ examples; AE/AEQ examples, battery, alarm and world-time tendencies; MDV106/107 emblem, colourways, construction and module claims | Whole-prefix meanings and contextual guide notes |
| 4 | MTP/LTP and V00x/13xx/B1xx/E3xx/E7xx/S1xx associations; E735AR dial, dimensions, module, battery and five colourways; CMK100 five launch configurations, dimensions and movement claims | Scoped series / suffix rules and contextual guide notes |
| 5 | D/T/L/B/C/G/V/E/AR context; all nine colour digits; shade / order markers; JF/J/CR/ER/V/VER/DR/DF markets | Decoder rules panel and applicable result segments |

`web/guide-interpretations.mjs` holds selected factual notes and position-specific rules. `web/prefix-meanings.mjs` supplies whole-prefix meanings. Prefixes remain grouped: AE is not displayed as separate A and E cards.

Important scope limits:

- A feature associated with a family is not automatically a specification of every member. Water resistance, solar power, reception systems, materials, alarms and battery types require exact-model evidence.
- The guide's MDV106/107 construction claims do not apply to MDV10, whose Casio page specifies 50 m. No ISO certification is inferred.
- A guide suggestion of 30 m for MTP-V00x does not convert a generic Water Resistant marking into a numeric rating.
- TCC has two contextual C readings; pre-hyphen V differs from trailing export V; B is not automatically Bluetooth or negative LCD.
- CMK's late-2026 launch and the MTP-E735AR-2A2V physical specifications were checked previously against primary pages, recorded in `research/guide-v3-review-2026-11-15.json`. Other guide claims remain labelled secondary information.
- Family numbers, colour codes and source references do not establish movement modules. The verified specification catalog is unchanged by these interpretation rules.

Additional owner-requested rule: D in GWF-D1000 is presented as a community depth / diving-sensor association, separately from the guide's bracelet-D reading.
