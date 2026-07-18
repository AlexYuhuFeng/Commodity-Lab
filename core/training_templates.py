"""Business and knowledge-point templates for AI-generated commodity training cases."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


_KNOWLEDGE_POINTS: list[dict[str, Any]] = [
    {
        "id": "exposure_objective",
        "label": {"en": "Exposure and hedge objective", "zh": "敞口与套保目标"},
        "description": {
            "en": "Identify whether the business is naturally long, short, or spread-exposed before choosing any instrument.",
            "zh": "先判断业务天然处于多头、空头还是价差敞口，再选择套保工具。",
        },
    },
    {
        "id": "forward_curve_carry",
        "label": {"en": "Forward structure and carry", "zh": "远期结构与持有成本"},
        "description": {
            "en": "Understand contango, backwardation, cost of carry, and roll yield before sizing or timing a hedge.",
            "zh": "在确定套保规模和时点前，理解 Contango、Backwardation、持有成本和展期收益。",
        },
    },
    {
        "id": "physical_paper_matching",
        "label": {"en": "Physical-paper matching", "zh": "实货与纸货匹配"},
        "description": {
            "en": "Match physical commodity obligations with futures, swaps, basis, FX, and options as one strategy.",
            "zh": "把商品实货义务与期货、掉期、基差、汇率和期权作为一个组合策略匹配。",
        },
    },
    {
        "id": "outright_price",
        "label": {"en": "Outright price hedge", "zh": "单边价格套保"},
        "description": {
            "en": "Use futures, forwards, or swaps to reduce exposure to absolute commodity price moves.",
            "zh": "使用期货、远期或掉期降低商品绝对价格波动风险。",
        },
    },
    {
        "id": "basis_spread",
        "label": {"en": "Basis, hub, and calendar spread", "zh": "基差、枢纽与跨期价差"},
        "description": {
            "en": "Separate outright commodity price risk from location, hub, tenor, unit, and FX basis.",
            "zh": "区分绝对价格风险与地点、枢纽、期限、单位和汇率基差风险。",
        },
    },
    {
        "id": "crude_benchmark_basis",
        "label": {"en": "Crude benchmark, grade, and location basis", "zh": "原油基准、品级与地点基差"},
        "description": {
            "en": "Separate Brent, WTI, Dubai, grade differential, delivery location, and loading-window effects.",
            "zh": "拆分 Brent、WTI、Dubai、品级贴水、交割地点和装船窗口影响。",
        },
    },
    {
        "id": "inventory_freight_roll",
        "label": {"en": "Inventory, freight, and roll risk", "zh": "库存、运费与展期风险"},
        "description": {
            "en": "Check holding period, chartering or pipeline cost, margin, credit, and futures roll risk.",
            "zh": "检查持有期、租船或管输成本、保证金、信用和期货展期风险。",
        },
    },
    {
        "id": "fx",
        "label": {"en": "FX and unit normalization", "zh": "汇率与单位归一化"},
        "description": {
            "en": "Normalize p/th, EUR/MWh, USD/MMBtu, and GBP/EUR/USD cash flows before comparing or hedging.",
            "zh": "比较或套保前，先把 p/th、EUR/MWh、USD/MMBtu 以及 GBP/EUR/USD 现金流归一化。",
        },
    },
    {
        "id": "options_optionality",
        "label": {"en": "Options and operational optionality", "zh": "期权与运营可选性"},
        "description": {
            "en": "Use caps, floors, collars, swing rights, cargo diversion, and regas optionality when payoff is asymmetric.",
            "zh": "当收益结构不对称时，使用上限、下限、领口、摆动权、船货转运和气化可选性。",
        },
    },
    {
        "id": "hedge_ratio_cross_hedge",
        "label": {"en": "Hedge ratio and cross-hedge quality", "zh": "套保比率与交叉套保质量"},
        "description": {
            "en": "Size the hedge by volume, tenor, price sensitivity, and correlation when the hedging instrument is imperfect.",
            "zh": "当工具不能完全匹配现货敞口时，按数量、期限、价格敏感度和相关性确定套保比例。",
        },
    },
    {
        "id": "capacity_storage_balancing",
        "label": {"en": "Capacity, storage, and balancing", "zh": "运力、储气与平衡"},
        "description": {
            "en": "Check pipeline capacity, nominations, storage inventory, imbalance exposure, and route constraints.",
            "zh": "检查管输运力、提名、库存、偏差敞口和路径约束。",
        },
    },
    {
        "id": "risk_controls",
        "label": {"en": "Execution and risk controls", "zh": "执行与风控"},
        "description": {
            "en": "Consider liquidity, margin, credit, limits, settlement, roll risk, and operational cut-off windows.",
            "zh": "考虑流动性、保证金、信用、限额、结算、移仓风险和运营截点。",
        },
    },
]


_BUSINESS_GROUPS: list[dict[str, Any]] = [
    {"id": "foundation", "label": {"en": "Foundations", "zh": "套保基础"}},
    {"id": "crude", "label": {"en": "Crude oil hedging", "zh": "原油套保"}},
    {"id": "procurement", "label": {"en": "Procurement", "zh": "采购端"}},
    {"id": "sales", "label": {"en": "Sales", "zh": "销售端"}},
    {"id": "integrated", "label": {"en": "Integrated strategy", "zh": "组合策略"}},
]


_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "foundation_hedging_basics",
        "group": "foundation",
        "business_type": {"en": "General hedging foundations", "zh": "套保通识基础"},
        "title": {"en": "General hedging tools", "zh": "通识金融工具"},
        "summary": {
            "en": "Inter-commodity foundations covering exposure, forward structure, futures/swaps, basis, options, hedge ratio, physical-paper matching, and controls.",
            "zh": "跨品种通识课程：覆盖敞口、远期结构、期货/掉期、基差、期权、套保比率、实货/纸货匹配和风控。",
        },
        "coverage": ["exposure_objective", "forward_curve_carry", "outright_price", "physical_paper_matching", "basis_spread", "hedge_ratio_cross_hedge", "options_optionality", "fx", "risk_controls"],
        "gas_models": ["simple_procurement"],
        "knowledge_points": ["exposure_objective", "forward_curve_carry", "outright_price", "physical_paper_matching", "basis_spread", "hedge_ratio_cross_hedge", "options_optionality", "fx", "risk_controls"],
        "required_curves": ["PRIMARY_BENCHMARK", "HEDGE_BENCHMARK"],
        "suggested_leg_types": ["physical", "swap"],
        "lesson_sequence": ["identify exposure", "read forward structure", "choose instrument", "set hedge ratio", "match physical and paper legs", "check controls", "explain residual risk"],
    },
    {
        "id": "crude_oil_hedging_basics",
        "group": "crude",
        "business_type": {"en": "Crude procurement / sales hedging", "zh": "原油采购/销售套保"},
        "title": {"en": "How should Brent / WTI exposure be hedged?", "zh": "Brent / WTI 敞口如何套保？"},
        "summary": {
            "en": "A crude oil case covering physical cargo exposure, futures or swaps, calendar and grade basis, inventory, freight, and risk controls.",
            "zh": "原油套保案例：覆盖实货船货敞口、期货或掉期、月差与品级基差、库存、运费和风控检查。",
        },
        "coverage": [
            "exposure_objective",
            "physical_paper_matching",
            "outright_price",
            "basis_spread",
            "crude_benchmark_basis",
            "inventory_freight_roll",
            "risk_controls",
        ],
        "gas_models": ["crude_cargo_hedge", "crude_calendar_basis", "crude_inventory_hedge"],
        "knowledge_points": [
            "exposure_objective",
            "physical_paper_matching",
            "outright_price",
            "crude_benchmark_basis",
            "inventory_freight_roll",
            "risk_controls",
        ],
        "required_curves": ["BRENT", "WTI", "DUBAI", "BRENT_WTI_SPREAD"],
        "suggested_leg_types": ["physical", "future", "swap", "basis"],
        "lesson_sequence": [
            "map crude benchmark and physical exposure",
            "separate flat price from grade/location/calendar basis",
            "match physical cargo or inventory with futures/swaps",
            "check freight, margin, roll, credit, and execution risk",
        ],
    },
    {
        "id": "gas_local_market_procurement",
        "group": "procurement",
        "business_type": {"en": "Local-market gas procurement", "zh": "本地市场天然气采购"},
        "title": {"en": "Local-market procurement cost hedge", "zh": "本地市场采购成本套保"},
        "summary": {
            "en": "A single-hub, single-currency procurement case focused on price direction, hedge volume, and tenor.",
            "zh": "单一枢纽、单一币种采购案例，训练价格方向、套保数量和期限匹配。",
        },
        "coverage": ["exposure_objective", "outright_price", "physical_paper_matching", "forward_curve_carry", "risk_controls"],
        "gas_models": ["simple_procurement", "eex_ocm_procurement"],
        "knowledge_points": ["exposure_objective", "outright_price", "physical_paper_matching", "risk_controls"],
        "required_curves": ["TTF"],
        "suggested_leg_types": ["physical", "swap"],
        "lesson_sequence": ["identify purchase exposure", "choose hedge direction", "match volume and tenor", "check execution controls"],
    },
    {
        "id": "gas_local_market_sale",
        "group": "sales",
        "business_type": {"en": "Local-market gas sales", "zh": "本地市场天然气销售"},
        "title": {"en": "Local-market sales revenue hedge", "zh": "本地市场销售收入套保"},
        "summary": {
            "en": "A single-hub, single-currency sales case covering fixed, floating, or formula-priced revenue exposure.",
            "zh": "单一枢纽、单一币种销售案例，覆盖固定价、浮动价和公式价收入敞口。",
        },
        "coverage": ["exposure_objective", "outright_price", "physical_paper_matching", "risk_controls"],
        "gas_models": ["customer_indexed_sale", "efet_bilateral_sale"],
        "knowledge_points": ["exposure_objective", "outright_price", "physical_paper_matching", "risk_controls"],
        "required_curves": ["TTF"],
        "suggested_leg_types": ["physical", "swap"],
        "lesson_sequence": ["identify sales exposure", "separate fixed and floating price", "choose hedge direction", "match volume and tenor"],
    },
    {
        "id": "procurement_beach_to_germany",
        "group": "procurement",
        "business_type": {"en": "Cross-regional gas supply and sales", "zh": "跨区域天然气供销"},
        "title": {"en": "Cross-hub supply and sales basis hedge", "zh": "跨枢纽供销基差套保"},
        "summary": {
            "en": "A cross-regional European gas case covering hub and delivery basis, transport route, and physical-paper matching.",
            "zh": "欧洲天然气跨区域供销案例，覆盖枢纽与交割基差、运输路径和实货/纸货匹配。",
        },
        "coverage": ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
        "gas_models": ["gsa_procurement", "cross_border_sale", "pipeline_capacity"],
        "knowledge_points": ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching"],
        "required_curves": ["TTF", "NBP", "EURGBP", "TTF_NBP_SPREAD"],
        "suggested_leg_types": ["physical", "basis", "fx", "capacity"],
        "lesson_sequence": ["map supply and delivery obligations", "separate outright price from hub basis", "add route and capacity checks", "explain residual risk"],
    },
    {
        "id": "gas_cross_currency_settlement",
        "group": "integrated",
        "business_type": {"en": "Cross-currency gas supply and sales", "zh": "跨币种天然气供销"},
        "title": {"en": "Cross-currency gas supply and sales hedge", "zh": "跨币种天然气供销套保"},
        "summary": {
            "en": "A gas supply-and-sales case where pricing, settlement, and functional currencies differ.",
            "zh": "商品计价、合同结算与本位币不同的天然气供销案例。",
        },
        "coverage": ["physical_paper_matching", "basis_spread", "fx", "risk_controls"],
        "gas_models": ["cross_border_sale", "customer_indexed_sale"],
        "knowledge_points": ["physical_paper_matching", "basis_spread", "fx", "risk_controls"],
        "required_curves": ["TTF", "NBP", "EURGBP", "TTF_NBP_SPREAD"],
        "suggested_leg_types": ["physical", "basis", "fx"],
        "lesson_sequence": ["hedge commodity exposure", "identify FX cash flows", "match FX direction and notional", "align tenor and settlement"],
    },
    {
        "id": "gas_transport_capacity_hedge",
        "group": "integrated",
        "business_type": {"en": "Cross-regional transport and delivery", "zh": "跨区域运输与交付"},
        "title": {"en": "Cross-regional transport and delivery coverage", "zh": "跨区域运输与交付保障"},
        "summary": {
            "en": "A delivery case combining the physical-paper hedge with capacity, nominations, congestion, and operational cut-offs.",
            "zh": "将运力、提名、拥堵和运营截点纳入实货/纸货套保的交付案例。",
        },
        "coverage": ["basis_spread", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
        "gas_models": ["pipeline_capacity", "cross_border_sale"],
        "knowledge_points": ["basis_spread", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
        "required_curves": ["TTF", "NBP", "TTF_NBP_SPREAD"],
        "suggested_leg_types": ["physical", "basis", "capacity"],
        "lesson_sequence": ["map route and delivery window", "reserve capacity", "check nominations and imbalance", "identify unhedged performance risk"],
    },
    {
        "id": "procurement_eex_ocm_window",
        "group": "procurement",
        "business_type": {"en": "EEX / OCM execution window", "zh": "EEX / OCM 窗口采购"},
        "title": {"en": "Short-term procurement through EEX / OCM windows", "zh": "EEX / OCM 窗口短期采购"},
        "summary": {
            "en": "A short-term procurement case where the desk must decide how to use exchange, OCM, futures, or swaps during intraday volatility.",
            "zh": "短期采购窗口案例：在日内波动中判断如何使用交易所、OCM、期货或掉期完成采购和套保。",
        },
        "coverage": ["outright_price", "basis_spread", "hedge_ratio_cross_hedge", "risk_controls"],
        "gas_models": ["eex_ocm_procurement", "balancing_window"],
        "knowledge_points": ["outright_price", "basis_spread", "hedge_ratio_cross_hedge", "risk_controls"],
        "required_curves": ["TTF", "OCM", "INTRADAY_SPREAD"],
        "suggested_leg_types": ["physical", "future", "swap"],
        "lesson_sequence": ["set purchase window", "compare spot vs derivative hedge", "check liquidity and cut-off", "explain execution risk"],
    },
    {
        "id": "procurement_lng_cargo",
        "group": "procurement",
        "business_type": {"en": "LNG cargo procurement", "zh": "LNG 船货采购"},
        "title": {"en": "LNG cargo with JKM / TTF optionality", "zh": "带 JKM / TTF 可选性的 LNG 船货采购"},
        "summary": {
            "en": "A cargo procurement case covering JKM/TTF conversion, FX, freight timing, diversion optionality, and regas exposure.",
            "zh": "LNG 船货采购案例，覆盖 JKM/TTF 转换、汇率、运费时点、转港可选性和气化敞口。",
        },
        "coverage": ["basis_spread", "fx", "options_optionality", "risk_controls"],
        "gas_models": ["lng_cargo_procurement", "lng_regas_sale"],
        "knowledge_points": ["basis_spread", "fx", "options_optionality", "risk_controls"],
        "required_curves": ["TTF", "JKM", "EURUSD", "TTF_JKM_SPREAD"],
        "suggested_leg_types": ["physical", "swap", "basis", "fx", "option"],
        "lesson_sequence": ["define cargo index and discharge window", "compare JKM and TTF economics", "hedge asymmetric downside", "state residual operational risk"],
    },
    {
        "id": "sales_efet_bilateral",
        "group": "sales",
        "business_type": {"en": "Bilateral EFET sale", "zh": "EFET 双边销售"},
        "title": {"en": "EFET bilateral sale with hub mismatch", "zh": "EFET 双边销售与枢纽错配"},
        "summary": {
            "en": "A sales case where the delivery point, customer price formula, credit exposure, and hedge instrument do not perfectly match.",
            "zh": "销售端案例：交割点、客户定价公式、信用敞口和套保工具不能完全匹配时如何设计组合动作。",
        },
        "coverage": ["physical_paper_matching", "basis_spread", "hedge_ratio_cross_hedge", "risk_controls"],
        "gas_models": ["efet_bilateral_sale", "cross_border_sale"],
        "knowledge_points": ["physical_paper_matching", "basis_spread", "hedge_ratio_cross_hedge", "risk_controls"],
        "required_curves": ["TTF", "NBP", "TTF_NBP_SPREAD"],
        "suggested_leg_types": ["physical", "basis", "swap"],
        "lesson_sequence": ["read physical delivery obligation", "match sales index", "add credit and settlement checks", "compare target vs user legs"],
    },
    {
        "id": "sales_lng_regas",
        "group": "sales",
        "business_type": {"en": "LNG regas sale", "zh": "LNG 船货气化销售"},
        "title": {"en": "Regasified LNG sale during market selloff", "zh": "市场下跌中的 LNG 气化销售"},
        "summary": {
            "en": "A sales case where LNG is regasified and sold while the market is falling, requiring price, basis, optionality, and performance protection.",
            "zh": "市场下跌时的 LNG 气化销售案例，训练价格、基差、可选性和履约保护。",
        },
        "coverage": ["outright_price", "basis_spread", "options_optionality", "capacity_storage_balancing", "risk_controls"],
        "gas_models": ["lng_regas_sale", "customer_indexed_sale"],
        "knowledge_points": ["outright_price", "basis_spread", "options_optionality", "capacity_storage_balancing"],
        "required_curves": ["TTF", "JKM", "TTF_JKM_SPREAD", "REGAS_WINDOW"],
        "suggested_leg_types": ["physical", "swap", "basis", "option", "capacity"],
        "lesson_sequence": ["align cargo arrival and regas slot", "protect customer sale price", "use options for downside if needed", "check delivery performance"],
    },
    {
        "id": "integrated_gas_portfolio",
        "group": "integrated",
        "business_type": {"en": "Integrated gas portfolio hedge", "zh": "天然气组合套保"},
        "title": {"en": "Multi-leg gas hedge under market stress", "zh": "市场压力下的多腿天然气套保"},
        "summary": {
            "en": "A capstone case combining physical supply, sales obligation, futures or swaps, basis, FX, capacity, options, and risk controls.",
            "zh": "综合案例：同时处理实货供应、销售义务、期货或掉期、基差、汇率、运力、期权和风控。",
        },
        "coverage": [
            "exposure_objective",
            "physical_paper_matching",
            "basis_spread",
            "fx",
            "capacity_storage_balancing",
            "options_optionality",
            "hedge_ratio_cross_hedge",
            "risk_controls",
        ],
        "gas_models": ["gsa_procurement", "efet_bilateral_sale", "lng_regas_sale", "pipeline_capacity"],
        "knowledge_points": ["physical_paper_matching", "basis_spread", "fx", "capacity_storage_balancing", "options_optionality", "risk_controls"],
        "required_curves": ["TTF", "NBP", "JKM", "EURGBP", "TTF_NBP_SPREAD"],
        "suggested_leg_types": ["physical", "swap", "basis", "fx", "capacity", "option"],
        "lesson_sequence": ["map full value chain", "separate risk buckets", "build target legs", "explain residual and controls"],
    },
]


def _locale(locale: str) -> str:
    return "zh" if (locale or "").lower().startswith("zh") else "en"


def _localized_text(value: dict[str, str], locale: str) -> str:
    lang = _locale(locale)
    return value.get(lang) or value.get("en") or ""


def _localize_template(template: dict[str, Any], locale: str) -> dict[str, Any]:
    item = deepcopy(template)
    item["business_type"] = _localized_text(template["business_type"], locale)
    item["title"] = _localized_text(template["title"], locale)
    item["summary"] = _localized_text(template["summary"], locale)
    return item


def list_business_groups(locale: str = "en") -> list[dict[str, str]]:
    return [{"id": group["id"], "label": _localized_text(group["label"], locale)} for group in _BUSINESS_GROUPS]


def list_knowledge_points(locale: str = "en") -> list[dict[str, str]]:
    return [
        {
            "id": point["id"],
            "label": _localized_text(point["label"], locale),
            "description": _localized_text(point["description"], locale),
        }
        for point in _KNOWLEDGE_POINTS
    ]


def list_templates(locale: str = "en") -> list[dict[str, Any]]:
    return [_localize_template(template, locale) for template in _TEMPLATES]


def get_template(template_id: str, locale: str = "en") -> dict[str, Any]:
    for template in _TEMPLATES:
        if template["id"] == template_id:
            return _localize_template(template, locale)
    raise KeyError(f"Unknown business template '{template_id}'.")
