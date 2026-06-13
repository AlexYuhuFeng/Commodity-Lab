# Commodity Lab Product Roadmap

Commodity Lab is built as an AI-powered energy trading learning platform. The roadmap keeps V1 commercially focused on natural gas hedging and AI-generated training while preserving clean expansion paths for North America gas, LNG, crude oil, refined products, carbon, and power.

## Product North Star

Train energy traders through realistic, repeated decision practice:

```text
Choose business workflow
  -> AI generates case, curves, events, target actions, and rubric
  -> learner builds physical/paper/FX/capacity hedge
  -> receive immediate local score
  -> use AI for coaching, concepts, exams, and workspace actions
```

## V1: Europe Natural Gas First

Goal: make the first vertical credible and professionally useful.

Primary scope:

- TTF, NBP, THE, PEG, PSV, PVB as conceptual hub set.
- Hub spreads and basis.
- Unit and FX normalization.
- Storage calendar spreads.
- Route and capacity thinking.
- Nomination and operational context as training themes.
- AI-generated curves, target actions, rubrics, Socratic coaching, trade playbooks, exams, and safe workspace action cards.

Required V1 experience:

- User lands in a windowed Windows desktop client with a Codex-inspired native shell.
- User sees Mandarin by default and can switch language/theme from Settings.
- User chooses Haineng or DeepSeek in Settings and provides only an API key or local key file; model and endpoint are fixed by the app.
- User can generate a gas business case from procurement or sales templates.
- User can inspect generated multi-series high/low/close curves and strategy overlays.
- User can submit multi-leg hedges and receive immediate deterministic scoring.
- User can use the floating AI assistant for case generation, concept Q&A, and safe workspace customization.

Exit criteria:

- CI passes.
- Windows artifact builds.
- First-run UX is understandable.
- AI capabilities have mock tests.
- V1 contains no external market-data source selector or connector.
- Secrets are redacted.

## V2: North America Gas and LNG

Goal: expand natural gas while retaining same learning model.

Candidate scope:

- Henry Hub, AECO, Waha, Dawn.
- Producer hedging.
- Regional basis risk.
- Pipeline constraints.
- Weather-driven load risk.
- LNG optionality and cargo diversion concepts.

New requirements:

- Add North America gas assets.
- Add region-specific market context providers or deterministic fixtures.
- Add scenario registry entries.
- Extend skill-to-scenario mapping.
- Keep AI capabilities commodity-agnostic.

## V3: Crude Oil

Goal: extend beyond gas without changing platform architecture.

Candidate scope:

- Brent, WTI, Dubai.
- Brent-WTI and Brent-Dubai spreads.
- Time spreads.
- Physical differential and freight-aware cases.
- Refinery procurement exposure.

Key training concepts:

- Outright futures hedge.
- Calendar spread.
- Quality differential.
- Location differential.
- Freight and storage.

## V4: Refined Products

Candidate scope:

- Gasoil, gasoline, jet, fuel oil.
- Crack spreads.
- Regional arbitrage.
- Inventory and demand seasonality.
- Refinery margin training.

Key training concepts:

- Crack spread logic.
- Product yield and margin.
- Specification and location risk.
- Seasonal demand.

## V5: Carbon and Power

Candidate carbon scope:

- EUA, UKA, CEA.
- Compliance exposure.
- Calendar spread.
- Carbon-power linkage.

Candidate power scope:

- German baseload and peakload.
- UK power.
- Spark spread.
- Clean spark / clean dark spread.
- Renewable intermittency and load risk.

Key training concepts:

- Carbon compliance risk.
- Power shape risk.
- Fuel switching.
- Clean spread economics.

## AI Capability Evolution

Current and planned capabilities:

| Capability | V1 | Notes |
|---|---:|---|
| Case generation | Yes | Generate realistic cases from scenario and context. |
| Event drill | Yes | Convert events into structured drills. |
| Concept tutor | Yes | Teach energy concepts with examples. |
| Trade playbook | Yes | Pre-trade checklist and execution plan. |
| Socratic coach | Yes | Ask questions instead of giving answers. |
| Advisor review | Yes | Post-decision coaching. |
| Adaptive exam | Yes | Targeted questions from weak skills. |
| Market research assistant | Future | Search-backed case generation. |
| Negotiation coach | Future | Contract and counterparty roleplay. |
| Risk manager persona | Future | Risk-limit and portfolio review mode. |

## Commercial Readiness Roadmap

### Alpha

- Core platform architecture exists.
- Europe gas scenarios available.
- Deterministic scoring works.
- AI endpoint works with mock tests.
- Windows build workflow exists.

### Beta

- First-run UX completed.
- Learning journey visible in UI.
- AI Full Power Mode visually distinct.
- Scenario Registry is the primary scenario source.
- User settings and provider state are clear.

### Release Candidate

- CI passes reliably.
- Windows artifact installs and launches.
- No borderless shell unless explicitly designed.
- Secrets are not leaked.
- README and docs explain setup and use.
- Demo workflow can be followed by a new user without developer help.

### Commercial Delivery

- One complete Europe gas learning path.
- Multiple realistic use cases.
- AI coaching validated with representative prompts.
- Release artifacts versioned.
- Known limitations documented.
- Data-source caveats visible.
