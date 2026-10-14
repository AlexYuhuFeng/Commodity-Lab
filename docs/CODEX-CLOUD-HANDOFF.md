# Codex Cloud handoff — Commodity Lab

Repository: `AlexYuhuFeng/Commodity-Lab`.

## Start here

Use branch **`feature/handbook-evidence-portfolio`**, based on PR #7's `feature/handbook-practice-grounding` at `4ac65065e588a9ed3e6f5de994938529e22767a7`. Do not start from main: the additive product work is still in dependent, unmerged PRs. The chain is #4 gas → #5 crude → #6 interactive handbook → #7 grounded legacy/DeepSeek → HB3 evidence portfolio.

This session used a managed cloud execution environment. The chat tools could inspect that environment but could not create a separate Codex Cloud project/task. The installed CLI offered `codex cloud exec`, but an actual `codex cloud list --json` call returned HTTP 401 (invalid authentication token); no Cloud task was launched. Reauthenticate in the Codex UI, not by placing login tokens in this repository. In Codex Cloud, select this repository and branch and run `bash scripts/setup_codex_cloud.sh` as setup with registry network access. The script installs existing Python/frontend dependencies, tests, packaging and Chromium; it creates no service/account, credentials or deployment. Node 22+ and Python 3.12 are the CI reference versions.

Run the commands in `AGENTS.md`. Keep API keys in secure environment settings only, never chat or GitHub. Configure `DEEPSEEK_API_KEY` only if live provider testing is necessary and authorized. The public Flash API model is `deepseek-flash`; legacy aliases are mapped. The browser suite explicitly disables live AI to make regressions reproducible.

## Product direction

Extend Commodity Lab into a universal interactive business-model trading handbook. Initially European gas and crude, trading-company roles only. Preserve reading + generative conversation + checked practice + legacy tools. Explain business economics, exposures, financial/commercial/operational mitigation and remaining risks. Do not define success by speculative PnL.

## Current milestone

HB3 adds versioned local evidence, named profiles, prerequisites for assessed reasoning, duplicate-resistant numerical readiness, immutable reflections, separate local reasoning review and JSON export. No institutional mastery is awarded. Full design is in `docs/adr/0006-local-competency-evidence.md`; workflow and endpoints in `docs/handbook/EVIDENCE.md`; verification in `docs/handbook/EVIDENCE-VERIFICATION.md`.

## Next executable task

Use backlog HB-10 for authenticated learner/reviewer authority and genuinely independent commercial-case evidence. First design session ownership/access boundaries for all existing local workflows, then implement an isolated adapter with reviewed role checks, migrations and authorization tests. Keep local profiles explicitly local. Do not certify learners until external rubric/domain review is recorded. HB-07 authoring/import can follow once actual handbook source material is available. External policy documents and licensed data are absent; do not invent their approval.

Before resuming, inspect the PR and final CI head, read durable progress, and run baseline tests. Record failures honestly. Do not merge any PR or publish releases as part of the handoff.
