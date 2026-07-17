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
import re
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
        "exposure": {
            "direction": "long",
            "volume": 100000,
            "unit": "bbl",
            "risk": {
                "zh": "未来炼厂原油采购成本、Brent 基准、月差与运费上涨风险",
                "en": "Future refinery crude procurement cost, Brent benchmark, calendar-spread, and freight upside risk",
            },
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
                "target_actions": [
                    {"leg_type": "physical", "market": "Middle East crude cargo", "side": "buy", "quantity": 100000, "tenor": "M+2"},
                    {"leg_type": "future", "market": "ICE Brent", "side": "buy", "quantity": 70000, "tenor": "M+2"},
                    {"leg_type": "option", "market": "Brent call", "side": "buy", "quantity": 30000, "tenor": "M+2"},
                    {"leg_type": "capacity", "market": "VLCC freight", "side": "buy", "quantity": 1, "tenor": "M+2"},
                ],
                "outcome": {
                    "zh": "随后近月价格继续上冲。长 Brent 与看涨期权能缓冲采购成本，但运费、保证金和流动性同样决定策略能否执行。",
                    "en": "Prompt prices continued higher. Long Brent and calls cushioned procurement cost, while freight, margin, and liquidity determined whether the hedge remained executable.",
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
                "target_actions": [
                    {"leg_type": "physical", "market": "Refinery crude cargo", "side": "buy", "quantity": 100000, "tenor": "M+1"},
                    {"leg_type": "future", "market": "ICE Brent", "side": "buy", "quantity": 50000, "tenor": "M+1"},
                    {"leg_type": "option", "market": "Brent call spread", "side": "buy", "quantity": 50000, "tenor": "M+1"},
                    {"leg_type": "basis", "market": "Brent M1/M3 calendar spread", "side": "buy", "quantity": 50000, "tenor": "M+1/M+3"},
                ],
                "outcome": {
                    "zh": "价格在高位剧烈波动，继续等比例追加期货会放大保证金和过度套保风险；价差与期权更适合管理尾部风险。",
                    "en": "Prices became highly volatile near the peak. Adding futures one-for-one increased margin and over-hedge risk; spreads and options offered more controlled tail protection.",
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
                "target_actions": [
                    {"leg_type": "physical", "market": "Refinery crude cargo", "side": "buy", "quantity": 100000, "tenor": "M+2"},
                    {"leg_type": "option", "market": "Brent call", "side": "sell", "quantity": 30000, "tenor": "M+2"},
                    {"leg_type": "future", "market": "ICE Brent inventory hedge", "side": "sell", "quantity": 50000, "tenor": "M+2"},
                    {"leg_type": "basis", "market": "Brent M1/M3 calendar spread", "side": "sell", "quantity": 50000, "tenor": "M+1/M+3"},
                ],
                "outcome": {
                    "zh": "供应恢复预期推动价格和近端月差回落。及时平掉上行保护并为已锁定库存建立下行保护，可避免把危机阶段的头寸带入恢复阶段。",
                    "en": "Reopening expectations weakened prices and prompt spreads. Unwinding upside protection and adding downside cover for committed inventory avoided carrying crisis positioning into normalization.",
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


def _replay_rubric(locale: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "decision_structure",
            "label": _localized(locale, "组合动作", "Decision structure"),
            "points": 55,
            "rule": _localized(locale, "实货、纸货、方向、数量与期限应形成一致的风险覆盖。", "Physical and paper legs, sides, quantities, and tenors should form a coherent hedge."),
        },
        {
            "id": "risk_reasoning",
            "label": _localized(locale, "风险推理", "Risk reasoning"),
            "points": 25,
            "rule": _localized(locale, "解释价格、月差/基差、期权和运费风险。", "Explain price, calendar/basis, option, and freight risk."),
        },
        {
            "id": "controls",
            "label": _localized(locale, "执行与风控", "Execution and controls"),
            "points": 20,
            "rule": _localized(locale, "检查保证金、流动性、信用、限额和执行窗口。", "Check margin, liquidity, credit, limits, and execution windows."),
        },
    ]


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
            "checkpoint_count": len(event["checkpoints"]),
            "exposure": {
                **{key: value for key, value in event["exposure"].items() if key != "risk"},
                "risk": event["exposure"]["risk"][language],
            },
        },
        "current_checkpoint": _localize_checkpoint(current, locale, checkpoint),
        "visible_timeline": [
            _localize_checkpoint(item, locale, index)
            for index, item in enumerate(event["checkpoints"][: checkpoint + 1])
        ],
        "next_checkpoint": checkpoint + 1 if checkpoint + 1 < len(event["checkpoints"]) else None,
        "decision_rubric": _replay_rubric(locale),
        "market": market,
        "source_notes": deepcopy(event["source_notes"]),
        "information_policy": _localized(
            locale,
            "只显示该决策时点已经发生的信息；后续市场结果在提交决策后才揭示。",
            "Only information available at this decision point is shown; later outcomes are revealed after submission.",
        ),
    }


def _leg_tokens(value: Any) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if len(token) > 1
    }


def _absolute_number(value: Any) -> float:
    try:
        return abs(float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _target_leg_score(target: dict[str, Any], candidate: dict[str, Any]) -> float:
    if str(target.get("leg_type", "")).lower() != str(candidate.get("leg_type", "")).lower():
        return 0.0
    score = 0.5
    if str(target.get("side", "")).lower() == str(candidate.get("side", "")).lower():
        score += 0.15
    target_market = _leg_tokens(target.get("market"))
    candidate_market = _leg_tokens(candidate.get("market"))
    if target_market:
        score += 0.15 * (len(target_market & candidate_market) / len(target_market))
    if str(target.get("tenor", "")).lower() == str(candidate.get("tenor", "")).lower():
        score += 0.1
    target_quantity = _absolute_number(target.get("quantity"))
    candidate_quantity = _absolute_number(candidate.get("quantity"))
    if target_quantity and candidate_quantity:
        score += 0.1 * min(target_quantity, candidate_quantity) / max(target_quantity, candidate_quantity)
    return min(1.0, score)


def evaluate_replay_decision(
    event_id: str,
    checkpoint: int,
    strategy_legs: list[dict[str, Any]],
    rationale: str,
    locale: str = "en",
) -> dict[str, Any]:
    """Score a point-in-time replay decision without requiring an LLM call."""
    event = next((item for item in _REPLAY_EVENTS if item["id"] == event_id), None)
    if event is None:
        raise KeyError(f"Unknown replay event '{event_id}'.")
    if checkpoint < 0 or checkpoint >= len(event["checkpoints"]):
        raise ValueError("Replay checkpoint is out of range.")

    current = event["checkpoints"][checkpoint]
    targets = current["target_actions"]
    legs = [leg for leg in strategy_legs if str(leg.get("leg_type", "")).strip()]
    target_matches = [
        max((_target_leg_score(target, leg) for leg in legs), default=0.0)
        for target in targets
    ]
    target_coverage = sum(target_matches) / len(target_matches) if target_matches else 0.0

    reasoning_text = " ".join(
        [str(rationale or ""), *[f"{leg.get('market', '')} {leg.get('leg_type', '')}" for leg in legs]]
    ).lower()
    risk_groups = [
        ("price", "flat price", "价格", "上涨", "下跌", "波动"),
        ("basis", "spread", "calendar", "基差", "价差", "月差"),
        ("option", "call", "put", "期权", "可选性"),
        ("freight", "capacity", "shipping", "运费", "运力", "船期"),
    ]
    control_terms = ("margin", "liquidity", "credit", "limit", "execution", "保证金", "流动性", "信用", "限额", "执行")
    risk_covered = sum(any(term in reasoning_text for term in group) for group in risk_groups)
    controls_covered = sum(term in reasoning_text for term in control_terms)

    decision_score = round(target_coverage * 55)
    risk_score = round((risk_covered / len(risk_groups)) * 25)
    controls_score = 20 if controls_covered >= 3 else 12 if controls_covered == 2 else 6 if controls_covered == 1 else 0
    baseline_score = min(100, decision_score + risk_score + controls_score)

    has_physical = any(leg.get("leg_type") == "physical" for leg in legs)
    has_paper = any(leg.get("leg_type") in {"future", "swap", "basis", "option"} for leg in legs)
    mistake_tags = [
        *([] if has_physical else ["missing_physical_leg"]),
        *([] if has_paper else ["missing_paper_hedge"]),
        *([] if target_coverage >= 0.7 else ["incomplete_decision_structure"]),
        *([] if risk_covered >= 3 else ["thin_risk_reasoning"]),
        *([] if controls_covered >= 2 else ["missing_execution_controls"]),
    ]
    if baseline_score >= 80:
        feedback = _localized(locale, "组合结构完整，可以推进到下一市场节点。", "The hedge is coherent enough to advance to the next market checkpoint.")
    elif baseline_score >= 60:
        feedback = _localized(locale, "方向基本正确，但仍需补足数量、期限或执行风控。", "The direction is broadly sound, but sizing, tenor, or execution controls still need work.")
    else:
        feedback = _localized(locale, "先补齐实货与纸货的对应关系，再检查风险解释和执行条件。", "First connect the physical and paper legs, then strengthen the risk rationale and execution controls.")

    return {
        "event_id": event_id,
        "checkpoint": _localize_checkpoint(current, locale, checkpoint),
        "evaluation": {
            "valid": True,
            "baseline_score": baseline_score,
            "rubric": _replay_rubric(locale),
            "mistake_tags": mistake_tags,
            "dimensions": [
                {"id": "decision_structure", "score": decision_score, "points": 55},
                {"id": "risk_reasoning", "score": risk_score, "points": 25},
                {"id": "controls", "score": controls_score, "points": 20},
            ],
            "metrics": {
                "strategy_leg_count": len(legs),
                "target_coverage": round(target_coverage, 4),
                "risk_groups_covered": risk_covered,
                "controls_covered": controls_covered,
            },
        },
        "feedback": feedback,
        "outcome": current["outcome"]["zh" if (locale or "").lower().startswith("zh") else "en"],
        "model_strategy": deepcopy(targets),
        "next_checkpoint": checkpoint + 1 if checkpoint + 1 < len(event["checkpoints"]) else None,
        "complete": checkpoint + 1 >= len(event["checkpoints"]),
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
