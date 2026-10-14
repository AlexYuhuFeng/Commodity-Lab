# DeepSeek live qualification — 2026-10-14

User requested actual LLM testing after seeing the offline regression screenshots. A supplied credential was stored in a private, permission-restricted app configuration outside the repository. No credential value appears in source, test fixtures, screenshots, evidence or this document. The local test backend uses existing DeepSeek settings; production/account credentials were not changed.

## Connection and fixes

Actual authenticated `GET /models` succeeded and advertised `deepseek-flash` and `deepseek-v4-pro`. The existing saved/UI alias `deepseek-v4-flash` incorrectly resolved to a public API model of the same name. It now resolves to **deepseek-flash**. Saved settings/internal aliases remain compatible; Haineng routing is unchanged. Only Flash was completion-tested.

The first real handbook reply was verbose and repeated card content. Its prompt now requests concise prose and uses cards for detail. Live legacy tutoring also exposed incorrect inference of MMBtu from the old exposure field and risk IDs used as chapter citations. Handbook-linked coaching no longer infers unknown quantity units, and the generic coaching API requests/validates a structured answer with registered chapter references before exposing text. Unsupported citations produce an explicit validation failure, not a fabricated source. Existing non-handbook requests keep their previous response contract.

## Actual live results

Seven real completions, plus one authenticated model-list request. No provider mocks in these probes. Times are individual observations, not a performance SLA.

| Probe | Observed result | Seconds |
| --- | --- | ---: |
| Initial English gas handbook | Long procurement hedge, residual risks, four valid card types and references; too verbose, subsequently tightened | 7.68 |
| English gas browser conversation | Concise margin/long-hedge explanation, comparison and risk-map cards; correct source anchors | 3.06 |
| Chinese owned-inventory browser conversation | Short hedge, historical cost versus settlement cash; explicitly refused unavailable next Brent price; requested practice delivered | 2.66 |
| Beach-to-hub streaming generation | 1,770 model-delta events; normalized case, matching chapter/session metadata and trading-company role | 8.63 |
| Initial legacy tutor | Transport versus price risk discussed, but exposed unit/citation issues; **not accepted** | 4.45 |
| First tutor correction | Numeric unit inference removed; some invalid inline risk references remained; **not accepted as reference-qualified** | 4.46 |
| Structured-reference tutor retest | API reference validation passed; correct symbolic margin/capacity distinction, no numeric MMBtu assertion | 4.13 |

The Chinese generated exercise was checked independently from its public inputs: quantity 11,500 bbl, benchmark entry 95, settlement 88, physical basis 1, historic acquisition 77, freight 2, short paper 9,200. Lifecycle margin = 11,500×(88+1−77−2) − 9,200×(88−95) = **USD 179,400**. Server grading passed and feedback resumed in the real UI. The question is a separate synthetic practice variant, not a forecast or settlement of the attached market scenario.

## Real application evidence

[English gas, AI online](evidence/deepseek-online-gas-en.png) and [Chinese inventory, AI online with persisted checked feedback](evidence/deepseek-online-inventory-zh.png). Both inspected; no mocked provider responses or status manipulation. The online indication corresponds to actual successful API requests. Previous offline screenshots remain deliberate reproducible regression evidence.

Transient live reports are `/workspace/scratch/commodity-live-*.json` and `.log`. The validated legacy API also returns `handbook_references`; UI continues to receive the existing plain answer field. The model cannot determine financial grading or edit positions.

## Remaining limits

This is a small functional/domain smoke, not proof of general reasoning quality, factual reliability, jailbreak resistance, availability, long-session performance or robust evaluation across all chapters. Pro was not tested. External editorial/domain sign-off, full LNG/route modeling, repeated instructor evidence and desktop bundles remain pending.

Legacy AI case quantities/conventions remain exploratory and are not promoted to reviewed financial contracts. When quantity units are unknown, coaching stays symbolic rather than inventing conversion. SSE advisor/live-assistant schemas still have their existing contracts; the additional strict citation schema applies to handbook-linked generic coaching. Reviewed Risk Lab calculations and checked numerical practice remain deterministic.
