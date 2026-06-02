from __future__ import annotations

import pytest

from core.gas_scenarios import get_capacity_context, get_scenario
from core.learning_session import evaluate_attempt, validate_order


def test_validate_order_rejects_missing_quantity() -> None:
    errors = validate_order({"side": "sell", "quantity": 0, "hedge_type": "short_hedge"})
    assert "quantity" in errors


@pytest.mark.parametrize(
    "order",
    [
        {"side": "hold", "quantity": 1000, "hedge_type": "short_hedge"},
        {"side": "sell", "quantity": "many", "hedge_type": "short_hedge"},
        {"side": "sell", "quantity": 1000},
    ],
)
def test_validate_order_rejects_invalid_required_fields(order: dict[str, object]) -> None:
    assert validate_order(order)


def test_evaluate_attempt_returns_errors_for_invalid_orders() -> None:
    scenario = get_scenario("producer_short_hedge", locale="en")

    result = evaluate_attempt(
        scenario=scenario,
        capacity_context=get_capacity_context("producer_short_hedge"),
        order={"side": "sell", "quantity": 0, "hedge_type": "short_hedge"},
        rationale="I sell futures to offset falling price risk.",
    )

    assert result["valid"] is False
    assert "quantity" in result["errors"]


def test_evaluate_attempt_scores_recommended_producer_hedge() -> None:
    scenario = get_scenario("producer_short_hedge", locale="en")
    result = evaluate_attempt(
        scenario=scenario,
        capacity_context=get_capacity_context("producer_short_hedge"),
        order={
            "side": "sell",
            "quantity": 80000,
            "hedge_type": "short_hedge",
            "price": 3.5,
        },
        rationale="I sell futures to offset falling price risk on expected production.",
    )
    assert result["valid"] is True
    assert result["score_inputs"]["direction_match"] is True
    assert result["score_inputs"]["hedge_type_match"] is True
    assert result["metrics"]["hedge_ratio"] == 0.8
    assert result["metrics"]["notional_usd"] == 280000.0
    assert result["metrics"]["capacity_utilization_pct"] == 80.0
    assert result["baseline_score"] >= 80


def test_evaluate_attempt_tags_capacity_blind_spot() -> None:
    scenario = get_scenario("pipeline_capacity_constraint", locale="en")
    result = evaluate_attempt(
        scenario=scenario,
        capacity_context=get_capacity_context("pipeline_capacity_constraint"),
        order={
            "side": "buy",
            "quantity": 60000,
            "hedge_type": "long_hedge",
            "price": 3.4,
        },
        rationale="I buy futures because prices may rise.",
    )
    assert "wrong_direction" in result["mistake_tags"]
    assert "ignores_capacity" in result["mistake_tags"]
    assert result["metrics"]["basis_impact_usd"] == pytest.approx(4500.0)
    assert result["baseline_score"] < 70
