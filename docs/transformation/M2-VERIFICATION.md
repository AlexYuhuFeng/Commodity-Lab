# M2A verification and limitations

Engineering verification: 2026-10-14. Branch `feature/crude-risk-training`, based on PR #4 (`ef51f422`). This is a dependent change; neither pull request is merged.

## Independent financial references

See [M2-CRUDE.md](M2-CRUDE.md) for manually derived arithmetic. `tests/test_crude_training.py` checks explicit expected values, alternative trade decompositions, both hedge directions, multiple defensible strategies, collateral under an adverse short rally, fractional quantities and six-decimal weighted-price rounding.

| Result, USD | Refinery supply | Owned inventory |
| --- | ---: | ---: |
| Physical sales | 47,000,000 | 22,500,000 |
| Purchase cash flow / historical cost | −46,500,000 | −23,100,000 |
| Freight | −1,250,000 | −450,000 |
| Swap receipts | 4,480,000 | 1,440,000 |
| Lifecycle trading margin before other costs | 3,730,000 | 390,000 |
| Settlement-date net cash flow | 3,730,000 | 23,490,000 |
| Peak sampled collateral | 4,128,000 | 1,920,000 |

Inventory purchase occurred September 15, before both decisions. It affects lifecycle margin but is excluded from November 30 settlement cash. Three synthetic fixings determine the November benchmark and grade averages; these conventions are not real Brent assessments or exchange settlement.

## Automated and application checks

- Backend: **198 tests passed**, including 37 new crude tests and the existing 161 regressions. Checks include invalid packs, convention/currency mismatches, policy direction and ratios, approval and liquidity, atomic concurrency, stale checkpoints, saved legacy gas sessions, future-information exclusion and read-only coaching.
- Frontend: **53 tests passed**, including USD session creation, signed inventory decisions and explicit conventions, independent saved gas/crude sessions, Chinese resume and blocked proposal assessment.
- Production frontend build passed.
- Browser: **four real-backend journeys passed with all ten screenshot comparisons**, run without updating baselines. Existing gas screenshots retain their baselines; four crude baselines cover English setup/settlement and Chinese mobile inventory decisions/dated cash flow. Screenshots were inspected. Crude mobile monetary rows stack labels and values to keep negative signs attached to amounts. Snapshot scrolling uses an explicit container position to avoid depending on prior automatic scroll anchoring.
- Linux PyInstaller backend built and complete gas/refinery/inventory API smoke passed in the preceding execution environment. The smoke reconciled margins and settlement-date cash with the table and verified persisted crude settlement reads. Fresh resumed-environment smoke also passed all three cases and persisted crude settlement reads.

## Evidence

Committed real application snapshots: [English setup](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/crude-setup-en-dark-linux.png), [English settlement](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/crude-settlement-en-dark-linux.png), [Chinese inventory form](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/crude-inventory-form-zh-mobile-light-linux.png), [Chinese cash ledger](../../tauri/tauri-frontend/e2e/risk-training.spec.js-snapshots/crude-inventory-ledger-zh-mobile-light-linux.png). Transient logs are under `/workspace/scratch/commodity-m2-*.log`; they contain no credentials.

## Unverified and deferred

No external commodity specialist has signed off the synthetic conventions or reference fixtures. Registry status `synthetic_reference_validated` means schema/financial regression validation, not corporate authorization or external certification. M2-01 remains in progress until that sign-off; the implementation is reviewable.

Windows and full Linux Tauri desktop bundles, interactive packaged desktop screenshots, real Haineng/DeepSeek requests, provider quality and availability are **unverified**. Optional coaching uses existing integration and tested offline fallback; numerical authority remains deterministic.

No live/licensed price source, real exchange lots or margin, options, FX, fees/tax/financing, demurrage, emission-credit model, enterprise access control or instructor publishing lifecycle is claimed. AI-authored packs cannot be uploaded or executed; semantic validation and an immutable registered catalog are the foundation, with author/reviewer lifecycle and quarantine still pending.

Pull request: [#5](https://github.com/AlexYuhuFeng/Commodity-Lab/pull/5), dependent on #4; implementation `e8e89ef8`. Remote CI status is available on the pull request; local results above are independently verified.
