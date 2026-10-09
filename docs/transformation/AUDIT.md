# Repository audit

Inspected main 629a72af6304b061822c15956e1b5e91868a6435 and draft PR #3 (6242d718), 2026-10-09.

| Area | Evidence and assessment | Decision |
|---|---|---|
| Runtime | React 18/Vite, Tauri 1 Rust shell, local FastAPI Python sidecar; dynamic localhost port and backend lifecycle in `tauri/src-tauri/src/main.rs` | Preserve desktop and API bridge |
| UX | `App.jsx` ~5,566 lines, `styles.css` ~9,147; courses/library/workbench/progress, bilingual copy, product scaffolds | Add isolated scoped feature; avoid broad rewrite |
| Curriculum | `training_templates`, `gas_scenarios`, `energy_models`, `learning_journey`; gas and crude catalogs, other products scaffolded | Preserve; do not equate catalog breadth with validated financial support |
| Assessment | `learning_session` recommended-side/type scoring, `hedge` profit-sensitive scores; generated target-leg matching | Preserve compatibility; new assessment separates evidence, policy and outcomes |
| Learners | In-memory backend profile starts at 50, additive deltas, tags mapped to skills; UI local records | Insufficient for mastery/enterprise identity; new sessions durable, broader migration M2 |
| Markets | `market_learning` seeded synthetic curves, reviewed replay metadata, checkpoint slicing; historical curves explicitly calibrated simulations | Reuse provenance principles; new fixture wholly synthetic, server-sequential |
| Finance | `hedge` signed derivative PnL, `backtest`/strategies, energy asset metadata; no unified physical/derivative ledger or settlement convention | Independent Decimal procurement/swaps model for slice |
| AI | `haineng_client` OpenAI-compatible Haineng/DeepSeek, SSE, structured actions and consistency normalization; Windows DPAPI persistence | Optional ungraded coach only; provider round-trip unverified |
| Data | `platts_market` external symbol mapping, entitlement-dependent REST adapter, fresh/stale cache/provenance; no subscription evidence | No licensed data used; commercial redistribution terms require review |
| Tests | pytest suites across DB, markets, learning, API, release guardrails; Vitest App and key import | Run full regressions and extend new domain/API/UI coverage |
| CI/releases | PR CI Python only; separate release workflow tests frontend and packages Windows NSIS/MSI and Linux x86_64/ARM64 deb/AppImage; PyInstaller hidden imports | Extend PR gate to frontend; preserve release jobs; include new router imports |
| Dependencies/licenses | No root LICENSE observed; existing Python/JS dependencies broadly permissive (React MIT, FastAPI MIT, pandas BSD, DuckDB MIT, OpenAI Apache-2.0); PyInstaller has GPL bootloader exception | No new runtime dependencies; legal review needed before redistribution; do not infer repo license |
| Credentials | `.env.example`, key-file gitignore, redaction and DPAPI tests; non-Windows persisted key behavior needs production review | No credential changes; no values in new artifacts |

PR #3 correctly isolates illustrative policy and acknowledges missing aggregation/direction/maturity. Tests were not executed according to PR body. Unknown instrument strings can bypass options restrictions; volume comparability is caller asserted; floating tolerance is fixed; profile is unversioned. Do not merge/cherry-pick blindly. New contracts use a supported-instrument enum, exact Decimal limits, matching conventions and accumulated positions.

Technical debt: oversized frontend/backend modules, loosely typed generated scenarios, mixed quantitative/teaching scores, dependency lower bounds without Python lock, single local identity and weak persistence. Neither microservices nor a desktop replacement addresses these first. New feature isolation provides a tested migration seam.
