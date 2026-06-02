from __future__ import annotations

from typing import Any

SCENARIO_CATEGORIES = {
    "Price Risk Hedge": [
        {
            "id": "price_risk_1",
            "title": "Producer price hedge",
            "description": (
                "You are a crude oil producer facing the risk of falling prices over the next quarter. "
                "Propose a hedge plan that protects margin while retaining some upside." 
            ),
            "recommended": "short_hedge",
        },
        {
            "id": "price_risk_2",
            "title": "Consumer cost hedge",
            "description": (
                "A fertilizer plant needs to lock in ammonia input costs ahead of seasonal demand spikes. "
                "Choose a hedge type that reduces exposure to rising feedstock prices." 
            ),
            "recommended": "long_hedge",
        },
    ],
    "Calendar Spread": [
        {
            "id": "calendar_1",
            "title": "Winter season spread",
            "description": (
                "You want to capture the spread between front-month and next-season natural gas contracts. "
                "Design a calendar spread hedge that benefits from seasonality while limiting directional risk." 
            ),
            "recommended": "calendar_spread",
        },
        {
            "id": "calendar_2",
            "title": "Grain carry trade",
            "description": (
                "Carry traders are looking at the price gap between nearby and deferred wheat futures. "
                "Identify a spread structure that reflects storage and financing costs." 
            ),
            "recommended": "calendar_spread",
        },
    ],
    "Basis Risk": [
        {
            "id": "basis_1",
            "title": "Pipeline basis hedge",
            "description": (
                "A power generator pays a fixed basis over a benchmark gas contract. "
                "Construct a hedge that protects the basis differential rather than the benchmark price alone." 
            ),
            "recommended": "basis_hedge",
        },
        {
            "id": "basis_2",
            "title": "Refinery crack spread",
            "description": (
                "A refinery is exposed to the difference between crude and refined product prices. "
                "Choose a position that isolates the margin component of the trade." 
            ),
            "recommended": "basis_hedge",
        },
    ],
    "Volatility & Risk": [
        {
            "id": "volatility_1",
            "title": "Storage value hedge",
            "description": (
                "A natural gas storage operator wants to protect against sudden volatility spikes ahead of winter. "
                "Select a hedge approach that reduces exposure to price swings." 
            ),
            "recommended": "basis_hedge",
        },
        {
            "id": "volatility_2",
            "title": "Electricity load hedge",
            "description": (
                "A utility is hedging against load volatility while remaining exposed to mild weather upside. "
                "Design a balanced hedge with defined downside protection." 
            ),
            "recommended": "short_hedge",
        },
    ],
}


def get_practice_categories() -> list[str]:
    return list(SCENARIO_CATEGORIES.keys())


def get_scenarios(category: str) -> list[dict[str, Any]]:
    return SCENARIO_CATEGORIES.get(category, [])


def evaluate_plan(category: str, hedge_type: str, side: str) -> dict[str, Any]:
    scenarios = get_scenarios(category)
    if not scenarios:
        return {
            "score": 0,
            "feedback": "Select a valid category and propose a hedge plan.",
        }

    expected = {item["recommended"] for item in scenarios}
    base_score = 60 if hedge_type in expected else 30
    side_bonus = 5 if (category == "Price Risk Hedge" and side == "sell") or (category == "Volatility & Risk" and side == "sell") else 0
    return {
        "score": min(100, base_score + side_bonus),
        "feedback": (
            "This plan is aligned with the category if you selected a hedge structure that offsets directionally biased risk. "
            "For better scores, match the hedge type to the scenario’s primary risk exposure and explain the rationale clearly."
        ),
    }
