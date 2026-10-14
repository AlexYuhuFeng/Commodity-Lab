# ADR 0003 — validated packs and domain dispatch

Accepted for M2A, 2026-10-09.

Add typed commodity-neutral reviewed scenario contracts and a registry around the local session engine. Keep the M1 gas engine and API payloads compatible; dispatch saved states by immutable version. Crude procurement and merchant-inventory packs share one financial/decision engine, with distinct physical cash-flow contracts and hedge directions.

Each pack carries commodity, unit, currency, delivery month, pricing window, settlement date, fixed physical terms and dated synthetic fixings. Validate structural and financial consistency before registration. Only registered versions can start sessions; no client or AI upload endpoint can publish a pack. AI coaching sees the same checkpoint-bounded evidence as the learner and has no grading, pricing or execution authority.

Historical inventory acquisition is a dated ledger entry. Lifecycle trading margin includes it, while final-settlement net cash excludes it. Monetary limits have explicit currency. A benchmark swap hedges the benchmark only: grade differential and freight remain visible exposures.

Alternatives rejected: cloning the gas engine per commodity (drifting policy/state logic), silently renaming EUR/MWh fields for crude (broken units and API), treating historical purchases as final cash payments (incorrect liquidity), and unrestricted AI packs (unreviewed numerical models). Gas migration into the neutral schema is deferred behind compatibility evidence rather than forced into this change.
