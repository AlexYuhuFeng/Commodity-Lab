"""Deterministic introductory arithmetic, independent of LLM prose."""
from decimal import Decimal, ROUND_HALF_UP
from core.handbook_content import CHAPTERS, text
D = Decimal
VERSION = "handbook-practice-v1"


def create_practice(chapter_id: str, seed: int) -> tuple[dict, dict]:
    chapter = CHAPTERS[chapter_id]
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 1000000:
        raise ValueError("invalid_seed")
    crude = chapter.commodity == "crude_oil"
    quantity = D(10000 if crude or chapter_id == "gas-lng-regas" else 1000) + D(seed % 20) * 100
    currency, unit = ("USD", "bbl") if crude else ("EUR", "MWh")
    givens = {"quantity":str(quantity),"currency":currency,"unit":unit,"pricing_period":"same synthetic month","seed":seed}
    if chapter_id == "gas-beach-hub":
        hub = D(40 + seed % 15); discount = D(3 + seed % 5); route = D(1)
        givens.update(hub_sales_price=str(hub), beach_purchase_price=str(hub-discount), route_cost_per_unit=str(route))
        result = quantity * (discount-route)
        steps = f"{quantity} × ({hub} − {hub-discount} − {route}) = {result} {currency}"
        prompt = text("Calculate the matched beach-to-hub physical margin. Both legs have equal delivered energy, one currency and the same pricing window. Only stated route costs apply.","计算匹配的上岸点至枢纽实货利润。两端交付能量相等、同币种、同定价窗口，仅计入给定线路成本。")
    elif chapter_id == "gas-lng-regas":
        price = D(40 + seed % 10); cost = D(30 + seed % 5); factor = D("0.98"); fee = D(2)
        usable = quantity * factor
        givens.update(sales_price=str(price), purchase_price=str(cost), usable_energy_factor=str(factor), terminal_fee_per_purchased_unit=str(fee))
        result = usable * price - quantity * (cost+fee)
        steps = f"{quantity} × {factor} = {usable} MWh; {usable} × {price} − {quantity} × ({cost} + {fee}) = {result} EUR"
        prompt = text("Calculate simplified regas resale margin. All energy is already converted to MWh and all prices to EUR/MWh. Sell only usable energy; purchase and terminal fee apply to purchased energy. Excludes freight, FX, financing, schedules and other charges.","计算简化气化转售利润。全部能量已换算为MWh、价格为欧元/MWh。仅销售可用能量；采购与接收站费按采购能量计算。不含运费、汇率、融资、排程及其他收费。")
    else:
        inventory = chapter_id == "crude-inventory"
        entry = D((85 if inventory else 75 if crude else 35) + seed % 15)
        final = entry + D(-7 if inventory else 10 if crude else 5)
        basis = D(1 if inventory or not crude else 2); freight = D(2 if crude else 1)
        fixed = D(77 if inventory else 94 if crude else 60)
        hedge = quantity * D("0.8" if crude else "0.5") * (-1 if inventory else 1)
        sales = quantity * (final+basis if inventory else fixed)
        purchase = -quantity * (fixed if inventory else final+basis)
        shipment = -quantity * freight; paper = hedge * (final-entry)
        result = sales + purchase + shipment + paper
        givens.update(fixed_sales_price=None if inventory else str(fixed),historical_purchase_price=str(fixed) if inventory else None,benchmark_entry=str(entry),benchmark_settlement=str(final),physical_basis=str(basis),freight_per_unit=str(freight),signed_paper_quantity=str(hedge))
        steps = f"sales {sales}; purchase cost {purchase}; freight {shipment}; paper {hedge} × ({final} − {entry}) = {paper}; lifecycle margin = {result} {currency}"
        prompt = text("Calculate lifecycle trading margin: physical sales minus purchase cost and freight, plus signed benchmark-swap cash flow. All pricing windows match; no other costs. A historical inventory purchase affects margin but is not paid again at settlement.","计算全周期交易利润：实货销售减采购成本及运费，加有符号基准掉期现金流。定价窗口全部匹配，无其他成本。历史库存采购影响利润，但不会在结算时再次支付。")
    answer = result.quantize(D("0.01"),rounding=ROUND_HALF_UP)
    public = {"version":VERSION,"chapter_id":chapter_id,"prompt":prompt,"givens":givens,"answer_currency":currency,"answer_unit":"money","evidence_status":"provisional_practice_not_mastery"}
    zh_steps=steps.replace("sales", "销售").replace("purchase cost", "采购成本").replace("freight", "运费").replace("paper", "纸货").replace("lifecycle margin", "全周期利润")
    solution = {"answer":str(answer),"working":text(steps,zh_steps),"remediation":chapter.sections[1].id}
    return public, solution


def assess(solution: dict, answer: Decimal) -> dict:
    if not answer.is_finite(): raise ValueError("finite_answer_required")
    correct = abs(answer-D(solution["answer"])) <= D("0.01")
    return {"correct":correct,"expected_answer":solution["answer"],"working":solution["working"],"remediation_section":solution["remediation"],"evidence_status":"provisional_practice_not_mastery"}
