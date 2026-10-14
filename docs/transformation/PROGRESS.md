# Durable delivery record

2026-10-09 — M1 engineering and local verification complete; [PR #4](https://github.com/AlexYuhuFeng/Commodity-Lab/pull/4) open for review.

Repository: AlexYuhuFeng/Commodity-Lab. Working checkout: `/workspace/Commodity-Lab`. Isolated branch: `feature/gas-training-vertical-slice`. Main/base: `629a72af6304b061822c15956e1b5e91868a6435`. Draft PR #3 reviewed independently; not merged or cherry-picked.

Delivered: audit, requirements/architecture/roadmap, UX constitution, two ADRs, dependency backlog, Decimal gas engine, configurable illustrative policy, schema/version checks, durable atomic local sessions, bilingual learner flow, separate diagnostics/policy/financial assessment, ungraded optional AI/offline coach, exports and regression gates.

Verified: 161 Python tests; 50 frontend tests; Vite build; two real-backend browser workflows; six screenshot comparisons; Linux packaged backend build and full scenario smoke. See VERIFICATION.md for exact numerical references and limitations.

Resume environment: `/workspace/commodity-venv/bin/python`, Node 24; browser binaries at `/workspace/commodity-browsers`. Transient test logs are under `/tmp/commodity-*.log`. Use network-enabled sandbox execution for localhost API/browser tests. No credentials or licensed data were added.

Pull request: https://github.com/AlexYuhuFeng/Commodity-Lab/pull/4. Implementation commit: `4576de5d`. The first remote CI run passed unit/build gates but failed screenshot comparison from host-font differences. Browser typography is now pinned with a test-only OFL font; [remote CI run 37914696249](https://github.com/AlexYuhuFeng/Commodity-Lab/actions/runs/37914696249) passed on final implementation commit `c2621d9f`.

Remaining review work: address reviewer feedback. Local and remote verification gates pass. Do not merge or publish releases. Next milestone: validated crude cargo financial model, then commodity-neutral packs and repeated competence/instructor evidence (M2 backlog).

User direction: every scenario uses a trading-company role, not a utility. The gas case now has fixed-price industrial sales, indexed purchases and explicit trading margin. Future crude covers cargo profit and refinery sourcing; emission-credit scenarios require validated models before enablement. Scenario version is `gas-trading-company-v1`; older experimental session records are retained and rejected for active resume to prevent silent contract changes.

Final role consistency follow-up: shared Haineng/DeepSeek system prompts now frame the learner as a trading company, including refinery/customer sourcing mandates. The disabled North American utility-role template was reworded without enabling the domain. Two bilingual prompt-contract regressions bring the full backend suite to 161 passing tests. Final role-consistency [CI run 37919599697](https://github.com/AlexYuhuFeng/Commodity-Lab/actions/runs/37919599697) passed on `8312761c`, including all unit, build, bilingual browser and visual gates.


2026-10-14 — M2A engineering implemented on isolated branch `feature/crude-risk-training`, based on M1 `ef51f422`. Two synthetic trading-company crude mandates: fixed-price refinery supply procurement and owned merchant inventory. Added typed neutral contracts/registry, signed USD Brent training swaps, pricing-window averages, grade/freight cash flows, historical purchase ledger timing, policy currency checks, shared atomic sessions, bilingual UX and case-specific offline/AI coaching. Existing gas endpoint/state and workflows are preserved. ADR 0003 records dispatch/compatibility decisions.

Resume verification: 198 backend tests passed; 53 frontend tests passed; Vite build passed. Prior environment Linux packaged backend build and three-scenario API smoke passed. A resumed browser comparison exposed scroll anchoring in one new crude screenshot; fixed with explicit container alignment. Final four browser workflows and all ten screenshot comparisons pass without updating baselines. See M2-VERIFICATION.md for numerical references, screenshot links, remaining domain sign-off and unverified desktop/provider checks. Logs now use durable `/workspace/scratch/commodity-m2-*.log` rather than transient /tmp.

Delivered dependent [PR #5](https://github.com/AlexYuhuFeng/Commodity-Lab/pull/5), targeting `feature/gas-training-vertical-slice` (PR #4 remains open). Implementation commit `e8e89ef8`. Fresh resumed packaged API smoke passes both crude references and legacy gas, including persisted settlement reads. Next action: monitor PR CI and address review feedback. CI pull-request filter now includes dependent branches. Do not merge or publish. Next milestone: external review of crude conventions/references, reviewed pack authoring lifecycle, then repeated competency evidence/instructor review. Emission credits remain disabled pending validated models.


2026-10-14 — HB1 interactive handbook engineering implemented on `feature/interactive-handbook`, based on PR #5 `0dc87cf6`. User direction: universal business-model foundation; initially European gas (hub, beach, LNG regas) and crude; preserve current generative/interactive experience and existing work. Five bilingual editorial-draft chapters, grounded typed-card conversation, current learner-profile injection, optional compatible as-of Risk Lab context, persisted practice/remediation, checked generated numerical variants and links to existing tools are implemented. ADR 0004 and UI constitution govern the additive design.

Verification: 226 backend tests; 61 frontend tests; Vite build; seven real-backend browser journeys and 14 final screenshot comparisons pass. New snapshots use ordinary reproducible-seed API requests, with real calculations. Linux backend packaging passes. Fresh packaged smoke passes all five handbook exercises plus the three legacy gas/crude reference cases; see handbook/VERIFICATION.md and durable `/workspace/scratch/commodity-hb-*.log`. Real provider calls, external domain/editorial sign-off and full desktop bundles remain unverified. Chapters never claim authoritative policy/full beach or LNG simulator coverage. HB backlog records remaining work.

Next action: finish packaged smoke, commit/push and open dependent PR against `feature/crude-risk-training`; monitor CI. Do not merge PRs #4/#5 or publish. Next milestone: review/import the user's handbook content, qualify configured AI responses, then extend validated route/regas models and repeated competency evidence.
