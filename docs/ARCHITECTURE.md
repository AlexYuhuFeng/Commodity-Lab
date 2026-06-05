# Commodity Lab Architecture

Commodity Lab is an AI-powered energy trading learning platform. The first commercial focus is European natural gas, but the architecture is deliberately designed for future North America gas, LNG, crude oil, refined products, carbon, and power modules.

## Product Positioning

Commodity Lab is not a static course, spreadsheet calculator, or simple hedging simulator. It is a guided training terminal where a learner repeatedly practices realistic energy trading decisions with structured market context, deterministic scoring, and AI coaching.

Core loop:

```text
Market context
  -> AI case or Socratic prompt
  -> learner decision
  -> deterministic scoring
  -> learner profile update
  -> adaptive next recommendation
```

## Layered Architecture

```text
Energy Domain Layer
  -> EnergyModule / EnergyAsset / TrainingScenario / AICapability

Scenario Registry Layer
  -> commodity-agnostic scenario discovery, filtering, and future scenario registration

Market Context Layer
  -> Yahoo Finance, simulated data, Platts-reserved context, future EEX/ICE/ENTSOG/GIE sources

AI Capability Layer
  -> case_generation, event_drill, concept_tutor, trade_playbook, socratic_coach, advisor_review, exam

Learning Layer
  -> deterministic evaluation, learner profile, weak-skill detection, adaptive journey

Desktop Delivery Layer
  -> FastAPI backend, React frontend, Tauri Windows desktop packaging
```

## Energy Domain Layer

Implemented in:

```text
core/energy_models.py
```

Primary abstractions:

- `EnergyModule`: top-level product module such as natural gas, crude oil, oil products, carbon, or power.
- `EnergyAsset`: tradable or risk-bearing asset definition such as TTF, NBP, Brent, EUA, or German baseload.
- `TrainingScenario`: reusable scenario contract independent of commodity type.
- `AICapability`: AI function contract independent of commodity type.

Current module status:

| Module | Status | Notes |
|---|---|---|
| Natural Gas | Enabled | V1 focuses on Europe gas. |
| Crude Oil | Constructing | Future Brent/WTI/Dubai and spread training. |
| Oil Products | Constructing | Future cracks, gasoil, gasoline, jet, fuel oil training. |
| Carbon | Constructing | Future EUA/UKA/CEA and compliance-risk training. |
| Power | Constructing | Future baseload, peakload, spark spread, clean spread training. |

## Scenario Registry Layer

Implemented in:

```text
core/scenario_registry.py
```

Purpose:

- Avoid hard-coding every scenario in natural-gas-specific modules.
- Allow future modules to register scenarios through the same contract.
- Enable scenario filtering by commodity, region, status, tags, and locale.

V1 enabled scenarios should be Europe gas first. North America gas scenarios may exist as `constructing` placeholders but should not dominate the primary journey.

## Market Context Layer

Current status:

- Yahoo Finance: enabled for supported public futures symbols.
- Simulated: deterministic fallback for training continuity.
- Platts: reserved for user-provided credentials and future commercial integration.

Rules:

1. If a live provider succeeds, returned source must show that provider.
2. If a live provider fails, the UI and API must explicitly show fallback reason.
3. AI must not invent exact market prices, settlement values, outage facts, or regulatory facts without supplied context.
4. Future sources can include EEX, ICE, ENTSOG, GIE, TSO tariff data, and curated news/search results.

## AI Capability Layer

Implemented primarily in:

```text
core/haineng_client.py
```

Supported capabilities:

| Capability | Role |
|---|---|
| `case_generation` | Generate realistic trading cases from scenario, market context, and user request. |
| `event_drill` | Convert market events into structured trading drills. |
| `concept_tutor` | Teach concepts with practical energy examples. |
| `trade_playbook` | Produce pre-trade checklists and execution/risk plans. |
| `socratic_coach` | Ask diagnostic questions instead of giving the answer immediately. |
| `advisor_review` | Review a submitted decision against deterministic scoring. |
| `exam` | Generate adaptive assessment questions. |

海能 is required for AI Full Power Mode, but the product must not block initial entry when 海能 is not configured. Base Mode should still provide market context, scenarios, decision ticket, deterministic scoring, and basic journey structure.

## Learning Layer

Implemented in:

```text
core/learner_profile.py
core/learning_journey.py
```

Tracked skill dimensions:

- price risk
- basis
- spread
- storage
- capacity and route
- units and FX
- controls
- operations

The learning journey maps weak skills to scenarios and AI capabilities. For example:

| Weak Skill | Scenario Direction | AI Capability |
|---|---|---|
| basis | TTF/NBP spread | socratic_coach |
| units_fx | TTF/NBP unit normalization | concept_tutor |
| capacity_route | European route/capacity case | trade_playbook |
| storage | storage calendar spread | case_generation |
| operations | event-driven operational drill | event_drill |

## API Surface

Core V1 API endpoints:

```text
GET  /api/v1/catalog
GET  /api/v1/scenarios
GET  /api/v1/scenarios/{scenario_id}/context
POST /api/v1/attempts/evaluate
GET  /api/v1/learner-profile
GET  /api/v1/learning-journey
POST /api/v1/ai/generate
GET  /api/v1/provider-status
POST /api/v1/provider-settings
```

## First-Run Product Flow

Target UX:

```text
Welcome
  -> choose role
  -> choose track: Europe Natural Gas
  -> see Base Mode capabilities
  -> start first guided scenario
  -> connect 海能 to unlock AI Full Power Mode
```

Roles to support:

- Student
- Junior Trader
- Trader
- Risk Manager
- Commercial Manager
- Scheduler / Operator

## Future Module Extension Contract

To add a new module, do not fork the application structure. Instead:

1. Add or enable `EnergyModule`.
2. Register `EnergyAsset` definitions.
3. Register `TrainingScenario` entries.
4. Provide market context provider or deterministic fallback.
5. Map tags to learner skills.
6. Reuse AI capabilities.
7. Add module-specific tests.

## Commercial Readiness Criteria

Commodity Lab should not be called commercially ready until the following are true:

- CI passes for Python, frontend, and Tauri packaging.
- Windows artifact is generated and downloadable.
- First-run UX is understandable without developer explanation.
- Base Mode works without 海能.
- AI Full Power Mode clearly changes the experience after 海能 connection.
- Each AI capability has mocked tests with realistic European gas use cases.
- Data source priority and fallback status are visible and correct.
- Scenario Registry and Learning Journey are covered by tests.
- Secrets are never echoed in API responses, prompts, or logs.
