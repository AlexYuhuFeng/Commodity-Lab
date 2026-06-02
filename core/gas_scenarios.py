"""Natural gas scenario catalog and deterministic sample context for V1."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


_CATEGORY_DATA: list[dict[str, Any]] = [
    {
        "id": "natural_gas",
        "status": "enabled",
        "label": {
            "en": "Natural Gas",
            "zh": "天然气",
        },
        "description": {
            "en": "V1 scenarios for natural gas price, basis, storage, and pipeline risk.",
            "zh": "V1 天然气价格、基差、储气和管道风险场景。",
        },
    },
    {
        "id": "oil_products",
        "status": "constructing",
        "label": {
            "en": "Oil Products",
            "zh": "油品",
        },
        "description": {
            "en": "Oil products workflows are visible but still under construction.",
            "zh": "油品工作流已展示，但仍在建设中。",
        },
    },
    {
        "id": "metals",
        "status": "constructing",
        "label": {
            "en": "Metals",
            "zh": "金属",
        },
        "description": {
            "en": "Metals workflows are visible but still under construction.",
            "zh": "金属工作流已展示，但仍在建设中。",
        },
    },
    {
        "id": "grains",
        "status": "constructing",
        "label": {
            "en": "Grains",
            "zh": "谷物",
        },
        "description": {
            "en": "Grains workflows are visible but still under construction.",
            "zh": "谷物工作流已展示，但仍在建设中。",
        },
    },
]

_GUIDED_STEPS: list[dict[str, Any]] = [
    {
        "id": "understand_exposure",
        "label": {
            "en": "Understand exposure",
            "zh": "识别风险敞口",
        },
        "description": {
            "en": "Identify the physical exposure, hedge horizon, and risk driver.",
            "zh": "识别现货风险敞口、套保期限和主要风险驱动因素。",
        },
    },
    {
        "id": "inspect_market",
        "label": {
            "en": "Inspect market",
            "zh": "观察市场",
        },
        "description": {
            "en": "Review sample futures, basis, and operating context before hedging.",
            "zh": "在套保前观察样本期货、基差和运营背景。",
        },
    },
    {
        "id": "place_hedge",
        "label": {
            "en": "Place hedge",
            "zh": "建立套保",
        },
        "description": {
            "en": "Select the hedge side, size, instrument, and execution timing.",
            "zh": "选择套保方向、规模、工具和执行时点。",
        },
    },
    {
        "id": "review_score",
        "label": {
            "en": "Review score",
            "zh": "复盘评分",
        },
        "description": {
            "en": "Compare the hedge decision against the scenario objective.",
            "zh": "对照场景目标复盘套保决策。",
        },
    },
    {
        "id": "exam",
        "label": {
            "en": "Exam",
            "zh": "测验",
        },
        "description": {
            "en": "Answer a short assessment question to reinforce the lesson.",
            "zh": "完成简短测验，巩固本场景要点。",
        },
    },
]

_SCENARIO_DATA: list[dict[str, Any]] = [
    {
        "id": "producer_short_hedge",
        "status": "enabled",
        "commodity_id": "natural_gas",
        "commodity": "natural_gas",
        "enabled": True,
        "difficulty": "intro",
        "exposure": {
            "direction": "long",
            "volume_mmbtu": 100000,
            "risk": {
                "en": "Forward production revenue falls if Henry Hub natural gas prices decline.",
                "zh": "如果亨利港天然气价格下跌，远期产量收入会下降。",
            },
        },
        "recommended_hedge_type": "short_hedge",
        "recommended_side": "sell",
        "default_symbol": "NG=F",
        "title": {
            "en": "Producer Short Hedge",
            "zh": "生产商卖出套保",
        },
        "summary": {
            "en": "A gas producer protects forward revenue from a Henry Hub price decline.",
            "zh": "天然气生产商通过卖出套保，保护远期收入免受亨利港价格下跌影响。",
        },
        "learning_objectives": {
            "en": [
                "Match a long physical production exposure with a short futures hedge.",
                "Size the hedge ratio against expected production volume.",
                "Evaluate how futures gains offset lower physical sales prices.",
            ],
            "zh": [
                "将现货生产多头风险与期货空头套保相匹配。",
                "根据预期产量确定套保比例。",
                "评估期货收益如何抵消现货销售价格下跌。",
            ],
        },
    },
    {
        "id": "winter_load_spike",
        "status": "enabled",
        "commodity_id": "natural_gas",
        "commodity": "natural_gas",
        "enabled": True,
        "difficulty": "intro",
        "exposure": {
            "direction": "short",
            "volume_mmbtu": 85000,
            "risk": {
                "en": "Heating demand can lift spot and futures prices before fuel is purchased.",
                "zh": "采暖需求可能在采购燃料前推高现货和期货价格。",
            },
        },
        "recommended_hedge_type": "long_hedge",
        "recommended_side": "buy",
        "default_symbol": "NG=F",
        "title": {
            "en": "Winter Load Spike",
            "zh": "冬季负荷上升",
        },
        "summary": {
            "en": "A utility hedges rising winter fuel costs as heating demand accelerates.",
            "zh": "公用事业企业在采暖需求上升时，对冲冬季燃料成本上涨风险。",
        },
        "learning_objectives": {
            "en": [
                "Connect weather-driven load risk to a long natural gas hedge.",
                "Read front-month price movement before placing the hedge.",
                "Explain how the hedge reduces budget volatility for gas purchases.",
            ],
            "zh": [
                "将天气驱动的负荷风险与天然气买入套保联系起来。",
                "在建立套保前观察近月价格变化。",
                "说明套保如何降低燃气采购预算波动。",
            ],
        },
    },
    {
        "id": "pipeline_capacity_constraint",
        "status": "enabled",
        "commodity_id": "natural_gas",
        "commodity": "natural_gas",
        "enabled": True,
        "difficulty": "intermediate",
        "exposure": {
            "direction": "short",
            "volume_mmbtu": 111000,
            "risk": {
                "en": "Tight pipeline space can raise delivered costs and widen regional basis.",
                "zh": "管道空间紧张可能抬高到岸成本并扩大区域基差。",
            },
        },
        "recommended_hedge_type": "basis_hedge",
        "recommended_side": "buy",
        "default_symbol": "NG=F",
        "title": {
            "en": "Pipeline Capacity Constraint",
            "zh": "管道运力约束",
        },
        "summary": {
            "en": "A shipper manages basis and nomination risk when pipeline capacity tightens.",
            "zh": "托运人在管道运力趋紧时管理基差和提名量风险。",
        },
        "learning_objectives": {
            "en": [
                "Interpret available capacity, nomination, and utilization metrics.",
                "Recognize how constrained transport can widen regional basis.",
                "Choose a hedge that addresses both price and delivery-location risk.",
            ],
            "zh": [
                "解读可用运力、提名量和利用率指标。",
                "识别管输约束如何扩大区域基差。",
                "选择同时覆盖价格和交割地点风险的套保方案。",
            ],
        },
    },
    {
        "id": "regional_basis_blowout",
        "status": "enabled",
        "commodity_id": "natural_gas",
        "commodity": "natural_gas",
        "enabled": True,
        "difficulty": "intermediate",
        "exposure": {
            "direction": "long",
            "volume_mmbtu": 90000,
            "risk": {
                "en": "A local cash discount can widen versus Henry Hub and reduce realized sales value.",
                "zh": "本地现货相对亨利港的贴水可能扩大，压低实现销售价值。",
            },
        },
        "recommended_hedge_type": "basis_hedge",
        "recommended_side": "sell",
        "default_symbol": "NG=F",
        "title": {
            "en": "Regional Basis Blowout",
            "zh": "区域基差扩大",
        },
        "summary": {
            "en": "A marketer hedges a local price discount that widens versus Henry Hub.",
            "zh": "贸易商对冲本地价格相对亨利港贴水扩大的风险。",
        },
        "learning_objectives": {
            "en": [
                "Separate benchmark futures risk from regional basis exposure.",
                "Identify when a basis hedge is more relevant than an outright hedge.",
                "Review how transport constraints can change local cash pricing.",
            ],
            "zh": [
                "区分基准期货风险与区域基差风险。",
                "判断何时基差套保比单边价格套保更合适。",
                "复盘运输约束如何改变本地现货定价。",
            ],
        },
    },
    {
        "id": "storage_calendar_spread",
        "status": "enabled",
        "commodity_id": "natural_gas",
        "commodity": "natural_gas",
        "enabled": True,
        "difficulty": "advanced",
        "exposure": {
            "direction": "long",
            "volume_mmbtu": 75000,
            "risk": {
                "en": "Storage margin depends on the spread between injection and withdrawal months.",
                "zh": "储气利润取决于注气月份和采气月份之间的价差。",
            },
        },
        "recommended_hedge_type": "calendar_spread",
        "recommended_side": "spread",
        "default_symbol": "NG=F",
        "title": {
            "en": "Storage Calendar Spread",
            "zh": "储气库月差套保",
        },
        "summary": {
            "en": "A storage operator hedges injection and withdrawal economics with calendar spreads.",
            "zh": "储气库运营商使用月差套保管理注气和采气经济性。",
        },
        "learning_objectives": {
            "en": [
                "Relate storage value to the spread between nearby and deferred contracts.",
                "Assess injection, withdrawal, and carrying-cost assumptions.",
                "Use a calendar spread to reduce seasonal margin uncertainty.",
            ],
            "zh": [
                "将储气价值与近月和远月合约价差联系起来。",
                "评估注气、采气和持有成本假设。",
                "使用月差套保降低季节性利润不确定性。",
            ],
        },
    },
]

_SAMPLE_PRICE_POINTS: dict[str, list[dict[str, Any]]] = {
    "producer_short_hedge": [
        {"date": "2026-01-05", "close": 3.42},
        {"date": "2026-01-06", "close": 3.38},
        {"date": "2026-01-07", "close": 3.31},
        {"date": "2026-01-08", "close": 3.29},
        {"date": "2026-01-09", "close": 3.25},
        {"date": "2026-01-12", "close": 3.18},
    ],
    "winter_load_spike": [
        {"date": "2026-01-05", "close": 3.14},
        {"date": "2026-01-06", "close": 3.21},
        {"date": "2026-01-07", "close": 3.33},
        {"date": "2026-01-08", "close": 3.47},
        {"date": "2026-01-09", "close": 3.58},
        {"date": "2026-01-12", "close": 3.66},
        {"date": "2026-01-13", "close": 3.72},
    ],
    "pipeline_capacity_constraint": [
        {"date": "2026-02-02", "close": 2.88},
        {"date": "2026-02-03", "close": 2.93},
        {"date": "2026-02-04", "close": 2.97},
        {"date": "2026-02-05", "close": 3.05},
        {"date": "2026-02-06", "close": 3.11},
        {"date": "2026-02-09", "close": 3.16},
    ],
    "regional_basis_blowout": [
        {"date": "2026-03-02", "close": 2.71},
        {"date": "2026-03-03", "close": 2.69},
        {"date": "2026-03-04", "close": 2.63},
        {"date": "2026-03-05", "close": 2.55},
        {"date": "2026-03-06", "close": 2.48},
        {"date": "2026-03-09", "close": 2.44},
    ],
    "storage_calendar_spread": [
        {"date": "2026-04-01", "close": 2.94},
        {"date": "2026-04-02", "close": 2.98},
        {"date": "2026-04-03", "close": 3.01},
        {"date": "2026-04-06", "close": 3.07},
        {"date": "2026-04-07", "close": 3.12},
        {"date": "2026-04-08", "close": 3.18},
    ],
}

_SOURCE_LABELS: dict[str, str] = {
    "sample": "Simulated",
    "simulated": "Simulated",
    "yfinance": "Yahoo Finance",
    "platts": "Platts",
}

_SOURCE_ALIASES: dict[str, str] = {
    "sample": "sample",
    "simulated": "simulated",
    "yfinance": "yfinance",
    "yahoo finance": "yfinance",
    "yahoo_finance": "yfinance",
    "yahoo-finance": "yfinance",
    "platts": "platts",
}

_SIMULATED_SOURCE = "simulated"
_SIMULATED_SOURCE_LABEL = "Simulated"

_CAPACITY_CONTEXTS: dict[str, dict[str, Any]] = {
    "pipeline_capacity_constraint": {
        "scenario_id": "pipeline_capacity_constraint",
        "receipt_point": "Permian Receipt",
        "delivery_point": "Gulf Coast Delivery",
        "pipeline_name": "Permian Gulf Express",
        "available_capacity_mmbtu": 120000,
        "nominated_mmbtu": 111000,
        "utilization_pct": 92.5,
        "congestion_status": "constrained",
        "flow_nodes": [
            {"id": "receipt", "label": "Permian Receipt", "role": "receipt"},
            {"id": "constraint", "label": "Capacity Constraint", "role": "constraint"},
            {"id": "delivery", "label": "Gulf Coast Delivery", "role": "delivery"},
        ],
        "flow_edges": [
            {"from": "receipt", "to": "constraint", "mmbtu": 111000},
            {"from": "constraint", "to": "delivery", "mmbtu": 111000},
        ],
    }
}


def list_categories(locale: str = "en") -> list[dict[str, Any]]:
    """Return commodity category cards with localized labels and V1 status."""
    active_locale = _normalize_locale(locale)
    return [_localize_category(category, active_locale) for category in _CATEGORY_DATA]


def list_scenarios(locale: str = "en") -> list[dict[str, Any]]:
    """Return enabled V1 natural gas scenarios only."""
    active_locale = _normalize_locale(locale)
    return [
        _localize_scenario(scenario, active_locale)
        for scenario in _SCENARIO_DATA
        if _is_enabled_natural_gas_scenario(scenario)
    ]


def get_scenario(scenario_id: str, locale: str = "en") -> dict[str, Any]:
    """Return one localized scenario by id."""
    active_locale = _normalize_locale(locale)
    scenario = _find_scenario(scenario_id)
    return _localize_scenario(scenario, active_locale)


def get_market_context(scenario_id: str, source: str = "sample") -> dict[str, Any]:
    """Return deterministic Henry Hub sample market context for a scenario."""
    scenario = _find_scenario(scenario_id)
    points = _SAMPLE_PRICE_POINTS.get(scenario_id)
    if points is None:
        raise KeyError(f"No market context is configured for scenario '{scenario_id}'.")

    requested_source = _normalize_source(source)
    requested_source_label = _source_label(requested_source)
    is_fallback = requested_source not in {"sample", _SIMULATED_SOURCE}
    price_series = deepcopy(points)
    context: dict[str, Any] = {
        "scenario_id": scenario_id,
        "source": requested_source,
        "source_label": requested_source_label,
        "data_source": _SIMULATED_SOURCE,
        "data_source_label": _SIMULATED_SOURCE_LABEL,
        "symbol": scenario["default_symbol"],
        "instrument": "Henry Hub Natural Gas Futures",
        "unit": "USD/MMBtu",
        "price_series": price_series,
        "price_points": deepcopy(price_series),
        "latest_price": price_series[-1]["close"],
        "metadata": {
            "provider": requested_source,
            "requested_source": requested_source,
            "requested_source_label": requested_source_label,
            "returned_source": _SIMULATED_SOURCE,
            "returned_source_label": _SIMULATED_SOURCE_LABEL,
            "is_fallback": is_fallback,
        },
    }
    if is_fallback:
        context["metadata"]["fallback_reason"] = "Only deterministic sample data is available in V1."
    return context


def get_capacity_context(scenario_id: str) -> dict[str, Any]:
    """Return sample capacity and flow context for pipeline-aware scenarios."""
    scenario = _find_scenario(scenario_id)
    context = _CAPACITY_CONTEXTS.get(scenario_id)
    if context is not None:
        return deepcopy(context)
    return _build_default_capacity_context(scenario)


def _normalize_locale(locale: str) -> str:
    return "zh" if locale.lower().startswith("zh") else "en"


def _localize_category(category: dict[str, Any], locale: str) -> dict[str, Any]:
    return {
        "id": category["id"],
        "status": category["status"],
        "label": category["label"][locale],
        "description": category["description"][locale],
    }


def _localize_scenario(scenario: dict[str, Any], locale: str) -> dict[str, Any]:
    category = _find_category(scenario["commodity_id"])
    return {
        "id": scenario["id"],
        "status": scenario["status"],
        "commodity_id": scenario["commodity_id"],
        "commodity": scenario.get("commodity", scenario["commodity_id"]),
        "enabled": scenario.get("enabled", scenario["status"] == "enabled"),
        "commodity_label": category["label"][locale],
        "difficulty": scenario["difficulty"],
        "title": scenario["title"][locale],
        "summary": scenario["summary"][locale],
        "exposure": _localize_exposure(scenario["exposure"], locale),
        "recommended_hedge_type": scenario["recommended_hedge_type"],
        "recommended_side": scenario["recommended_side"],
        "default_symbol": scenario["default_symbol"],
        "guided_steps": _localize_guided_steps(locale),
        "learning_objectives": deepcopy(scenario["learning_objectives"][locale]),
    }


def _localize_exposure(exposure: dict[str, Any], locale: str) -> dict[str, Any]:
    return {
        "direction": exposure["direction"],
        "volume_mmbtu": exposure["volume_mmbtu"],
        "risk": exposure["risk"][locale],
    }


def _localize_guided_steps(locale: str) -> list[dict[str, Any]]:
    return [
        {
            "id": step["id"],
            "label": step["label"][locale],
            "description": step["description"][locale],
        }
        for step in _GUIDED_STEPS
    ]


def _find_category(category_id: str) -> dict[str, Any]:
    for category in _CATEGORY_DATA:
        if category["id"] == category_id:
            return category
    raise KeyError(f"Unknown category '{category_id}'.")


def _find_scenario(scenario_id: str) -> dict[str, Any]:
    for scenario in _SCENARIO_DATA:
        if scenario["id"] == scenario_id:
            return scenario
    raise KeyError(f"Unknown scenario '{scenario_id}'.")


def _is_enabled_natural_gas_scenario(scenario: dict[str, Any]) -> bool:
    enabled = scenario.get("enabled", scenario.get("status") == "enabled")
    commodity = scenario.get("commodity", scenario.get("commodity_id"))
    return enabled is True and scenario.get("status") == "enabled" and commodity == "natural_gas"


def _normalize_source(source: str) -> str:
    normalized = " ".join(source.strip().lower().split()) if source else "sample"
    return _SOURCE_ALIASES.get(normalized, normalized)


def _source_label(source: str) -> str:
    return _SOURCE_LABELS.get(source, source)


def _build_default_capacity_context(scenario: dict[str, Any]) -> dict[str, Any]:
    nominated_mmbtu = int(scenario["exposure"]["volume_mmbtu"])
    available_capacity_mmbtu = max(1, int(round(nominated_mmbtu * 1.25)))
    utilization_pct = round((nominated_mmbtu / available_capacity_mmbtu) * 100, 1)
    if utilization_pct >= 95:
        congestion_status = "constrained"
    elif utilization_pct >= 85:
        congestion_status = "watch"
    else:
        congestion_status = "normal"

    receipt_point = "Henry Hub Receipt"
    delivery_point = "Scenario Delivery"
    return {
        "scenario_id": scenario["id"],
        "receipt_point": receipt_point,
        "delivery_point": delivery_point,
        "pipeline_name": "Sample Natural Gas Flow",
        "available_capacity_mmbtu": available_capacity_mmbtu,
        "nominated_mmbtu": nominated_mmbtu,
        "utilization_pct": utilization_pct,
        "congestion_status": congestion_status,
        "flow_nodes": [
            {"id": "receipt", "label": receipt_point, "role": "receipt"},
            {"id": "nomination", "label": "Scheduled Nomination", "role": "nomination"},
            {"id": "delivery", "label": delivery_point, "role": "delivery"},
        ],
        "flow_edges": [
            {"from": "receipt", "to": "nomination", "mmbtu": nominated_mmbtu},
            {"from": "nomination", "to": "delivery", "mmbtu": nominated_mmbtu},
        ],
    }
