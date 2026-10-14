# HB3 verification — 2026-10-14

Branch: `feature/handbook-evidence-portfolio`, based on PR #7 head `4ac65065`.

## Automated and quantitative evidence

- **270 backend tests pass**, including existing financial references and new ownership, duplicate/retry qualification, prerequisites, version drift, self-review rejection, concurrent revision handling and audit-export tests.
- **69 frontend tests pass**, including retained legacy progress/remediation tests and new portfolio, review, profile and failure recovery coverage. Production Vite build passes.
- **Nine real-backend browser workflows pass**; 18 screenshot comparisons (15 retained existing images and three new portfolio/review baselines). New screens cover English desktop/dark, Chinese mobile/light and reasoning review. Existing image tolerance remains 1%; old snapshots were not regenerated. Final run evidence is in `/workspace/scratch/commodity-evidence-browser-final.log`.
- **Linux PyInstaller backend builds and packaged API smoke passes**. A fresh packaged database verifies all five supported chapter exercises, seven independently calculated arithmetic examples, two reasoning reviews, derived guided-assessment readiness, learner isolation and audit export. This smoke exposed and verifies router registration before the executable server starts. Logs: `/workspace/scratch/commodity-evidence-package.log` and `commodity-evidence-packaged-smoke.log`.
- `git diff --check` and setup-script shell syntax checks pass. No dependencies were added. Scoped credential-pattern scan found no API key literals in the changed application/docs/scripts. The current environment has no configured provider secret.

Independent packaged reference outcomes: gas hub seeds 0/1/2 are EUR 20,500 / 21,450 / 22,200; matched beach route seed 0 EUR 2,000; simplified preconverted regas EUR 72,000; refinery procurement USD 130,000; owned-inventory lifecycle USD 56,000. These use public input arithmetic, not AI answers. Reviewed quantitative models and scoring were not changed by HB3.

## Real application screenshots

[English portfolio](../../tauri/tauri-frontend/e2e/learning-evidence.spec.js-snapshots/evidence-portfolio-en-dark-linux.png), [local reasoning review](../../tauri/tauri-frontend/e2e/learning-evidence.spec.js-snapshots/evidence-reasoning-review-en-dark-linux.png), [Chinese mobile](../../tauri/tauri-frontend/e2e/learning-evidence.spec.js-snapshots/evidence-portfolio-zh-mobile-light-linux.png). These are captured from the actual application against the real offline backend. No fabricated online state or mocked assessments. Pinned fonts make CI comparison reproducible. Labels, controls and numerical counts are readable, keyboard-labelled and responsive; mobile overflow is checked.

## Explicitly unverified and remaining

Windows builds and full Tauri desktop bundles were not executed. Broader AI qualification was not rerun; PR #7 contains prior limited real DeepSeek evidence. External handbook/rubric/domain and corporate-policy approval remain absent. Local profiles/reviewer labels are not authenticated identity or instructor authority, and distinct arithmetic variants are not independent commercial cases. No professional mastery, certification or live authorization is awarded.

Separate Codex Cloud launch was attempted through the installed CLI: task-list authentication returned **401 Unauthorized**. No separate task was launched and no login/production credentials were changed. Setup is documented in [the Cloud handoff](../CODEX-CLOUD-HANDOFF.md); that script's complete execution in a new Codex Cloud project remains unverified until that project is created.
