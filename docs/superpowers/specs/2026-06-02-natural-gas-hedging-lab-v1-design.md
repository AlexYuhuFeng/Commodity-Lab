# Natural Gas Hedging Lab V1 Design

## Context

Commodity Lab is intended to become a learning hub for commodity trading skills. V1 will focus on hedging and will be delivered as native Windows and Linux clients through the existing Tauri desktop app.

The current repository already contains a Python core, a FastAPI backend under `tauri/backend`, a Tauri/Rust bridge, and a React/Vite frontend prototype under `tauri/tauri-frontend`. Existing reusable modules include `core/hedge.py`, `core/practice.py`, `core/data_source.py`, `core/platts_connector.py`, and `core/deepseek.py`. The V1 design should evolve these pieces rather than restart the app.

## Approved Direction

V1 is a Natural Gas Hedging Lab with an LLM-led training experience. The first usable screen is a guided trading-terminal workspace:

- Left rail: natural gas scenario deck.
- Center workspace: market context, pipeline capacity context, order ticket, order blotter, deterministic metrics, and results.
- Right rail: guided steps, 海能 advisor, hints, critique, mistake tags, and next action.
- Exam tab: 海能-generated questions tied to the selected scenario and user attempt history.

Other categories and product areas remain visible in navigation, but show a clear `Constructing` state.

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

## Provider Model

### 海能

The in-app LLM provider is branded as `海能`. Implementation should use an OpenAI-compatible client because the provided examples use:

- Python package: `openai`
- Client: `openai.OpenAI`
- Model default: `DeepSeek-V4`
- Base URL shape: a local CNOOC-hosted OpenAI-compatible `/v1` endpoint
- Supported modes: normal chat, streaming chat, streamed reasoning fields when present, and function/tool calling

The repository must not hardcode the sample API key or any user credential. The setup gate collects:

- 海能 API key
- 海能 base URL
- Model name, defaulting to `DeepSeek-V4`
- Optional streaming toggle
- Optional function-calling capability check

UI text says `海能`, not `DeepSeek`. Code may mention "OpenAI-compatible local DeepSeek deployment" only where it clarifies maintainability.

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

## Data Flow

1. App starts and asks backend for provider status.
2. If 海能 is not configured or fails health check, the setup gate blocks the learning loop.
3. After 海能 is healthy, frontend loads natural gas scenarios.
4. User selects a scenario.
5. Backend returns scenario facts, sample/yFinance/Platts market context, and capacity context.
6. 海能 introduces the scenario and asks the user to identify exposure.
7. User enters rationale and draft hedge order.
8. Python computes deterministic metrics and validation signals.
9. 海能 receives sanitized scenario, rationale, order, metrics, and attempt history.
10. 海能 returns hint, critique, score explanation, mistake tags, and next action.
11. User can revise the hedge, complete the attempt, and generate an exam.
12. Exam results feed back into the session summary and next-challenge generation.

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

## Testing

Unit tests:

- Natural gas scenario loading.
- Pipeline capacity sample calculations.
- Hedge scoring inputs and order simulation.
- Provider-status parsing.
- Prompt-contract builders that verify credentials are never included.

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

Manual verification:

- Start backend and Tauri frontend.
- Complete setup with user-provided 海能 credentials.
- Select a natural gas scenario.
- Place an order.
- Confirm metrics and 海能 guidance appear.
- Generate and submit a short exam.
- Confirm Platts failure does not block sample/yFinance mode.

## Delivery

V1 delivery remains Windows and Linux Tauri clients. The app should feel like a modern minimalist trading terminal, but prioritize a real training loop over broad unfinished functionality.

The final V1 acceptance criteria:

- 海能 setup gate is mandatory and branded correctly.
- Natural gas scenario deck works.
- Pipeline capacity sample model works without Platts.
- User can place simulated hedge orders.
- Deterministic metrics calculate locally.
- 海能 provides hints, critique, score explanation, debrief, and exam generation.
- Other categories and future sections are visible but marked `Constructing`.
- No provider credentials are committed or sent inside prompts.
