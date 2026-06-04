from __future__ import annotations

import pytest

from core.gas_scenarios import get_capacity_context, get_scenario
from core.learning_session import classify_mistakes, evaluate_attempt, validate_order


def test_validate_order_rejects_zero_quantity() -> None:
    errors = validate_order({"side": "sell", "quantity": 0, "hedge_type": "short_hedge"})
    assert "quantity" in errors


@pytest.mark.parametrize(
    "order",
    [
        {"side": "hold", "quantity": 1000, "hedge_type": "short_hedge"},
        {"side": "sell", "quantity": "many", "hedge_type": "short_hedge"},
        {"side": "sell", "quantity": 1000},
        {"side": "sell", "hedge_type": "short_hedge"},
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


def test_classify_mistakes_tags_capacity_blind_spot_directly() -> None:
    scenario = get_scenario("pipeline_capacity_constraint", locale="en")
    capacity = get_capacity_context("pipeline_capacity_constraint")
    tags = classify_mistakes(
        scenario=scenario,
        capacity_context=capacity,
        order={"side": "buy", "quantity": 60000, "hedge_type": "long_hedge"},
        rationale="I buy futures because prices may rise.",
    )

    assert "wrong_direction" in tags
    assert "wrong_hedge_type" in tags
    assert "ignores_capacity" in tags


def test_evaluate_attempt_scores_recommended_pipeline_basis_hedge() -> None:
    scenario = get_scenario("pipeline_capacity_constraint", locale="en")
    result = evaluate_attempt(
        scenario=scenario,
        capacity_context=get_capacity_context("pipeline_capacity_constraint"),
        order={
            "side": "sell",
            "quantity": 60000,
            "hedge_type": "basis_hedge",
            "price": 3.4,
        },
        rationale="I sell a basis hedge because pipeline capacity is constrained.",
    )

    assert result["valid"] is True
    assert result["score_inputs"]["direction_match"] is True
    assert result["score_inputs"]["hedge_type_match"] is True
    assert "wrong_direction" not in result["mistake_tags"]
    assert "ignores_capacity" not in result["mistake_tags"]
    assert result["metrics"]["hedge_ratio"] == 1.0
    assert result["baseline_score"] >= 90


def test_pipeline_basis_answer_must_mention_capacity_context() -> None:
    scenario = get_scenario("pipeline_capacity_constraint", locale="en")
    result = evaluate_attempt(
        scenario=scenario,
        capacity_context=get_capacity_context("pipeline_capacity_constraint"),
        order={
            "side": "sell",
            "quantity": 60000,
            "hedge_type": "basis_hedge",
            "price": 3.4,
        },
        rationale="I sell a basis hedge.",
    )

    assert "ignores_capacity" in result["mistake_tags"]


def test_capacity_rationale_handles_punctuation_and_hyphenation() -> None:
    scenario = get_scenario("pipeline_capacity_constraint", locale="en")

    for rationale in ("Pipeline.", "pipeline-capacity risk"):
        result = evaluate_attempt(
            scenario=scenario,
            capacity_context=get_capacity_context("pipeline_capacity_constraint"),
            order={
                "side": "sell",
                "quantity": 60000,
                "hedge_type": "basis_hedge",
                "price": 3.4,
            },
            rationale=rationale,
        )

        assert "ignores_capacity" not in result["mistake_tags"]


def test_regional_basis_hedge_does_not_require_capacity_language() -> None:
    scenario = get_scenario("regional_basis_blowout", locale="en")
    result = evaluate_attempt(
        scenario=scenario,
        capacity_context=get_capacity_context("regional_basis_blowout"),
        order={
            "side": "sell",
            "quantity": 90000,
            "hedge_type": "basis_hedge",
            "price": 2.55,
        },
        rationale="The local discount may widen versus Henry Hub.",
    )

    assert result["score_inputs"]["direction_match"] is True
    assert result["score_inputs"]["hedge_type_match"] is True
    assert result["score_inputs"]["capacity_sensitive"] is False
    assert "ignores_capacity" not in result["mistake_tags"]
    assert result["baseline_score"] >= 90
