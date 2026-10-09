# Milestone 1 verification evidence

Executed 2026-10-09 on Linux x86_64, Python 3.12.14, Node 24.19.0. Branch `feature/gas-training-vertical-slice`; base `629a72af6304b061822c15956e1b5e91868a6435`.

| Gate | Result |
|---|---|
| Full backend regression | **161 passed** (`python -m pytest -q`) |
| Full frontend regression | **50 passed**, 3 files (`npm test`) |
| Frontend production build | **Passed**, Vite 8.0.16 |
| Browser workflows | **2 passed**, real FastAPI and React; English desktop and Chinese mobile journeys, blocked proposals, resize, settlement, saved-session resume, keyboard focus and overflow |
| Visual regression | **6 PNG baselines inspected; 6 comparisons passed** without `--update-snapshots`, Playwright 1.64.0 / Chromium 156.0.8078.4 |
| Linux packaged backend | **Built** with PyInstaller 6.22.3 using the existing build script; packaged health API and complete gas workflow **passed**, net cost €368,000 and trading margin €112,000 before other costs |
| Diff hygiene | `git diff --check` passed |
| New-file credential patterns | Reviewed before commit; no new credential material or licensed data |
| Full Tauri Windows/Linux desktop bundles | **Unverified in this session**; preserved release workflow, hidden-import lists extended |
| Real Haineng/DeepSeek provider | **Unverified**; offline and mocked configured/error paths tested |
| Licensed market entitlement | **Unverified / unused**; all new market observations synthetic |
| Corporate authority and instructor rubric sign-off | **Not claimed**; policy illustrative, diagnostic evidence provisional |

## Independent numerical reference

At decision 1, a gas trading company expects to source 10,000 MWh to fulfill a flexible-volume customer sales contract at €60/MWh and takes 8,000 MWh long at €40/MWh. At decision 2, nominations fall to 8,000 MWh, quote is €50/MWh, and target falls to 6,400 MWh. The resize is an offsetting 1,600 MWh short trade, with all swap cash flows paid at final settlement.

Final index €55/MWh, basis €5/MWh:

- Physical outflow: 8,000 × (55 + 5) = **€480,000**.
- Swap receipt: 8,000 × (55 − 40) − 1,600 × (55 − 50) = **€112,000**. Independently: 1,600 × (50 − 40) + 6,400 × (55 − 40) = the same receipt.
- Physical sales receipt: 8,000 × 60 = **€480,000**; unhedged physical margin **€0**; trading margin including swaps **€112,000** before freight/fees/tax/financing.
- Net purchase cost: 480,000 − 112,000 = **€368,000**.
- Volume-adjusted initial budget: 8,000 × (40 + 2) = **€336,000**; budget variance **−€32,000**.
- Ex-post cost-shock offset: 112,000 / (480,000 − 336,000) = **77.78%**. It is not a statistical hedge-effectiveness test.
- Peak sampled collateral estimate: **€40,000** before the second resize; final estimate **€35,200**.

Falling-price independent reference: 8,000 MWh long at 40 marked at 30 loses €80,000; 10% initial margin is €24,000; adverse net MTM plus initial margin is **€104,000**. Tests also cover no hedge, 50% hedge, fractional quantities, exact 80% boundary, direction/backing, approval, unsupported instruments/units/periods, nonfinite/boolean input, concurrent requests, information leakage, schema/version rejection and grade independence from outcomes.

## Screenshots

Committed real browser screenshots under `tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/`:

- [English setup](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/gas-setup-en-dark-linux.png)
- [English decision](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/gas-decision-en-dark-linux.png)
- [English settlement](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/gas-settlement-en-dark-linux.png)
- [Chinese mobile setup](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/gas-setup-zh-mobile-light-linux.png)
- [Chinese mobile evidence](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/gas-decision-zh-mobile-light-linux.png)
- [Chinese mobile decision form](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/gas-form-zh-mobile-light-linux.png)

Screenshot typography is normalized with pinned `@fontsource/noto-sans-sc` 5.3.0 (OFL-1.1), a test-only dependency; the shipped UI retains its system font stack. The initial GitHub run passed unit/build gates but exposed system-font differences, so font selection was pinned rather than relaxing comparison thresholds.

The shell uses a scrolling content region; viewport captures show real visible UI. Initial clipped element captures were replaced before baseline acceptance. Light-mode labels were corrected after inspection. Baselines are Linux-specific; OS/fonts/browser changes may require reviewed rebaselining, not blind approval.

## Reproduction

```bash
python -m venv /tmp/commodity-venv
/tmp/commodity-venv/bin/pip install -r requirements.txt pytest httpx
/tmp/commodity-venv/bin/python -m pytest -q
cd tauri/tauri-frontend
npm ci
npm test
npm run build
npx playwright install --with-deps chromium
COMMODITY_TEST_PYTHON=/tmp/commodity-venv/bin/python npm run test:visual
```

The test harness loads its pinned Latin/Chinese font locally, with no external font service. Browser harness uses a dedicated `/tmp/commodity-lab-e2e.sqlite`, disables saved AI settings, and launches both servers. Use `CHROMIUM_PATH` only for an intentional alternative browser. In the managed sandbox, API/browser tests needed network-enabled execution; restricted attempts stalled and are not counted as passing. Build artifacts and transient logs are excluded from Git.

## Known limits

One fixed European gas procurement pack; no options, exchange-lot sizing, FX, fees, financing, daily margin ledger, portfolio VaR, or full accounting PnL. Nomination and market changes occur at reviewed checkpoints, not intraday. Approval is self-declared for training. Device-local SQLite is not multiuser authentication, enterprise governance, tamper-evident audit, or retention management. Rationale review and repeated competency evidence are the next assessment milestone. Legacy workflows pass regression tests but are not upgraded to this financial contract. No live execution is introduced.

PR CI now includes frontend build/tests and browser comparisons. The first remote run failed screenshot comparisons due to host-font differences; the corrected [remote CI run 37914696249](https://github.com/AlexYuhuFeng/Commodity-Lab/actions/runs/37914696249) **passed** on implementation commit `c2621d9f`. Remote CI independently passed the backend/frontend/build and normalized-font browser gates.
