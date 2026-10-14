# Commodity Lab — agent handoff

Read `docs/CODEX-CLOUD-HANDOFF.md`, `docs/transformation/PROGRESS.md`, the machine-readable `docs/transformation/backlog.json`, and the applicable ADRs before changing architecture. Preserve existing React/Tauri, FastAPI, AI providers and legacy learning workflows. Supported reviewed financial training domains are European gas and crude; beach/regas chapters include bounded introductory exercises, not full validated market simulators.

Work in an isolated branch; create reviewable PRs. Do not merge, publish releases, connect live trading execution, introduce paid services or alter production credentials without explicit user authorization. Training-company roles only. Illustrative policy is never actual company policy. Keep deterministic financial/assessment authority separate from AI prose. Never commit credentials or licensed data.

Verification (from repository root):

- `.venv/bin/python -m pytest -q`
- Frontend directory: `npm test` and `npm run build`
- Frontend directory: `CI=1 COMMODITY_TEST_PYTHON="$PWD/../../.venv/bin/python" npx playwright test`
- Linux package when changed: `PATH="$PWD/.venv/bin:$PATH" bash tauri/scripts/build_backend.sh`, then smoke real packaged API.

Browser tests disable local AI settings and use synthetic reproducible exercises. Do not substitute mocked screenshots or relax image tolerances to hide a layout regression. New screenshot baselines require inspection. Clearly report checks not executed, especially Windows/full desktop bundles and live provider qualification. Update durable progress and backlog; never mark external sign-off or professional mastery complete based on code generation.
