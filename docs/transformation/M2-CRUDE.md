# M2A — trading-company crude risk workflows

Scope: M2-01 and the reviewed-pack/registry foundation of M2-02. Build on PR #4 without merging it. A dependent PR targets `feature/gas-training-vertical-slice`; no main merge or release is authorized.

## Roles and reviewed synthetic contracts

1. **Refinery procurement mandate**: a trading company resells nominated November crude to a refinery at fixed USD 94/bbl. It sources up to 600,000 bbl at the November Brent training average plus grade differential, and pays freight. A contractual quantity option reduces the nominated cargo to 500,000 bbl at decision 2. The trading company, not the refinery operator, owns the decision.
2. **Merchant inventory**: a trading company already owns 300,000 bbl purchased on September 15 at USD 77/bbl. It will sell in November at the Brent training average plus grade differential and pay outbound freight. The purchase is a historical cash flow and cost basis; it is not a second settlement payment. Short Brent swaps can protect the inventory's downside.

The November pricing window is November 5–25, with **three equally weighted synthetic fixings** on November 5, 15 and 25. This educational convention is not a claim about Dated Brent, ICE futures or real daily-assessment contracts. Weighted prices use Decimal arithmetic and ROUND_HALF_UP to six decimal places; monetary outputs round to cents. Both decisions occur before the pricing window. Paper contracts settle against the same training benchmark average, in USD/bbl; positions are barrel notionals, not exchange lots. Grade basis and freight remain unhedged.

## Independent reference examples

Procurement: quotes 80 then 86; final fixings 84,90,96 average 90. Grade fixings 1,3,5 average 3; freight final 2.50/bbl. Buy 480,000 paper bbl at 80, then resize to 400,000 at 86. Paper receipts = 480,000×10 − 80,000×4 = 4,480,000. Independently: 80,000×6 + 400,000×10 = 4,480,000.

At final 500,000 bbl: sales 47,000,000; purchases −46,500,000; freight −1,250,000; unhedged physical margin −750,000; hedged trading margin **3,730,000**. Net sourcing cost 43,270,000. Volume-adjusted initial budget 500,000×(80+1+2)=41,500,000, budget variance −1,770,000. Adverse physical-margin shock 6,250,000; paper offset 71.68%. Sampled peak collateral 4,128,000 before resizing.

Inventory: quotes 80 then 76; final fixings 70,74,78 average 74. Grade final average 1; freight 1.50/bbl. Hold 240,000 bbl short at 80. Paper receipts = 240,000×6 = 1,440,000. Sales 22,500,000; historical purchase −23,100,000; outbound freight −450,000. Unhedged margin −1,050,000; hedged trading margin **390,000**. Final settlement cash receipt **23,490,000**, distinct from lifecycle margin because purchase payment occurred earlier. Initial volume-adjusted physical-margin expectation = 300,000×(80+2−1−77)=1,200,000. Adverse margin shock 2,250,000; paper offset 64%. Peak sampled collateral 1,920,000.

Rising-price short reference: short 240,000 at 80 marked at 90 loses 2,400,000; simplified 10% initial collateral = 2,160,000; combined estimate = 4,560,000. No model or prose coach may override these results.

## Engineering contract and quality gates

Typed commodity-neutral packs validate chronology, units/currency, fixed-price terms, pricing window, weighted fixings, final benchmark/basis consistency, and obligation continuity after the last decision. Registry dispatch preserves the gas API/session state and its reference results. No submitted pack becomes executable: learners select reviewed registered versions. Invalid candidate packs fail schema/semantic validation; an author/reviewer publishing lifecycle and AI-generated executable packs remain future work.

Policy operates on total signed target, supported instrument, matching commodity/unit/currency/pricing/delivery/window and current eligible physical volume. Corporate illustrative defaults remain 80%, backed direction, no options and approval constraints. More permissive profiles are simulation-only. Monetary limits carry their currency; an EUR gas limit cannot be silently reused for USD crude.

Client uses the existing commodity selector, separate saved-session keys per commodity, and scenario selection within the crude desk. Same Brief → evidence → decision → review → settlement workflow, with ledger timing and case-specific coaching. Gas regressions, both hedge directions, resizing, pricing average, historical versus settlement cash flows, leakage, restart and concurrency must pass. Bilingual browser journeys and inspected screenshot comparisons are required.

Not included: real Dated Brent assessments, exchange settlement/margin, options, FX, taxes, financing, demurrage estimation, instructor sign-off, enterprise access control, or emission-credit support.
