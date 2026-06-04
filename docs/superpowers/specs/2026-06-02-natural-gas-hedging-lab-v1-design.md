# Commodity Lab V1 Natural Gas Hedging Design

## Context

Commodity Lab is intended to become a learning hub for commodity trading skills. V1 will focus on hedging and will be delivered as a native Windows client through the existing Tauri desktop app.

The current repository already contains a Python core, a FastAPI backend under `tauri/backend`, a Tauri/Rust bridge, and a React/Vite frontend prototype under `tauri/tauri-frontend`. Existing reusable modules include `core/hedge.py`, `core/practice.py`, `core/data_source.py`, and `core/platts_connector.py`. The V1 design should evolve these pieces rather than restart the app.

## Approved Direction

V1 is the Commodity Lab natural gas hedging module with an LLM-led training experience. The first usable screen is a guided trading-terminal workspace:

- Left rail: natural gas scenario deck.
- Center workspace: market context, pipeline capacity context, order ticket, order blotter, deterministic metrics, and results.
- Right rail: guided steps, 海能 advisor, hints, critique, mistake tags, and next action.
- Exam tab: 海能-generated questions tied to the selected scenario and user attempt history.

Other categories and product areas remain visible in navigation, but show a clear `Constructing` state.

The client must support English and Mandarin from V1. All first-party UI text, setup flows, scenario labels, guidance steps, validation messages, exam instructions, and constructing states must be available in both languages through a real translation catalog rather than inline conditionals. The active language should also be sent to 海能 so tutor output, exam questions, hints, and debriefs match the user's selected language.

## Scope

V1 enables only natural gas scenarios:

- Producer short hedge against falling Henry Hub prices.
- Utility or power-load hedge against winter price spikes.
- Pipeline capacity constraint with sample nominations, available capacity, congestion, and basis impact.
- Regional basis blowout hedge.
- Storage or calendar-spread hedge.

Pipeline capacity must work in sample mode when Platts is not configured. Platts enriches market and capacity data when available, but does not gate basic scenario use.

海能 is required before the learning loop starts. Without a configured and healthy 海能 connection, the app shows setup and provider-health states only. No fake advisor, score explanation, exam, or debrief is shown.

## Out Of Scope

- Oil, refined products, metals, grains, and non-gas scenarios.
- Multi-user accounts, cloud sync, or shared classrooms.
- Live order routing or broker integration.
- Full Platts contract-universe management beyond the optional data-provider path.
- A separate Streamlit app. V1 targets the Tauri desktop app.

## Bilingual UX And Visual Aid Requirements

V1 should feel like a professional product, not an engineering prototype. The UI should be minimalist and trading-terminal-like, but still intuitive for learners who are not yet confident with hedging terminology.

Language support:

- Support English and Mandarin Chinese with a persistent language selector available from setup and the main app header.
- Default to English unless a saved user preference exists.
- Keep all first-party strings in a translation catalog, including buttons, labels, tooltips, scenario names, guided-step names, empty states, errors, metric labels, exam copy, and constructing states.
- Keep commodity terms consistent across both languages through a small glossary, including hedge, basis, capacity, nomination, congestion, exposure, hedge ratio, P&L, and calendar spread.
- Pass the selected locale to 海能 prompts and require responses in that locale.
- Allow user rationale and exam answers in either English or Mandarin, independent of the UI language.

Visual aid requirements:

- Use charts, compact diagrams, and visual state cues to teach the scenario rather than relying on text alone.
- Show a pipeline-capacity strip or flow diagram for capacity scenarios: receipt point, pipeline segment, delivery point, available capacity, nominations, utilization, and congestion status.
- Show exposure visually with clear long/short direction, unhedged amount, hedged amount, and hedge ratio.
- Show order effects immediately after simulation through P&L, coverage, basis impact, and mistake tags.
- Use a guided stepper in the right rail so learners always know where they are: understand exposure, inspect market, place hedge, review score, exam.
- Use concise tooltips or inline definitions for trading terms; avoid long instructional paragraphs inside dense panels.
- Use meaningful icons and status colors for provider health, data source, completed steps, warnings, and constructing sections.

Product quality requirements:

- The first screen after setup must be usable without reading a manual.
- The order ticket must guide required fields and prevent invalid orders before submission.
- Dense panels must stay readable on desktop and laptop viewports; text must not overlap or overflow.
- Empty, loading, provider-error, and constructing states must look intentional and polished.
- The UI should use restrained color, clear hierarchy, and stable panel dimensions so it feels like a modern commodity training terminal.

## Provider Model

### 海能

The in-app LLM provider is branded as `海能`. Implementation should use an OpenAI-compatible client because the provided examples use:

- Python package: `openai`
- Client: `openai.OpenAI`
- Model default: `V4-Flash`
- Base URL shape: a local CNOOC-hosted OpenAI-compatible `/v1` endpoint
- Supported modes: normal chat, streaming chat, streamed reasoning fields when present, and function/tool calling

The repository must not hardcode the sample API key or any user credential. The setup gate collects:

- 海能 API key
- 海能 base URL
- Model name, defaulting to `V4-Flash`
- Optional streaming toggle
- Optional function-calling capability check

UI text says `海能`; provider implementation details must not become product wording.

### Platts

Platts is optional. Users provide their own Platts credentials and endpoint settings. If Platts is unavailable, the app falls back to yFinance or sample scenario series where possible.

### yFinance And Sample Data

yFinance and built-in sample data provide default market context. Natural gas pipeline-capacity scenarios must have built-in sample constraints, nominations, utilization, and congestion events so the training loop remains usable without Platts.

## LLM-Led Learning Model

海能 should be an active tutor, not a passive chat box. Deterministic Python code computes market data, order simulation, P&L, hedge ratios, exposure coverage, capacity utilization, and baseline rubric inputs. 海能 explains the learning value, probes the user's reasoning, generates hints, and creates adaptive exams.

V1 海能 roles:

- Dynamic scenario framing: introduces each gas hedging case as a tutor.
- Pre-trade coach: asks the user to identify exposure before placing orders.
- Socratic guidance: asks targeted questions rather than revealing full answers too early.
- Live hint engine: gives one next step based on the current scenario and order draft.
- Action reviewer: critiques hedge direction, sizing, timing, instrument choice, basis treatment, and capacity awareness.
- Mistake classifier: tags repeated patterns such as wrong direction, over-hedging, under-hedging, ignoring basis, ignoring capacity, or confusing physical and financial exposure.
- Adaptive scoring explainer: uses Python metrics as evidence and explains the score in training language.
- Debrief writer: summarizes what the user did, why it mattered, and what to retry.
- Exam generator: creates 3-5 natural gas hedging questions based on the current scenario and attempt history.
- Next-challenge generator: proposes a follow-up exercise based on weaknesses.

Function calling should be used where it improves reliability. 海能 can request deterministic app functions such as fetching scenario state, computing hedge metrics, classifying a mistake candidate, or retrieving recent attempt history before producing final coaching.

## Components

### Python Core

- `core/gas_scenarios.py`: natural gas scenario definitions, including pipeline capacity sample data and expected learning objectives.
- `core/haineng_client.py` or `core/llm_provider.py`: provider-neutral OpenAI-compatible 海能 client, prompt contracts, streaming support, capability checks, and function-call orchestration.
- `core/learning_session.py`: session state, attempts, order history, user rationale, mistake tags, and debrief summary.
- `core/hedge.py`: reused and extended only where needed for gas hedging metrics.
- `core/data_source.py` and `core/platts_connector.py`: retained as data-provider routing and optional Platts integration points.

### Backend

`tauri/backend/main.py` should expose endpoints for:

- Provider setup status and health checks.
- Scenario list and scenario detail.
- Market context for selected scenario.
- Pipeline capacity context for selected scenario.
- Attempt evaluation.
- 海能 hint generation.
- 海能 action review and score explanation.
- 海能 debrief generation.
- 海能 exam generation and exam feedback.

The backend should avoid leaking credentials into prompts, logs, test snapshots, or frontend state.

### Tauri Bridge

`tauri/src-tauri/src/main.rs` should evolve from fixed commands such as `ping_backend` and `simulate_backend` toward a small generic backend bridge or a complete set of specific commands for V1 endpoints. The bridge still starts and stops the Python backend with the desktop app.

### Frontend

`tauri/tauri-frontend/src/App.jsx` should be split into feature components instead of remaining a single prototype file. A dedicated stylesheet should define the minimalist terminal-like UI system.

Frontend sections:

- Setup Gate
- Scenario Deck
- Guided Simulator
- Market Context Panel
- Pipeline Capacity Panel
- Order Ticket
- Order Blotter
- Metrics and Results
- 海能 Advisor Rail
- Exam Tab
- Constructing Views

Frontend architecture should include:

- `src/i18n.js` or equivalent translation module with English and Mandarin dictionaries.
- A persistent language selector and saved locale preference.
- Component-level use of translation keys rather than hardcoded visible strings.
- Reusable visual-aid components for market charts, exposure bars, capacity diagrams, guided stepper, provider health, and constructing states.

## Data Flow

1. App starts and asks backend for provider status.
2. App loads the saved locale preference and applies English or Mandarin UI strings.
3. If 海能 is not configured or fails health check, the setup gate blocks the learning loop.
4. After 海能 is healthy, frontend loads natural gas scenarios in the selected locale.
5. User selects a scenario.
6. Backend returns scenario facts, sample/yFinance/Platts market context, and capacity context.
7. 海能 receives the selected locale and introduces the scenario in that language.
8. 海能 asks the user to identify exposure before order entry.
9. User enters rationale and draft hedge order.
10. Python computes deterministic metrics and validation signals.
11. 海能 receives sanitized scenario, rationale, order, metrics, selected locale, and attempt history.
12. 海能 returns hint, critique, score explanation, mistake tags, and next action in the selected locale.
13. User can revise the hedge, complete the attempt, and generate an exam.
14. Exam results feed back into the session summary and next-challenge generation.

## Error Handling

- Missing 海能 key: block simulator, advisor, scoring, debrief, and exam; show setup gate.
- 海能 health-check failure: show retry, editable settings, and clear provider-status detail.
- 海能 request failure during an attempt: preserve local order state and deterministic metrics; disable AI output until retry succeeds.
- 海能 function-call failure: fall back to a plain structured prompt only if deterministic metrics are already available; otherwise show retry.
- Platts missing or failed: fall back to yFinance or sample scenario series.
- yFinance failed: fall back to sample market series.
- Capacity data unavailable: use built-in sample capacity model for V1 gas scenarios.
- Invalid order: show deterministic validation before sending anything to 海能.
- No fake AI responses: all advisor, score explanation, and exam content must come from 海能.
- Missing translation key: fail visibly in development and fall back to English in packaged clients.
- 海能 returns the wrong language: show the response, tag it as a language mismatch in logs, and retry only when the user explicitly requests regeneration.

## Testing

Unit tests:

- Natural gas scenario loading.
- Pipeline capacity sample calculations.
- Hedge scoring inputs and order simulation.
- Provider-status parsing.
- Prompt-contract builders that verify credentials are never included.
- Translation catalog coverage for English and Mandarin.
- Locale-aware prompt builders that include the selected language and never include credentials.

Backend tests:

- Setup status endpoint.
- Scenario list and detail endpoints.
- Market context fallback behavior.
- Capacity context fallback behavior.
- Attempt evaluation endpoint.
- Hint, debrief, and exam endpoints with mocked 海能 responses.

Frontend tests:

- Setup gate blocks simulator until 海能 is configured.
- Scenario deck shows only natural gas enabled.
- Other tabs show `Constructing`.
- User can select a scenario, enter an order, view deterministic metrics, and request 海能 feedback.
- Exam tab can request generated questions and submit answers.
- Language selector updates the full app shell, simulator, constructing states, and exam UI.
- Visual aids render for market, exposure, capacity, guided-step, and provider-health panels.
- Text remains readable without overlap in both English and Mandarin.

Manual verification:

- Start backend and Tauri frontend.
- Complete setup with user-provided 海能 credentials.
- Switch between English and Mandarin and confirm all visible first-party UI text changes.
- Select a natural gas scenario.
- Place an order.
- Confirm visual aids explain market context, pipeline capacity, exposure, hedge result, and guided step status.
- Confirm metrics and 海能 guidance appear in the selected language.
- Generate and submit a short exam.
- Confirm Platts failure does not block sample/yFinance mode.

## Delivery

V1 delivery is a Windows Tauri client. The app should feel like a modern minimalist trading terminal, but prioritize a real training loop over broad unfinished functionality.

The final V1 acceptance criteria:

- 海能 setup gate is mandatory and branded correctly.
- English and Mandarin UI are both complete and selectable.
- 海能 tutor, exam, hint, and debrief output follow the selected language.
- Natural gas scenario deck works.
- Pipeline capacity sample model works without Platts.
- User can place simulated hedge orders.
- Deterministic metrics calculate locally.
- 海能 provides hints, critique, score explanation, debrief, and exam generation.
- Professional visual aids are present for market context, pipeline capacity, exposure, guidance steps, and provider status.
- Other categories and future sections are visible but marked `Constructing`.
- No provider credentials are committed or sent inside prompts.
