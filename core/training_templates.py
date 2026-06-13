"""Business and knowledge-point templates for AI-generated gas training cases."""
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
        "id": "physical_paper_matching",
        "label": {"en": "Physical-paper matching", "zh": "实货与纸货匹配"},
        "description": {
            "en": "Match GSA, EFET, LNG, capacity, futures, swaps, basis, FX, and options as one strategy.",
            "zh": "把 GSA、EFET、LNG、运力、期货、掉期、基差、汇率和期权作为一个组合策略匹配。",
        },
    },
    {
        "id": "outright_price",
        "label": {"en": "Outright price hedge", "zh": "单边价格套保"},
        "description": {
            "en": "Use futures, forwards, or swaps to reduce exposure to absolute gas price moves.",
            "zh": "使用期货、远期或掉期降低天然气绝对价格波动风险。",
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
    {"id": "procurement", "label": {"en": "Procurement", "zh": "采购端"}},
    {"id": "sales", "label": {"en": "Sales", "zh": "销售端"}},
    {"id": "integrated", "label": {"en": "Integrated strategy", "zh": "组合策略"}},
]


_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "foundation_hedging_basics",
        "group": "foundation",
        "business_type": {"en": "Natural gas hedging foundations", "zh": "天然气套保基础"},
        "title": {"en": "What exposure are we hedging?", "zh": "我们到底在套保什么？"},
        "summary": {
            "en": "A beginner case that teaches exposure direction, hedge objective, physical-paper matching, quantity, tenor, and basic execution checks.",
            "zh": "入门案例：先讲清楚敞口方向、套保目标、实货/纸货匹配、数量、期限和基础执行检查。",
        },
        "coverage": ["exposure_objective", "physical_paper_matching", "outright_price"],
        "gas_models": ["customer_indexed_sale", "simple_procurement"],
        "knowledge_points": ["exposure_objective", "outright_price", "physical_paper_matching"],
        "required_curves": ["TTF", "TRAINING_HEDGE_INDEX"],
        "suggested_leg_types": ["physical", "swap"],
        "lesson_sequence": ["identify exposure", "choose hedge side", "match quantity and tenor", "explain residual risk"],
    },
    {
        "id": "procurement_beach_to_germany",
        "group": "procurement",
        "business_type": {"en": "Upstream Beach Delivery GSA", "zh": "上游 Beach Delivery 资源（GSA）"},
        "title": {"en": "UK Beach Delivery sold into Germany", "zh": "英国上游 Beach Delivery 卖德国"},
        "summary": {
            "en": "A procurement case for UK beach gas sold into Germany, covering NBP/TTF basis, EUR/GBP FX, transport capacity, and physical-paper matching.",
            "zh": "英国 beach delivery 资源卖往德国的采购/销售组合案例，覆盖 NBP/TTF 基差、EUR/GBP 汇率、运输能力和实纸货匹配。",
        },
        "coverage": ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
        "gas_models": ["gsa_procurement", "cross_border_sale", "pipeline_capacity"],
        "knowledge_points": ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching"],
        "required_curves": ["TTF", "NBP", "EURGBP", "TTF_NBP_SPREAD"],
        "suggested_leg_types": ["physical", "basis", "fx", "capacity"],
        "lesson_sequence": ["map beach receipt and German sale", "separate hub basis from FX", "add capacity check", "score residual risk"],
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
