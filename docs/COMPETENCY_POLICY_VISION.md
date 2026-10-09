# Commodity Lab — Competency and Policy Foundation

**Status:** exploratory design; no change to the current application UX or release behavior.

## Product direction

Commodity Lab serves new hires and experienced commercial staff using a common simulation engine and differentiated learning paths. Success is evidenced by better decisions under uncertainty, not by realized simulated PnL alone.

The first three learning environments are:

1. **Corporate compliance:** teach the organization's actual versioned policies, including approvals and instrument eligibility.
2. **Professional academy:** teach broader trading and risk-management capabilities without presenting hypothetical permissions as corporate authorization.
3. **Advanced strategy laboratory:** compare counterfactual strategies and policy constraints under clear simulated assumptions.

A training profile must never be used to authorize a live order.

## Boundary between engines

- **Market/scenario engine:** generates or replays time-consistent market states and information checkpoints.
- **Financial simulation engine:** independently computes positions, cash flow, PnL, hedge effectiveness and liquidity impact.
- **Training policy engine:** evaluates configured limits, separately from financial outcome and teaching score.
- **Assessment engine:** records decision-time evidence, risk recognition, reasoning and control adherence; grades against reviewed rubrics.
- **AI coach:** explains decisions, generates variants and chooses practice content; it may not invent numerical results or grant permissions.

## First vertical slice: hedging policy

A deliberately narrow reference implementation is in `core/training_policy.py`. It checks an illustrative 80% paper-versus-eligible-physical quantity limit, physical backing and prohibited options. It offers a more permissive **simulated** academy policy. It does *not* determine real compliance.

**Important:** The user's description of an 80% limit is insufficient to implement a real corporate rule. Before real policy training, determine which physical positions qualify, whether buying and selling offsets are netted, contract tenor, portfolio grouping, units, pre-existing hedges, exemptions and approval logic. A real system must validate exact instrument mappings and versioned policy documents before enforcement.

## Next engineering tasks

1. Map current frontend and backend flow and establish compatibility tests before UI changes.
2. Define policy profiles as versioned, approved structured data with effective dates and provenance.
3. Build a position/exposure aggregation contract, distinguishing gross/notional/eligible exposure and open paper commitments.
4. Add a deterministic simulation of price, basis, margin and liquidity outcomes, with independently reviewed numerical fixtures.
5. Implement assessment rubrics that separate policy compliance, hedge effectiveness, explanation quality and realized PnL.
6. Build an instructor-controlled scenario authoring and review workflow.
7. Design and visually test beginner, practitioner and advanced workspaces in Chinese and English.

Any expansion must preserve the existing application, make no changes to production credentials, and require benchmark evidence before replacing established modules.
