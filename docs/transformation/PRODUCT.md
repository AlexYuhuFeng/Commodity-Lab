# Commodity Lab transformation — milestone 1

Status: implementation baseline, 2026-10-09. Training only; no execution connectivity.

## Requirements and boundaries

All scenarios place the learner on a **trading-company desk**, never in a utility-company role. Gas uses physical sourcing and customer-sales margin management; future crude cases cover profit-oriented cargo trading and refinery procurement mandates. Emission-credit trading is a future domain requiring validated models and curriculum. Financial outcomes measure trading economics separately from decision quality.
Serve new hires, commercial traders, risk managers and instructors through demonstrated competence. Assess commercial judgment separately from policy, hedge performance and realized outcome. Preserve React/Tauri, FastAPI, existing gas/crude lessons, replay, settings and releases.

The first complete workflow is a synthetic European gas procurement exposure: a gas trading company buys November 2026 gas at TTF monthly index plus regional basis to fulfill industrial-customer sales at a fixed €60/MWh, with nominated volume up to 10,000 MWh. Two sequential hedge decisions precede settlement; nominations decline at the second checkpoint. Learners can hold, partially hedge or increase coverage, explain reasoning and answer diagnostic questions. Long cash-settled TTF training swaps hedge price increases; they do not hedge regional basis. No exchange contract sizing or live authorization is implied.

Policy profiles are immutable session snapshots, versioned and illustrative. Corporate defaults: 80% of eligible matching physical MWh, no naked paper, swaps only, approval above a configurable ratio. Academy and advanced lab are separate simulation environments, still constrained by implemented instrument models. Failed proposals are reviewable but do not execute or advance the checkpoint. Existing positions are rechecked after physical changes.

Settlement and cash-flow arithmetic use Decimal. Store decision-time evidence, policy, rubric version and rationale on the server; no future observations in learner or AI payloads. AI can coach from these records but cannot calculate, change grades, change positions or generate executable markets. An explicit offline coach supports operation without credentials.

## Six cooperating capabilities
A modular monolith is sufficient. Curriculum owns a commodity-neutral prerequisite graph and evidence-based remediation; scenario owns versioned reviewed packs and visibility; finance owns explicit units/currency/periods and cash flows; policy owns profiles and cumulative eligibility; assessment owns reviewed diagnostic rubrics; AI owns ungraded coaching. React owns presentation; FastAPI owns orchestration; SQLite owns local durable sessions. Legacy adapters remain available, with migration behind regression gates.

Curriculum foundation: fundamentals → physical exposure → derivatives → pricing/hedging → basis → portfolio/liquidity → operations → advanced strategies. This slice gathers diagnostic evidence for exposure, basis and liquidity; one case never establishes professional mastery. Future mastery requires repeated independent assessments and instructor-reviewed reasoning.

## Roadmap
1. M1: gas procurement, sequential decisions, durable audit, bilingual workflow, numerical and visual evidence.
2. M2: reviewed crude cargo financial model; commodity-neutral scenario schemas; learner identity and repeated competency evidence; instructor review/export.
3. M3: portfolio aggregation, actual policy document mapping and approvals, exchange margin/contract conventions, scenario authoring and validated AI variation.
4. M4: licensed replay/data entitlement review, enterprise access control, competency analytics and deployment qualification.

## High-risk decisions
- Hedge direction and physical sign: purchase cash flow is negative; long swap receipts offset rising index costs.
- Volume changes: eligibility uses the current nomination, not inception volume; old hedges remain until explicitly resized.
- Basis: unhedged basis must remain visible, even when index risk is fully hedged.
- Liquidity: simplified initial margin plus negative mark-to-market is an educational collateral estimate, not clearing-house margin.
- Information boundaries: server state advances only after a valid decision; no client-selected checkpoint or settlement price.
- Assessment: structured diagnostics are provisional evidence; prose quality requires human review. No grade for fortunate price moves.
- AI/data: existing provider integration is reused only for optional coaching; no real provider or entitlement is assumed verified.

## Acceptance of the vertical slice
An offline learner can start, inspect current facts, configure a profile, submit two defensible decisions, see separate assessment and final cash flows, resume after restart, and request optional AI coaching. Tests independently derive numerical examples and cover invalid inputs, policy breaches, duplicate/stale submissions and leakage. Existing backend/frontend regressions pass. Desktop packaging remains preserved and explicitly unverified unless executed.

## Interactive handbook direction (2026-10-14)

Extend the existing product with written business-model knowledge and chapter-bound generative interaction. Universal knowledge/card contracts, initial European gas and crude collections. Preserve courses, existing generative AI practice, simulations, profile tracking, Workbench/replay and desktop architecture. AI assembles approved learning components; engines retain numerical authority. Editorial draft chapters cover hub supply, beach-to-hub, LNG regas, refinery procurement and owned inventory. Beach/regas arithmetic is introductory, not a full validated market simulator. See ADR 0004 and `docs/handbook` for acceptance, scope and verification; HB backlog items separate engineering completion from domain/provider qualification.
