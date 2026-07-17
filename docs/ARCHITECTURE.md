# Commodity Lab Architecture

Commodity Lab is a Windows desktop learning platform for commodity trading and financial risk management. The product combines a stable competency framework with DeepSeek-generated lessons, market states, decisions, and coaching.

## Product Contract

The learning experience has one visible loop:

```text
Learning goal
  -> market evidence
  -> business decision
  -> immediate deterministic score
  -> concise AI review
  -> next drill
```

The interface keeps this loop simple. Advanced parameters, provider details, and curriculum metadata stay collapsed until the learner needs them.

## Learning Model

The curriculum is stable across learners; the route through it is personalized.

- **Competency graph:** exposure and hedge objective, market structure, physical-paper matching, basis, FX, capacity/freight/storage, options, execution, and controls.
- **Business models:** European gas procurement and sales, LNG and regas, pipeline capacity, EFET/OCM/EEX workflows, and crude cargo, benchmark, calendar, inventory, and freight hedging.
- **AI planner:** chooses the next explanation, drill, replay checkpoint, or exam from the learner's goal and actual local progress.
- **Mission compiler:** produces the case background, evidence, decision gates, target actions, and rubric as one internally consistent session.
- **Scoring engine:** scores generated target actions locally. AI explains and adapts; it is not required for the initial score.

## Market Evidence Layer

Every market context uses the same contract and carries `mode`, `source_tier`, `as_of`, `benchmark`, unit, curve metrics, and provenance.

### Live market

The provider adapter is designed for entitled S&P Global Commodity Insights (Platts) delivery. S&P documents API, streaming, sFTP, and developer/MCP access for subscribed data. Live delivery still requires customer credentials, entitlements, symbol mapping, licensing review, and an encrypted local credential store.

Current status: the capability contract and explicit fallback behavior exist; the production Platts fetch adapter is not complete. A live request that cannot be fulfilled falls back to a labelled simulation and never presents simulated data as live.

### Historical replay

A replay event is a point-in-time information pack:

- only facts available at the current checkpoint are visible;
- future checkpoints and outcomes remain hidden;
- each checkpoint has a decision prompt, observable market state, and source notes;
- price paths may be historically calibrated simulations when licensed tick data is unavailable.

The first pack covers the 2026 Strait of Hormuz disruption using an EIA event narrative and a clearly labelled simulated training curve.

### AI-simulated market

`core/market_learning.py` generates deterministic forward curves and OHLC histories for natural gas and crude oil. It supports contango, backwardation, flat, and high-volatility regimes. The numeric engine owns prices and consistency; DeepSeek owns the business narrative, events, decisions, and teaching language.

This separation prevents prompt wording from producing contradictory curves and makes regression testing possible.

## Runtime Layers

```text
React learning client
  -> simple learning studio, workbench, replay, progress, floating assistant

FastAPI application service
  -> provider settings, market evidence, replay sessions, case generation, scoring

Learning and market core
  -> curriculum templates, deterministic market engine, replay packs, scoring rules

AI provider contract
  -> Haineng / DeepSeek prompts, structured case JSON, safe workspace actions

Tauri Windows shell
  -> native window, secure local settings, backend lifecycle, release packaging
```

## AI Interaction Contract

AI may generate or update a case, curve context, strategy legs, explanation, exam, and learning route through structured actions. The UI applies visible actions and navigates to the affected workspace instead of only describing the change in chat.

### Curriculum and product workspaces

The curriculum has two layers:

1. **General hedging tools:** exposure direction, forward structure and carry, futures/forwards/swaps, physical-paper matching, basis, options, hedge ratios, FX, and execution controls. Completion records in this layer are shared across products.
2. **Product-specific application:** market conventions, business flows, benchmarks, logistics, and risk combinations for the selected commodity. Natural Gas and Crude Oil are active workspaces. Refined Products, Power, and Carbon are visible but disabled until their reviewed curriculum and scenario packs are ready.

The compact product selector changes the active curriculum, scenarios, market engine, historical events, progress view, and AI context together. Product changes invalidate in-flight generation and assistant requests, and template actions are checked against the selected product before execution. This prevents stale or hallucinated cross-product content from entering the current lesson.

The generation path uses three execution planes so model latency never blocks the whole lesson:

1. **Local evidence plane:** the deterministic market engine immediately creates forward quotes, OHLC history, provenance, and replay state.
2. **Streamed orchestration plane:** the backend sends stage, market, and provider-token events over SSE. The Tauri shell forwards those events to React, which progressively replaces the local scenario skeleton with generated fields.
3. **Local decision plane:** rubric and replay decisions are scored locally as soon as the learner submits. The model is used afterward for explanation, counterfactuals, and the next drill.

Only decision-relevant curriculum items, six forward tenors, and a sampled history are sent to the model. The full market dataset remains in the client. This reduces prompt size without reducing chart fidelity or curriculum coverage across the overall learning path.

The app does not expose private chain-of-thought. During longer operations it shows useful stage summaries such as:

1. Understanding the learning goal.
2. Resolving market evidence and provenance.
3. Building the curve and event path.
4. Mapping exposures and target actions.
5. Preparing the decision and rubric.

Provider text is not the primary control surface. Structured AI actions such as `patch_case`, `set_market_curves`, `set_chart_fields`, `set_strategy_legs`, and learning-route updates must produce an immediate visible workspace change. Text explains the change briefly after the UI has applied it.

## Data and Security Rules

- AI and market credentials must never enter Git, release notes, screenshots, or logs.
- Live data must preserve provider attribution, entitlement boundaries, symbol, and as-of time.
- Historical replay must prevent future-information leakage.
- Simulated values must remain labelled as simulated at every API boundary.
- Generated rubrics and actions are validated before deterministic scoring.
- Provider failures must leave the client responsive and offer a clear recovery path.

## Primary References

- [S&P Global Commodity Insights Market Data](https://www.spglobal.com/commodityinsights/en/products-services/market-data)
- [S&P Global Commodity Insights Developer MCP Getting Started](https://developer.spglobal.com/commodityinsights/mcp/getting-started)
- [CME Group: What is Contango and Backwardation?](https://www.cmegroup.com/education/courses/introduction-to-ferrous-metals/what-is-contango-and-backwardation)
- [U.S. EIA: Petroleum markets responded to disruptions in the Middle East in Q2 2026](https://www.eia.gov/todayinenergy/detail.php?id=67865)
