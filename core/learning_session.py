"""Deterministic evaluation helpers for natural gas hedging practice."""
from __future__ import annotations

from typing import Any


_VALID_SIDES = {"buy", "sell", "spread"}
_OUTRIGHT_HEDGE_TYPES = {"long_hedge", "short_hedge"}
_CAPACITY_TERMS = {
    "basis",
    "capacity",
    "constraint",
    "congestion",
    "flow",
    "nomination",
    "pipeline",
    "transport",
}


def validate_order(order: dict[str, Any]) -> dict[str, str]:
    """Return field-level validation errors for a hedge order."""
    errors: dict[str, str] = {}

    side = _normalized_text(order.get("side"))
    if side not in _VALID_SIDES:
        errors["side"] = "Side must be one of: buy, sell, spread."

    quantity = _to_float(order.get("quantity"))
    if quantity is None:
        errors["quantity"] = "Quantity is required and must be numeric."
    elif quantity <= 0:
        errors["quantity"] = "Quantity must be greater than zero."

    hedge_type = _normalized_text(order.get("hedge_type"))
    if not hedge_type:
        errors["hedge_type"] = "Hedge type is required."

    return errors


def classify_mistakes(
    scenario: dict[str, Any],
    capacity_context: dict[str, Any],
    order: dict[str, Any],
    rationale: str,
) -> list[str]:
    """Return deterministic mistake tags for an otherwise valid attempt."""
    score_inputs = _build_score_inputs(scenario, capacity_context, order, rationale)
    tags: list[str] = []

    if not score_inputs["direction_match"]:
        tags.append("wrong_direction")
    if not score_inputs["hedge_type_match"]:
        tags.append("wrong_hedge_type")
    if score_inputs["hedge_ratio"] < 0.5:
        tags.append("under_hedged")
    elif score_inputs["hedge_ratio"] > 1.25:
        tags.append("over_hedged")
    if score_inputs["capacity_sensitive"] and not score_inputs["mentions_capacity"]:
        tags.append("ignores_capacity")

    return tags


def evaluate_attempt(
    scenario: dict[str, Any],
    capacity_context: dict[str, Any],
    order: dict[str, Any],
    rationale: str,
) -> dict[str, Any]:
    """Score one natural gas hedging attempt without external services."""
    errors = validate_order(order)
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "score_inputs": {},
            "mistake_tags": [],
            "baseline_score": 0,
            "metrics": {},
        }

    score_inputs = _build_score_inputs(scenario, capacity_context, order, rationale)
    mistake_tags = classify_mistakes(scenario, capacity_context, order, rationale)
    baseline_score = _score_attempt(score_inputs, mistake_tags)

    return {
        "valid": True,
        "errors": {},
        "score_inputs": score_inputs,
        "mistake_tags": mistake_tags,
        "baseline_score": baseline_score,
        "metrics": _build_metrics(scenario, capacity_context, order),
    }


def _build_score_inputs(
    scenario: dict[str, Any],
    capacity_context: dict[str, Any],
    order: dict[str, Any],
    rationale: str,
) -> dict[str, Any]:
    expected_side = _normalized_text(scenario.get("recommended_side"))
    expected_hedge_type = _normalized_text(scenario.get("recommended_hedge_type"))
    actual_side = _normalized_text(order.get("side"))
    actual_hedge_type = _normalized_text(order.get("hedge_type"))
    capacity_sensitive = _is_capacity_sensitive(scenario, capacity_context)

    direction_match = bool(expected_side and actual_side == expected_side)
    if capacity_sensitive and actual_hedge_type in _OUTRIGHT_HEDGE_TYPES:
        direction_match = False

    return {
        "expected_side": expected_side,
        "actual_side": actual_side,
        "direction_match": direction_match,
        "expected_hedge_type": expected_hedge_type,
        "actual_hedge_type": actual_hedge_type,
        "hedge_type_match": bool(
            expected_hedge_type and actual_hedge_type == expected_hedge_type
        ),
        "hedge_ratio": _hedge_ratio(scenario, order),
        "capacity_sensitive": capacity_sensitive,
        "mentions_capacity": _mentions_capacity(rationale),
    }


def _build_metrics(
    scenario: dict[str, Any],
    capacity_context: dict[str, Any],
    order: dict[str, Any],
) -> dict[str, float]:
    quantity = _to_float(order.get("quantity")) or 0.0
    metrics: dict[str, float] = {
        "hedge_ratio": _hedge_ratio(scenario, order),
    }

    price = _to_float(order.get("price"))
    if price is not None:
        metrics["notional_usd"] = round(quantity * price, 2)

    capacity_utilization = _capacity_utilization_pct(capacity_context)
    if capacity_utilization is not None:
        metrics["capacity_utilization_pct"] = capacity_utilization

    basis_impact = _basis_impact_usd(capacity_context, quantity)
    if basis_impact is not None:
        metrics["basis_impact_usd"] = basis_impact

    return metrics


def _score_attempt(score_inputs: dict[str, Any], mistake_tags: list[str]) -> int:
    score = 100

    if "wrong_direction" in mistake_tags:
        score -= 35
    if "wrong_hedge_type" in mistake_tags:
        score -= 25
    if "under_hedged" in mistake_tags or "over_hedged" in mistake_tags:
        score -= 15
    if "ignores_capacity" in mistake_tags:
        score -= 20

    hedge_ratio = score_inputs["hedge_ratio"]
    if 0.5 <= hedge_ratio < 0.75 or 1.1 < hedge_ratio <= 1.25:
        score -= 5

    return max(0, min(100, score))


def _hedge_ratio(scenario: dict[str, Any], order: dict[str, Any]) -> float:
    quantity = _to_float(order.get("quantity")) or 0.0
    exposure = scenario.get("exposure") or {}
    exposure_volume = _to_float(exposure.get("volume_mmbtu"))
    if not exposure_volume or exposure_volume <= 0:
        return 0.0
    return round(quantity / exposure_volume, 4)


def _capacity_utilization_pct(capacity_context: dict[str, Any]) -> float | None:
    utilization = _to_float(capacity_context.get("utilization_pct"))
    if utilization is not None:
        return round(utilization, 1)

    nominated = _to_float(capacity_context.get("nominated_mmbtu"))
    available = _to_float(capacity_context.get("available_capacity_mmbtu"))
    if nominated is None or not available or available <= 0:
        return None
    return round((nominated / available) * 100, 1)


def _basis_impact_usd(
    capacity_context: dict[str, Any],
    quantity_mmbtu: float,
) -> float | None:
    configured_impact = _to_float(capacity_context.get("basis_impact_usd"))
    if configured_impact is not None:
        return round(configured_impact, 2)

    explicit_basis = _first_numeric(
        capacity_context,
        (
            "basis_delta_usd_per_mmbtu",
            "basis_widening_usd_per_mmbtu",
            "basis_usd_per_mmbtu",
        ),
    )
    if explicit_basis is not None:
        return round(quantity_mmbtu * explicit_basis, 2)

    utilization = _capacity_utilization_pct(capacity_context)
    if utilization is None or utilization <= 85:
        return None

    stress_basis = (utilization - 85.0) / 100.0
    return round(quantity_mmbtu * stress_basis, 2)


def _is_capacity_sensitive(
    scenario: dict[str, Any],
    capacity_context: dict[str, Any],
) -> bool:
    scenario_id = _normalized_text(scenario.get("id"))
    recommended_hedge_type = _normalized_text(scenario.get("recommended_hedge_type"))
    congestion_status = _normalized_text(capacity_context.get("congestion_status"))

    return (
        "capacity" in scenario_id
        or recommended_hedge_type == "basis_hedge"
        or congestion_status in {"watch", "constrained"}
    )


def _mentions_capacity(rationale: str) -> bool:
    words = set(_normalized_text(rationale).replace("/", " ").split())
    return bool(words & _CAPACITY_TERMS)


def _normalized_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_numeric(
    values: dict[str, Any],
    keys: tuple[str, ...],
) -> float | None:
    for key in keys:
        value = _to_float(values.get(key))
        if value is not None:
            return value
    return None
