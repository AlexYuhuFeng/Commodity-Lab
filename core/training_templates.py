"""Business and knowledge-point templates for AI-generated gas training cases."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


_KNOWLEDGE_POINTS: list[dict[str, Any]] = [
    {
        "id": "outright_price",
        "label": {"en": "Outright price hedge", "zh": "单边价格套保"},
        "description": {
            "en": "Use futures or swaps to reduce exposure to absolute gas price moves.",
            "zh": "使用期货或掉期降低天然气绝对价格波动风险。",
        },
    },
    {
        "id": "basis_spread",
        "label": {"en": "Basis and hub spread", "zh": "基差与枢纽价差"},
        "description": {
            "en": "Separate commodity price risk from location, hub, unit, and FX basis.",
            "zh": "区分商品价格风险与地点、枢纽、单位和汇率基差风险。",
        },
    },
    {
        "id": "fx",
        "label": {"en": "FX hedge", "zh": "汇率套保"},
        "description": {
            "en": "Hedge GBP/EUR/USD currency mismatch created by NBP, TTF, LNG, or EFET contracts.",
            "zh": "管理 NBP、TTF、LNG 或 EFET 合同带来的英镑、欧元、美元错配。",
        },
    },
    {
        "id": "physical_paper_matching",
        "label": {"en": "Physical-paper matching", "zh": "实货与纸货匹配"},
        "description": {
            "en": "Match GSA, LNG cargo, EFET, capacity, futures, swaps, and basis legs as one strategy.",
            "zh": "将 GSA、LNG 船货、EFET、运力、期货、掉期和基差腿作为组合策略匹配。",
        },
    },
    {
        "id": "volatility_event",
        "label": {"en": "Volatility event response", "zh": "剧烈波动应对"},
        "description": {
            "en": "React to sharp market rises or falls with hedge ratio, instrument, liquidity, and limit checks.",
            "zh": "在市场暴涨或暴跌时检查套保比例、工具、流动性和限额。",
        },
    },
]


_BUSINESS_GROUPS: list[dict[str, Any]] = [
    {"id": "procurement", "label": {"en": "Procurement", "zh": "采购端"}},
    {"id": "sales", "label": {"en": "Sales", "zh": "销售端"}},
]


_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "procurement_beach_to_germany",
        "group": "procurement",
        "business_type": {"en": "Upstream beach delivery GSA", "zh": "上游 Beach Delivery 资源（GSA）"},
        "title": {"en": "UK beach delivery sold into Germany", "zh": "英国上游 Beach Delivery 卖德国"},
        "summary": {
            "en": "Generate a case for buying UK beach gas and selling into Germany, covering NBP/TTF, FX, transport, and paper hedge legs.",
            "zh": "生成英国 beach delivery 采购、德国销售的案例，覆盖 NBP/TTF、汇率、运输和纸货套保腿。",
        },
        "knowledge_points": ["basis_spread", "fx", "physical_paper_matching"],
        "required_curves": ["TTF", "NBP", "EURGBP", "TTF_NBP_SPREAD"],
        "suggested_leg_types": ["physical", "basis", "fx", "capacity"],
    },
    {
        "id": "procurement_eex_ocm_window",
        "group": "procurement",
        "business_type": {"en": "EEX / OCM execution window", "zh": "EEX / OCM 窗口"},
        "title": {"en": "Window execution for short-term procurement", "zh": "短期采购窗口执行"},
        "summary": {
            "en": "Generate a case where procurement must decide how to use exchange/OCM windows during intraday volatility.",
            "zh": "生成采购端在日内波动中使用交易所/OCM 窗口的决策案例。",
        },
        "knowledge_points": ["outright_price", "volatility_event", "physical_paper_matching"],
        "required_curves": ["TTF", "OCM", "INTRADAY_SPREAD"],
        "suggested_leg_types": ["physical", "future", "swap"],
    },
    {
        "id": "procurement_lng_cargo",
        "group": "procurement",
        "business_type": {"en": "LNG cargo", "zh": "LNG 船货"},
        "title": {"en": "LNG cargo indexed to global gas", "zh": "LNG 船货采购"},
        "summary": {
            "en": "Generate a case for LNG cargo procurement with TTF/JKM optionality, FX, freight timing, and regas exposure.",
            "zh": "生成 LNG 船货采购案例，覆盖 TTF/JKM 可选性、汇率、运费时点和气化敞口。",
        },
        "knowledge_points": ["outright_price", "basis_spread", "fx"],
        "required_curves": ["TTF", "JKM", "EURUSD", "TTF_JKM_SPREAD"],
        "suggested_leg_types": ["physical", "swap", "fx"],
    },
    {
        "id": "sales_efet_bilateral",
        "group": "sales",
        "business_type": {"en": "Bilateral EFET", "zh": "EFET 双边"},
        "title": {"en": "EFET bilateral sale with hub mismatch", "zh": "EFET 双边销售与枢纽错配"},
        "summary": {
            "en": "Generate a case for bilateral gas sales where NBP or beach delivery differs from the sales hub.",
            "zh": "生成双边销售案例，处理 NBP 或 Beach Delivery 与销售枢纽不一致的风险。",
        },
        "knowledge_points": ["basis_spread", "physical_paper_matching"],
        "required_curves": ["TTF", "NBP", "TTF_NBP_SPREAD"],
        "suggested_leg_types": ["physical", "basis", "swap"],
    },
    {
        "id": "sales_lng_regas",
        "group": "sales",
        "business_type": {"en": "LNG regas sale", "zh": "LNG 船货气化销售"},
        "title": {"en": "Regasified LNG sale during market selloff", "zh": "市场下跌中的 LNG 气化销售"},
        "summary": {
            "en": "Generate a case where LNG is regasified and sold while the market is falling, requiring price and basis protection.",
            "zh": "生成市场下跌时 LNG 气化销售案例，需要管理价格和基差保护。",
        },
        "knowledge_points": ["outright_price", "volatility_event", "physical_paper_matching"],
        "required_curves": ["TTF", "JKM", "TTF_JKM_SPREAD"],
        "suggested_leg_types": ["physical", "swap", "basis"],
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

