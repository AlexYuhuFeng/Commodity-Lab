"""Registered synthetic crude packs. Prices are educational, not licensed assessments."""
from types import MappingProxyType
from core.training_contracts import ScenarioPack

CONVENTIONS = {
    "commodity": "crude_oil", "benchmark": "Brent", "unit": "bbl", "currency": "USD", "instrument": "brent_swap",
    "delivery_period": "2026-11", "pricing_period": "2026-11", "pricing_window_start": "2026-11-05",
    "pricing_window_end": "2026-11-25", "settlement_date": "2026-11-30",
}


def observation(day, quote, basis, freight, quantity, en, zh):
    return {"date": day, "benchmark_price": quote, "grade_basis": basis, "freight_per_unit": freight,
            "eligible_quantity": quantity, "fact": {"en": en, "zh": zh}}


def fixings(benchmark, basis):
    return tuple({"date": day, "benchmark_price": p, "grade_basis": b, "weight": "1"}
                 for day, p, b in zip(("2026-11-05", "2026-11-15", "2026-11-25"), benchmark, basis))


REFINERY = ScenarioPack(
    version="crude-refinery-procurement-v1",
    title={"en": "Crude refinery procurement mandate", "zh": "原油炼厂采购委托"},
    conventions=CONVENTIONS,
    physical={"kind": "fixed_sale_indexed_purchase", "fixed_price": "94"},
    observations=(
        observation("2026-10-01", "80", "1", "2", "600000",
                    "You run a trading-company cargo desk, sourcing November crude for a refinery customer. Resell nominated barrels at fixed $94/bbl, up to 600,000 bbl. Buy at the November Brent training average plus grade differential and pay freight. Protect the commercial margin; you do not operate the refinery.",
                    "你负责贸易公司的原油船货业务，为炼厂客户采购11月原油。按固定94美元/桶转售提名量，上限600,000桶；按11月Brent训练均价加品级价差采购并支付运费。保护商业利润，你不是炼厂运营商。"),
        observation("2026-10-15", "86", "2", "2.5", "500000",
                    "Shipping disruption raises the Brent quote, grade differential and freight. The customer exercises a contractual quantity option for 500,000 bbl. Reassess existing paper against the smaller matching physical obligation before resizing; the November pricing window has not started.",
                    "航运中断推高Brent报价、品级价差和运费。客户行使合同数量选择权，提名量降至500,000桶。调整头寸前，重新核对现有纸货与减少后的实货义务；11月定价窗口尚未开始。"),
        observation("2026-11-30", "90", "3", "2.5", "500000",
                    "The three synthetic November fixings average $90/bbl for Brent and $3/bbl for grade differential. Deliver 500,000 bbl to the refinery customer at the contracted $94/bbl; freight is $2.50/bbl. Sales, purchase, freight and swap cash flows settle separately.",
                    "11月三次合成定价的Brent均价为90美元/桶，品级价差均值为3美元/桶。按合同94美元/桶向炼厂客户交付500,000桶，运费为2.50美元/桶。销售、采购、运费与掉期现金流分别结算。"),
    ),
    fixings=fixings(("84", "90", "96"), ("1", "3", "5")),
)

INVENTORY = ScenarioPack(
    version="crude-merchant-inventory-v1",
    title={"en": "Crude merchant inventory risk", "zh": "原油贸易库存风险"},
    conventions=CONVENTIONS,
    physical={"kind": "owned_inventory_indexed_sale", "fixed_price": "77", "historical_purchase_date": "2026-09-15"},
    observations=(
        observation("2026-10-01", "80", "2", "1", "300000",
                    "You manage a trading-company inventory book. You already own 300,000 bbl, bought and paid for on September 15 at $77/bbl. Sell the cargo in November at the Brent training average plus grade differential and pay outbound freight. Protect resale value and trading profit; the refinery is your customer.",
                    "你管理贸易公司的库存账簿。已在9月15日按77美元/桶购入并支付300,000桶原油。11月按Brent训练均价加品级价差出售船货，并支付出港运费。保护转售价值与交易利润，炼厂是你的客户。"),
        observation("2026-10-15", "76", "1.5", "1.5", "300000",
                    "Weaker refinery demand lowers the Brent quote and grade differential. Tank congestion lifts outbound freight to $1.50/bbl. The full 300,000 bbl remains owned inventory; consider short benchmark protection and collateral risk if prices rebound.",
                    "炼厂需求减弱，Brent报价与品级价差下降。储罐拥堵使出港运费升至1.50美元/桶。300,000桶仍为自有库存；考虑基准价格空头保护，以及价格反弹时的抵押资金风险。"),
        observation("2026-11-30", "74", "1", "1.5", "300000",
                    "The three synthetic November fixings average $74/bbl for Brent and $1/bbl for grade differential. Sell 300,000 bbl, pay $1.50/bbl outbound freight and settle paper. The September acquisition remains a historical cost and cash flow, not another payment today.",
                    "11月三次合成定价的Brent均价为74美元/桶，品级价差均值为1美元/桶。出售300,000桶，支付1.50美元/桶出港运费并结算纸货。9月采购仍是历史成本与现金流，并非今天再次付款。"),
    ),
    fixings=fixings(("70", "74", "78"), ("0", "1", "2")),
)

PACKS = MappingProxyType({pack.version: pack for pack in (REFINERY, INVENTORY)})
