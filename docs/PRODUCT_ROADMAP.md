# Commodity Lab Product Roadmap

## North Star

Commodity Lab should feel like an expert tutor with a trading workbench, not a static question bank. A learner states a goal once; the platform selects the right market evidence, generates a realistic decision, evaluates the response immediately, and builds the next exercise from demonstrated gaps.

The UI rule is equally strict: one screen, one primary job, one obvious next action.

## Stable Curriculum

Every learner should ultimately cover the same core outcomes:

1. Exposure and hedge objective.
2. Forward curves, contango/backwardation, and carry.
3. Physical-paper matching and hedge direction.
4. Hub, location, grade, and time basis.
5. FX, capacity, freight, storage, and inventory.
6. Hedge ratio, correlation, and cross-hedge quality.
7. Options and operational optionality.
8. Liquidity, margin, credit, limits, and execution.
9. Integrated portfolio decisions and post-trade review.

DeepSeek can change examples, pacing, explanations, difficulty, and the next drill. It must not silently remove required outcomes.

## Active Delivery: Market-Aware Learning Foundation

Implemented in the current development branch:

- natural gas and crude-oil simulated market contexts;
- contango, backwardation, flat, and volatile regimes;
- forward curves, OHLC history, structure metrics, provenance, and as-of time;
- historical replay API with future-information isolation;
- initial 2026 Strait of Hormuz disruption replay pack;
- market-aware DeepSeek case generation;
- explicit live-data fallback without false live labels;
- compact AI learning studio with one goal input and one generate action;
- workbench display for provenance, forward structure, and market time.

Exit checks:

- all market modes use the same evidence contract;
- simulations are deterministic for the same seed;
- replay checkpoints cannot reveal future facts;
- generated cases retain market provenance;
- light and dark themes remain readable at supported desktop sizes;
- frontend, backend, and production builds pass.

## Phase 2: Production Platts Adapter

Goal: add entitled live-market learning without coupling the curriculum to a single feed.

- Confirm the customer's Platts product, API/stream/sFTP access, symbols, units, and redistribution rights.
- Implement secure local OAuth/client-credential storage.
- Build provider adapter, cache, retry, rate-limit, and stale-data behavior.
- Add natural-gas and crude symbol mapping plus unit normalization.
- Snapshot the exact evidence used by each training session.
- Add delayed/stale indicators and explicit simulated fallback.
- Test against a non-production subscription before release.

The repository must not contain customer credentials or licensed market payloads.

## Phase 3: Replay Studio

Goal: train decisions under uncertainty, not hindsight.

- Add replay authoring schema and source review checklist.
- Add event packs for supply disruption, storage shock, infrastructure outage, price collapse, and demand surge.
- Reveal evidence checkpoint by checkpoint.
- Compare the learner's decision with plausible alternatives, not one perfect trade.
- Generate counterfactual drills by changing hedge timing, basis, optionality, or physical constraints.

## Phase 4: Adaptive Tutor

Goal: turn completed work into a coherent learning path.

- Persist only real attempts and demonstrated skills.
- Build a mastery model from rubric-level evidence.
- Let DeepSeek choose the next lesson inside curriculum prerequisites.
- Keep responses concise by default and move generated content directly into the relevant UI.
- Add spaced review, exams, and targeted remediation.
- Show AI activity as high-level stages and visible workspace changes.

## Phase 5: Portfolio and Trade Operations

Goal: move from single cases to realistic desk decisions.

- multi-position and multi-period portfolios;
- P&L attribution and hedge effectiveness;
- limits, liquidity, credit, margin, and execution planning;
- LNG, pipeline, storage, and crude-cargo optionality;
- role-based procurement, sales, trading, and risk-manager simulations.

## Release Gate

A formal release requires:

- full automated test suite and production build passing;
- installed Windows executable launched and exercised through a complete training flow;
- API credentials retained securely across restart;
- no misleading live-data labels;
- no placeholder progress or placeholder market values presented as user history;
- visual QA in Chinese and English, light/dark/system themes, and representative window sizes;
- bilingual UTF-8 release notes and installers published only as GitHub release assets.
