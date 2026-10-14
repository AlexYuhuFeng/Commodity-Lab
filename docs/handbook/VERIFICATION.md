# Interactive handbook — verification and limits

2026-10-14. Additive branch `feature/interactive-handbook`, based on PR #5 (`0dc87cf6`). No merges/releases. See [ADR 0004](../adr/0004-interactive-handbook.md) and [milestone scope](MILESTONE.md).

## Verified engineering

- **226 backend tests passed**: existing 198 regressions plus 28 handbook tests. Covers five independent numerical examples, negative margin, rounding tolerance, fresh/reproducible seeds, input validation, valid/invalid AI cards, approved references/actions, actual profile injection, future/private-answer boundaries, cross-chapter session mismatch, atomic stale submissions, resume and persisted grading. Provider responses are mocked; no real provider qualification is implied.
- **61 frontend tests passed**: existing 53 plus eight handbook tests. Reading/tool navigation, requests/answers, Chinese resume, offline and failure states, source links, incompatible-session exclusion, escaped AI prose, typed comparison/simulation cards and stale-conversation retry and last-chapter restoration.
- Production Vite build passed.
- **Seven real-backend browser journeys and 14 screenshot comparisons passed**, without updating baselines on the final run. Three handbook journeys cover hub/beach practice and resume/tool navigation, Chinese mobile regas practice, and both crude models. Existing four gas/crude Risk Lab workflows remain operational. Ten existing screenshots were refreshed solely for the added Handbook navigation item; financial/UI workflow behavior is unchanged. Four new snapshots show reading and verified exercises in English/Chinese. Screenshot threshold remains 1%; test-only OFL typography remains pinned.
- Browser practice uses the normal `practice_seed=0` request contract for reproducible screenshots. Responses/calculations are real backend results, not mocked or masked. Ordinary learner requests omit the seed and receive generated variants.
- Linux PyInstaller backend build passed with explicit handbook hidden imports. Fresh packaged smoke passed all five handbook reference exercises, persisted grading/resume, and the existing gas/refinery/inventory scenarios. Full Tauri desktop bundles remain unverified.

## Independently derived seed-zero practice references

| Chapter | Explicit reference | Result |
| --- | --- | ---: |
| Hub supply | 1,000×(60−40−1−1) + 500×(40−35) | EUR 20,500 |
| Beach-to-hub | 1,000×(40−37−1) | EUR 2,000 |
| Regas | 10,000×0.98×40 − 10,000×(30+2) | EUR 72,000 |
| Refinery supply | 10,000×(94−85−2−2) + 8,000×(85−75) | USD 130,000 |
| Owned crude inventory | 10,000×(78+1−77−2) − 8,000×(78−85) | USD 56,000 |

Prices, energy factors and costs are synthetic assumptions. Regas purchase/fees apply to purchased energy; sales apply to usable energy. Its EUR/MWh inputs are already converted: no JKM/FX/calorific conversion is performed. Inventory uses historical acquisition cost for lifecycle margin; it does not imply a second cash payment. These exercises are separate from the multi-checkpoint Risk Lab's reference values.

Server solutions are withheld until an answer is submitted. Subsequent conversation context includes public questions and submitted/verified feedback only. Assessment is provisional practice evidence; it does not alter legacy learner scores or assert mastery. Current server-side learner profiles guide AI context but are not replaced.

## Visual evidence

[English chapter](../../tauri/tauri-frontend/e2e/handbook.spec.js-snapshots/handbook-gas-reading-en-dark-linux.png), [English verified practice](../../tauri/tauri-frontend/e2e/handbook.spec.js-snapshots/handbook-gas-practice-en-dark-linux.png), [Chinese regas chapter](../../tauri/tauri-frontend/e2e/handbook.spec.js-snapshots/handbook-regas-reading-zh-mobile-light-linux.png), [Chinese verified practice](../../tauri/tauri-frontend/e2e/handbook.spec.js-snapshots/handbook-regas-practice-zh-mobile-light-linux.png). All inspected. Desktop reading/conversation columns share design tokens; Chinese mobile uses one column and has no horizontal overflow. All numbers/signs are readable in the checked examples.

## Explicitly unverified/deferred

- Real Haineng/DeepSeek calls, provider latency, response quality and grounded-answer accuracy. Uses existing credentials/settings; none added to repository. Offline mode cannot answer free-form questions and says so; provider/schema failures visibly fall back to reference cards.
- External editorial/market/domain review. Chapters are original **editorial training drafts**, not company policy, legal guidance, certified handbook content or citations to external documents. AI source links point to actual chapter passages; valid anchors do not verify every AI sentence.
- Full LNG/FX/terminal scheduling economics, complete route-capacity/balancing simulation, real market data or exchange settlements. Existing beach/LNG AI templates remain exploratory. Introductory arithmetic does not claim validated full market support.
- Windows/full Linux Tauri desktop bundles and interactive packaged UI screenshots; enterprise identity/retention; authoring CMS; handbook import pipeline; repeated mastery assessment; arbitrary AI executable scenarios; streaming dynamic cards.

Existing courses, practice, Workbench, replay, AI settings, learner profiles, Risk Lab and release workflows are preserved. Additional markets require validated conventions; none enabled by this milestone.

Pull request: [#6](https://github.com/AlexYuhuFeng/Commodity-Lab/pull/6), dependent on #5/#4. Implementation `1fab4f7b`. Remote CI evidence/status is recorded on the pull request; local checks above are independently verified.
