# Commodity Lab Architecture

Commodity Lab V1 is an AI-driven Windows desktop training terminal for natural gas hedging. The active workflow is generated training, not external market-data retrieval.

## Core Loop

```text
Business template
  -> AI-generated case, curves, target actions, and rubric
  -> learner builds multi-leg hedge
  -> local deterministic scoring
  -> optional AI explanation, exam, or workspace action
```

## Layers

```text
Business Template Layer
  -> procurement and sales workflows for natural gas

AI Generation Layer
  -> Haineng / DeepSeek compatible prompts for cases, curves, rubrics, exams, and live assistant actions

Learning Layer
  -> multi-leg answer model, deterministic scoring, learner feedback, and future profile tracking

Desktop Layer
  -> FastAPI backend, React frontend, Tauri Windows shell
```

## AI-Generated Training Context

V1 does not fetch external prices. The generated case owns its market context:

- curves with `open`, `high`, `low`, and `close`;
- events and business assumptions;
- expected physical, paper, FX, basis, or capacity legs;
- scoring rubric.

Deterministic gas fixtures remain in `core/gas_scenarios.py` only as offline fallback context for regression tests and unconfigured AI sessions.

## Provider Model

`core/haineng_client.py` contains the AI provider contract:

- `haineng`: local Haineng deployment profile;
- `deepseek`: separate fallback/testing profile;
- runtime settings are configured through the desktop Settings menu or optional environment variables;
- secrets are redacted from health responses and prompts.

## UI Model

The React app is organized around a trading terminal layout:

- left rail: business templates and knowledge points;
- center: generated case, Markdown decision prompt, chart, strategy builder, local score, rubric;
- right rail: AI actions and Markdown output;
- floating assistant: free-form questions and safe action cards;
- settings menu: API, language, theme, developer info, version, and update check;
- guided overlay: first-run step-by-step onboarding.

## Delivery

Commodity Lab V1 ships Windows desktop artifacts from the Tauri build. Generated installers and bundles are release artifacts, not repository source files.
