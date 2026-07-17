"""Market-state and event-replay primitives for AI-guided commodity training.

The numeric engine is deterministic by design. The language model chooses and
explains a regime; this module owns internally consistent curves, provenance,
and the information boundary for historical replays.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
import math
import os
import random
from typing import Any, Iterable


_SUPPORTED_COMMODITIES = {"natural_gas", "crude_oil"}
_SUPPORTED_REGIMES = {"contango", "backwardation", "flat", "volatile"}


def _localized(locale: str, zh: str, en: str) -> str:
    return zh if (locale or "").lower().startswith("zh") else en


def _parse_date(value: str | date | None) -> date:
    if isinstance(value, date):
        return value
    if value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return date.today()


def _month_start(value: date, month_offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + month_offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _prices(values: Iterable[Any]) -> list[float]:
    result: list[float] = []
    for value in values:
        if isinstance(value, dict):
            value = value.get("price", value.get("close"))
        try:
            result.append(float(value))
        except (TypeError, ValueError):
            continue
    return result


def classify_forward_curve(values: Iterable[Any], flat_tolerance: float = 0.005) -> dict[str, Any]:
    """Classify a forward curve from front-to-back prices."""
    prices = _prices(values)
    if len(prices) < 2:
        raise ValueError("At least two forward prices are required.")
    front = prices[0]
    back = prices[-1]
    if front == 0:
        raise ValueError("Front price cannot be zero.")
    percentage_slope = (back - front) / abs(front)
    if percentage_slope > flat_tolerance:
        structure = "contango"
    elif percentage_slope < -flat_tolerance:
        structure = "backwardation"
    else:
        structure = "flat"
    adjacent_spreads = [prices[index + 1] - prices[index] for index in range(len(prices) - 1)]
    return {
        "structure": structure,
        "front_price": round(front, 4),
        "back_price": round(back, 4),
        "front_back_spread": round(back - front, 4),
        "percentage_slope": round(percentage_slope, 6),
        "average_monthly_spread": round(sum(adjacent_spreads) / len(adjacent_spreads), 4),
    }


def _commodity_profile(commodity: str, locale: str) -> dict[str, Any]:
    if commodity == "crude_oil":
        return {
            "benchmark": "Brent",
            "unit": "USD/bbl",
            "base_price": 82.0,
            "color": "#0ea5e9",
            "label": _localized(locale, "布伦特原油", "Brent crude"),
        }
    return {
        "benchmark": "TTF",
        "unit": "EUR/MWh",
        "base_price": 34.0,
        "color": "#14b8a6",
        "label": _localized(locale, "TTF 天然气", "TTF natural gas"),
    }


def _curve_price(
    *,
    base_price: float,
    commodity: str,
    regime: str,
    month_index: int,
    rng: random.Random,
) -> float:
    slope_by_regime = {
        "contango": 0.013,
        "backwardation": -0.013,
        "flat": 0.0002,
        "volatile": -0.004,
    }
    slope = slope_by_regime[regime]
    seasonality = 0.0
    if commodity == "natural_gas":
        seasonality = 0.0035 * math.sin((month_index + 1) * math.pi / 3)
    elif commodity == "crude_oil":
        seasonality = 0.0015 * math.cos((month_index + 1) * math.pi / 4)
    volatility_shape = 0.0
    if regime == "volatile":
        volatility_shape = 0.018 * math.sin((month_index + 1) * 1.7)
    micro_noise = rng.uniform(-0.0007, 0.0007)
    multiplier = 1 + slope * month_index + seasonality + volatility_shape + micro_noise
    return round(max(base_price * multiplier, 0.01), 4)


def _history_series(
    *,
    base_price: float,
    as_of: date,
    regime: str,
    seed: int,
    days: int = 45,
) -> list[dict[str, Any]]:
    rng = random.Random(seed + 91_337)
    daily_sigma = 0.012 if regime == "volatile" else 0.006
    drift = {
        "contango": -0.0005,
        "backwardation": 0.0006,
        "flat": 0.0,
        "volatile": 0.0002,
    }[regime]
    close = base_price * 0.94
    points: list[dict[str, Any]] = []
    for index in range(days):
        day = as_of - timedelta(days=days - index - 1)
        open_price = close
        move = drift + rng.gauss(0, daily_sigma)
        if regime == "volatile" and index in {days // 3, days // 3 + 1}:
            move += 0.07 if index == days // 3 else -0.045
        close = max(open_price * (1 + move), 0.01)
        intraday = abs(rng.gauss(daily_sigma * 0.75, daily_sigma * 0.25))
        high = max(open_price, close) * (1 + intraday)
        low = min(open_price, close) * (1 - intraday)
        points.append(
            {
                "date": day.isoformat(),
                "open": round(open_price, 4),
                "high": round(high, 4),
                "low": round(max(low, 0.01), 4),
                "close": round(close, 4),
            }
        )
    scale = base_price / points[-1]["close"]
    for point in points:
        for field in ("open", "high", "low", "close"):
            point[field] = round(point[field] * scale, 4)
    return points


def build_simulated_market_context(
    *,
    commodity: str = "natural_gas",
    regime: str = "contango",
    seed: int = 42,
    as_of: str | date | None = None,
    locale: str = "en",
    base_price: float | None = None,
) -> dict[str, Any]:
    """Build a deterministic market state suitable for DeepSeek case generation."""
    if commodity not in _SUPPORTED_COMMODITIES:
        raise ValueError(f"Unsupported commodity: {commodity}")
    if regime not in _SUPPORTED_REGIMES:
        raise ValueError(f"Unsupported regime: {regime}")
    as_of_date = _parse_date(as_of)
    profile = _commodity_profile(commodity, locale)
    resolved_base_price = float(base_price if base_price is not None else profile["base_price"])
    rng = random.Random(seed)
    curve: list[dict[str, Any]] = []
    for month_index in range(12):
        delivery = _month_start(as_of_date, month_index + 1)
        price = _curve_price(
            base_price=resolved_base_price,
            commodity=commodity,
            regime=regime,
            month_index=month_index,
            rng=rng,
        )
        spread = max(price * 0.0015, 0.01)
        curve.append(
            {
                "tenor": f"M+{month_index + 1}",
                "delivery_month": delivery.strftime("%Y-%m"),
                "price": price,
                "bid": round(price - spread, 4),
                "ask": round(price + spread, 4),
            }
        )
    metrics = classify_forward_curve(curve)
    history = _history_series(
        base_price=curve[0]["price"],
        as_of=as_of_date,
        regime=regime,
        seed=seed,
    )
    structure_label = {
        "contango": _localized(locale, "升水结构", "contango"),
        "backwardation": _localized(locale, "现货升水结构", "backwardation"),
        "flat": _localized(locale, "平坦结构", "flat curve"),
        "volatile": _localized(locale, "高波动结构", "volatile curve"),
    }[regime]
    return {
        "commodity": commodity,
        "benchmark": profile["benchmark"],
        "label": profile["label"],
        "unit": profile["unit"],
        "as_of": as_of_date.isoformat(),
        "forward_curve": curve,
        "history": history,
        "curve_metrics": metrics,
        "market_narrative": _localized(
            locale,
            f"本地数值引擎生成的{structure_label}训练市场；DeepSeek 可据此编排事件、敞口和决策任务。",
            f"A {structure_label} training market generated by the local numeric engine; DeepSeek can use it to compose events, exposures, and decisions.",
        ),
        "provenance": {
            "mode": "ai_simulated",
            "label": _localized(locale, "AI 模拟市场", "AI-simulated market"),
            "source": "Commodity Lab deterministic market engine",
            "source_tier": "synthetic",
            "is_live": False,
            "as_of": as_of_date.isoformat(),
            "seed": seed,
            "requested_regime": regime,
        },
    }


_REPLAY_EVENTS: list[dict[str, Any]] = [
    {
        "id": "hormuz_2026_disruption",
        "commodity": "crude_oil",
        "title": {
            "zh": "2026 霍尔木兹海峡供应冲击复盘",
            "en": "2026 Strait of Hormuz supply-shock replay",
        },
        "summary": {
            "zh": "从炼厂采购和原油贸易视角，在信息逐步揭示的过程中管理实货、Brent 纸货、月差、运费和可选性。",
            "en": "Manage physical cargo, Brent paper, calendar spread, freight, and optionality as information is revealed to a refinery procurement desk.",
        },
        "skills": ["flat_price", "calendar_spread", "physical_paper_matching", "freight", "options", "risk_controls"],
        "source_notes": [
            {
                "publisher": "U.S. Energy Information Administration",
                "title": "Petroleum markets responded to disruptions in the Middle East in the second quarter",
                "published": "2026-07-15",
                "url": "https://www.eia.gov/todayinenergy/detail.php?id=67865",
                "use": "Event chronology and reported Brent range; training curves are simulated rather than copied from the licensed source cited by EIA.",
            }
        ],
        "checkpoints": [
            {
                "date": "2026-04-01",
                "label": {"zh": "供应通道受阻", "en": "Supply route disruption"},
                "facts": {
                    "zh": ["霍尔木兹海峡通行受限", "中东部分原油供应面临中断", "价格和日内波动显著上升"],
                    "en": ["Traffic through the Strait of Hormuz is constrained", "Some Middle East crude supply is disrupted", "Prices and intraday volatility rise sharply"],
                },
                "decision_required": {
                    "zh": "你负责未来两个月的炼厂原油采购。先决定实货覆盖、Brent 套保比例和是否购买上行保护。",
                    "en": "You manage two months of refinery crude procurement. Decide physical coverage, Brent hedge ratio, and whether to buy upside protection.",
                },
                "regime": "backwardation",
                "base_price": 103.0,
                "seed": 260401,
            },
            {
                "date": "2026-04-29",
                "label": {"zh": "不确定性达到高点", "en": "Uncertainty peaks"},
                "facts": {
                    "zh": ["Brent 近月价格触及季度高位", "现货供应稀缺性推高近端月差", "保证金和流动性压力同步上升"],
                    "en": ["Front-month Brent reaches the quarterly high", "Physical scarcity strengthens the prompt spread", "Margin and liquidity pressure rise with volatility"],
                },
                "decision_required": {
                    "zh": "重新评估原套保是否过度、是否应使用价差或期权替代追加期货。",
                    "en": "Reassess whether the original hedge is excessive and whether spreads or options should replace additional futures.",
                },
                "regime": "backwardation",
                "base_price": 118.0,
                "seed": 260429,
            },
            {
                "date": "2026-06-17",
                "label": {"zh": "恢复通航预期", "en": "Reopening expectations"},
                "facts": {
                    "zh": ["停火和恢复通航预期增强", "油轮活动开始恢复", "Brent 价格从高位快速回落"],
                    "en": ["Ceasefire and reopening expectations strengthen", "Tanker movements begin to recover", "Brent falls quickly from its peak"],
                },
                "decision_required": {
                    "zh": "决定是否平掉上行保护、锁定炼厂利润，并检查远期采购是否暴露于价格回落。",
                    "en": "Decide whether to unwind upside protection, lock refinery margin, and check whether deferred procurement is exposed to falling prices.",
                },
                "regime": "contango",
                "base_price": 84.0,
                "seed": 260617,
            },
        ],
    }
]


def _localize_checkpoint(checkpoint: dict[str, Any], locale: str, index: int) -> dict[str, Any]:
    language = "zh" if (locale or "").lower().startswith("zh") else "en"
    return {
        "index": index,
        "date": checkpoint["date"],
        "label": checkpoint["label"][language],
        "facts": list(checkpoint["facts"][language]),
        "decision_required": checkpoint["decision_required"][language],
    }


def list_replay_events(locale: str = "en") -> list[dict[str, Any]]:
    language = "zh" if (locale or "").lower().startswith("zh") else "en"
    return [
        {
            "id": event["id"],
            "commodity": event["commodity"],
            "title": event["title"][language],
            "summary": event["summary"][language],
            "skills": list(event["skills"]),
            "checkpoint_count": len(event["checkpoints"]),
            "source_publishers": [item["publisher"] for item in event["source_notes"]],
        }
        for event in _REPLAY_EVENTS
    ]


def build_replay_session(event_id: str, checkpoint: int = 0, locale: str = "en") -> dict[str, Any]:
    event = next((item for item in _REPLAY_EVENTS if item["id"] == event_id), None)
    if event is None:
        raise KeyError(f"Unknown replay event '{event_id}'.")
    if checkpoint < 0 or checkpoint >= len(event["checkpoints"]):
        raise ValueError("Replay checkpoint is out of range.")
    language = "zh" if (locale or "").lower().startswith("zh") else "en"
    current = event["checkpoints"][checkpoint]
    market = build_simulated_market_context(
        commodity=event["commodity"],
        regime=current["regime"],
        seed=current["seed"],
        as_of=current["date"],
        locale=locale,
        base_price=current["base_price"],
    )
    market["provenance"].update(
        {
            "mode": "historical_replay",
            "label": _localized(locale, "历史复盘（校准模拟）", "Historical replay (calibrated simulation)"),
            "source": "Commodity Lab replay engine",
            "source_tier": "historically_calibrated_simulation",
            "event_id": event_id,
            "checkpoint": checkpoint,
        }
    )
    return {
        "event": {
            "id": event["id"],
            "commodity": event["commodity"],
            "title": event["title"][language],
            "summary": event["summary"][language],
            "skills": list(event["skills"]),
        },
        "current_checkpoint": _localize_checkpoint(current, locale, checkpoint),
        "visible_timeline": [
            _localize_checkpoint(item, locale, index)
            for index, item in enumerate(event["checkpoints"][: checkpoint + 1])
        ],
        "next_checkpoint": checkpoint + 1 if checkpoint + 1 < len(event["checkpoints"]) else None,
        "market": market,
        "source_notes": deepcopy(event["source_notes"]),
        "information_policy": _localized(
            locale,
            "只显示该决策时点已经发生的信息；后续市场结果在提交决策后才揭示。",
            "Only information available at this decision point is shown; later outcomes are revealed after submission.",
        ),
    }


def market_capability_catalog(locale: str = "en") -> dict[str, Any]:
    platts_credentials_present = bool(
        os.getenv("COMMODITY_LAB_PLATTS_CLIENT_ID", "").strip()
        and os.getenv("COMMODITY_LAB_PLATTS_CLIENT_SECRET", "").strip()
    )
    return {
        "modes": [
            {
                "id": "live",
                "label": _localized(locale, "实盘市场", "Live market"),
                "description": _localized(locale, "使用机构订阅和映射后的真实评估价、期货曲线与市场元数据。", "Use entitled assessments, futures curves, and market metadata through an institutional subscription."),
            },
            {
                "id": "historical_replay",
                "label": _localized(locale, "历史事件复盘", "Historical replay"),
                "description": _localized(locale, "按当时可知信息逐步揭示市场变化和决策结果。", "Reveal market changes and decision outcomes using only information available at each point in time."),
            },
            {
                "id": "ai_simulated",
                "label": _localized(locale, "AI 模拟市场", "AI-simulated market"),
                "description": _localized(locale, "由本地数值引擎生成一致曲线，DeepSeek负责业务情景与教学编排。", "Use a deterministic numeric engine for coherent curves while DeepSeek composes the business and lesson."),
            },
        ],
        "providers": [
            {
                "id": "platts",
                "label": "S&P Global Commodity Insights (Platts)",
                "status": "credentials_present" if platts_credentials_present else "not_configured",
                "integration_state": "adapter_contract_ready",
                "delivery_options": ["REST API", "streaming", "sFTP"],
                "requires_subscription": True,
            }
        ],
        "fallback_mode": "ai_simulated",
        "replays": list_replay_events(locale=locale),
    }
