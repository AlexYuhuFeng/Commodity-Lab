# ADR 0001 — deterministic training slice in the desktop monolith

Accepted for M1, 2026-10-09.

Keep Tauri/React/FastAPI and all legacy endpoints. Add typed versioned contracts, pure Decimal financial/policy functions, a separate API router and local SQLite session storage. Capture policy and decision-time facts atomically. The server selects the next checkpoint; learner and AI receive only visible facts. No client prices or scores are accepted.

Cash-settled synthetic TTF swaps use MWh not exchange lots. Purchases settle against the final monthly TTF index plus basis; swap cash flows use signed quantity times final index minus entry quote. A resize is an incremental trade at the current quote. Margin is a simplified collateral estimate, labelled as such. Arithmetic rounds final amounts to cents, not intermediate quantities/prices.

A rubric of structured diagnostic choices gathers provisional evidence without grading free text automatically. AI is optional, visibly ungraded, and cannot mutate the simulation. Human judgment and repeated cases are necessary for mastery.

Alternatives rejected: reuse legacy profit score (wrong incentive), trust AI settlement (not reproducible), client-state replay (allows future selection/tampering), replace desktop/microservices (unnecessary migration risk). SQLite supports restart and atomic stale-request rejection; it is not enterprise multiuser storage. No generic derivatives library is claimed validated by this slice.
