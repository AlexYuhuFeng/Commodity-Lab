from __future__ import annotations

from fastapi.testclient import TestClient

from core.market_learning import (
    build_replay_session,
    build_simulated_market_context,
    classify_forward_curve,
    evaluate_replay_decision,
    list_replay_events,
    market_capability_catalog,
    replay_authoring_schema,
    review_replay_event,
)
from tauri.backend.main import app


client = TestClient(app)


def test_classify_forward_curve_distinguishes_market_structure() -> None:
    assert classify_forward_curve([30.0, 31.0, 32.0, 33.0])["structure"] == "contango"
    assert classify_forward_curve([33.0, 32.0, 31.0, 30.0])["structure"] == "backwardation"
    assert classify_forward_curve([30.0, 30.05, 29.98, 30.02])["structure"] == "flat"


def test_simulated_market_context_is_deterministic_and_provenanced() -> None:
    first = build_simulated_market_context(
        commodity="crude_oil",
        regime="backwardation",
        seed=17,
        as_of="2026-07-17",
        locale="en",
    )
    second = build_simulated_market_context(
        commodity="crude_oil",
        regime="backwardation",
        seed=17,
        as_of="2026-07-17",
        locale="en",
    )

    assert first == second
    assert first["curve_metrics"]["structure"] == "backwardation"
    assert len(first["forward_curve"]) == 12
    assert len(first["history"]) >= 30
    assert first["provenance"]["mode"] == "ai_simulated"
    assert first["provenance"]["is_live"] is False
    assert first["provenance"]["source_tier"] == "synthetic"


def test_replay_session_never_leaks_future_checkpoint_information() -> None:
    session = build_replay_session("hormuz_2026_disruption", checkpoint=0, locale="en")

    assert session["event"]["id"] == "hormuz_2026_disruption"
    assert session["current_checkpoint"]["index"] == 0
    assert session["next_checkpoint"] == 1
    assert len(session["visible_timeline"]) == 1
    assert "June 17" not in str(session)
    assert "target_actions" not in str(session)
    assert sum(item["points"] for item in session["decision_rubric"]) == 100
    assert session["market"]["provenance"]["mode"] == "historical_replay"
    assert session["market"]["provenance"]["source_tier"] == "historically_calibrated_simulation"
    assert session["source_notes"] == []


def test_natural_gas_replay_moves_from_supply_shock_to_lng_congestion_without_future_leakage() -> None:
    first = build_replay_session("european_gas_crisis_2022", checkpoint=0, locale="en")
    final = build_replay_session("european_gas_crisis_2022", checkpoint=2, locale="en")

    assert first["event"]["commodity"] == "natural_gas"
    assert first["current_checkpoint"]["label"] == "Supply tightening and refill competition"
    assert "High storage and LNG congestion" not in str(first)
    assert first["market"]["curve_metrics"]["structure"] == "backwardation"
    assert final["current_checkpoint"]["label"] == "High storage and LNG congestion"
    assert final["market"]["curve_metrics"]["structure"] == "contango"
    assert all(note["available_from"] <= "2022-10-24" for note in final["source_notes"])


def test_2021_gas_refill_replay_preserves_point_in_time_sources_and_sequence() -> None:
    first = build_replay_session("european_gas_refill_squeeze_2021", checkpoint=0, locale="en")
    second = build_replay_session("european_gas_refill_squeeze_2021", checkpoint=1, locale="en")
    final = build_replay_session("european_gas_refill_squeeze_2021", checkpoint=2, locale="en")

    assert first["current_checkpoint"]["label"] == "Low inventories enter refill season"
    assert "High-price winter entry" not in str(first)
    assert first["source_notes"] == []
    assert len(second["source_notes"]) == 2
    assert all(note["available_from"] <= "2021-09-21" for note in second["source_notes"])
    assert final["current_checkpoint"]["label"] == "High-price winter entry and rebalancing"
    assert final["market"]["provenance"]["requested_regime"] == "volatile"


def test_wti_storage_replay_teaches_expiry_delivery_and_calendar_risk() -> None:
    first = build_replay_session("wti_storage_squeeze_2020", checkpoint=0, locale="en")
    squeeze = build_replay_session("wti_storage_squeeze_2020", checkpoint=1, locale="en")
    final = build_replay_session("wti_storage_squeeze_2020", checkpoint=2, locale="en")

    assert first["event"]["commodity"] == "crude_oil"
    assert first["event"]["exposure"]["direction"] == "inventory_long"
    assert first["market"]["benchmark"] == "WTI"
    assert "Prompt contract turns negative" not in str(first)
    assert squeeze["current_checkpoint"]["label"] == "Prompt contract turns negative"
    assert squeeze["market"]["provenance"]["requested_regime"] == "volatile"
    assert squeeze["market"]["forward_curve"][0]["price"] == -37.63
    assert squeeze["market"]["forward_curve"][1]["price"] > 0
    assert squeeze["market"]["history"][-1]["close"] == -37.63
    assert squeeze["market"]["curve_metrics"]["structure"] == "contango"
    assert squeeze["source_notes"] == []
    assert {note["publisher"] for note in final["source_notes"]} == {
        "U.S. Energy Information Administration",
    }


def test_replay_catalog_contains_two_business_distinct_events_per_active_product() -> None:
    events = list_replay_events(locale="en")
    by_commodity = {
        commodity: [event for event in events if event["commodity"] == commodity]
        for commodity in {event["commodity"] for event in events}
    }

    assert len(by_commodity["natural_gas"]) >= 2
    assert len(by_commodity["crude_oil"]) >= 2
    assert all(event["review"]["status"] == "reviewed" for event in events)


def test_replay_authoring_contract_reviews_sources_chronology_and_actions() -> None:
    schema = replay_authoring_schema()
    assert schema["version"] == 1
    assert {"date", "facts", "decision_required", "target_actions", "outcome"}.issubset(schema["checkpoint_required"])
    for event in list_replay_events(locale="en"):
        review = review_replay_event(event["id"])
        assert review["status"] == "reviewed"
        assert review["issues"] == []
        assert all(review["checks"].values())


def test_natural_gas_replay_scores_storage_and_regas_reasoning_locally() -> None:
    result = evaluate_replay_decision(
        "european_gas_crisis_2022",
        checkpoint=0,
        locale="en",
        strategy_legs=[
            {"leg_type": "physical", "market": "Flexible LNG / pipeline supply", "side": "buy", "quantity": 100000, "tenor": "Q4"},
            {"leg_type": "swap", "market": "TTF Q4 swap", "side": "buy", "quantity": 70000, "tenor": "Q4"},
            {"leg_type": "option", "market": "TTF call", "side": "buy", "quantity": 30000, "tenor": "Q4"},
            {"leg_type": "capacity", "market": "Storage injection / regas slot", "side": "buy", "quantity": 1, "tenor": "Summer-Q4"},
        ],
        rationale="Cover TTF price and basis risk with options, storage and regas capacity; check margin, liquidity, limits, credit, and execution.",
    )

    assert result["evaluation"]["baseline_score"] >= 90
    assert "storage/capacity" in result["evaluation"]["rubric"][1]["rule"]


def test_natural_gas_replay_accepts_future_as_a_swap_substitute_for_flat_price_cover() -> None:
    result = evaluate_replay_decision(
        "european_gas_crisis_2022",
        checkpoint=0,
        locale="en",
        strategy_legs=[
            {"leg_type": "physical", "market": "Flexible LNG / pipeline supply", "side": "buy", "quantity": 100000, "tenor": "Q4"},
            {"leg_type": "future", "market": "TTF Q4 future", "side": "buy", "quantity": 70000, "tenor": "Q4"},
            {"leg_type": "option", "market": "TTF call", "side": "buy", "quantity": 30000, "tenor": "Q4"},
            {"leg_type": "capacity", "market": "Storage injection / regas slot", "side": "buy", "quantity": 1, "tenor": "Summer-Q4"},
        ],
        rationale="Cover TTF price and basis risk with options, storage and regas capacity; check margin, liquidity, limits, credit, and execution.",
    )

    assert result["evaluation"]["baseline_score"] >= 90
    assert "incomplete_decision_structure" not in result["evaluation"]["mistake_tags"]


def test_market_capability_catalog_separates_live_replay_and_simulation(monkeypatch) -> None:
    monkeypatch.delenv("COMMODITY_LAB_PLATTS_CLIENT_ID", raising=False)
    monkeypatch.delenv("COMMODITY_LAB_PLATTS_CLIENT_SECRET", raising=False)

    catalog = market_capability_catalog(locale="en")

    assert {mode["id"] for mode in catalog["modes"]} == {"live", "historical_replay", "ai_simulated"}
    platts = next(provider for provider in catalog["providers"] if provider["id"] == "platts")
    assert platts["status"] == "not_configured"
    assert "secret" not in str(catalog).lower()
    assert catalog["fallback_mode"] == "ai_simulated"


def test_market_simulation_endpoint_returns_curve_regime() -> None:
    response = client.post(
        "/api/v1/market/simulate",
        json={
            "commodity": "natural_gas",
            "regime": "contango",
            "seed": 9,
            "as_of": "2026-07-17",
            "locale": "zh",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["curve_metrics"]["structure"] == "contango"
    assert payload["provenance"]["label"] == "AI 模拟市场"


def test_replay_catalog_and_session_endpoints() -> None:
    catalog_response = client.get("/api/v1/replays", params={"locale": "en"})
    assert catalog_response.status_code == 200
    assert any(item["id"] == "hormuz_2026_disruption" for item in catalog_response.json()["events"])

    session_response = client.post(
        "/api/v1/replays/hormuz_2026_disruption/session",
        json={"checkpoint": 0, "locale": "en"},
    )
    assert session_response.status_code == 200
    session = session_response.json()
    assert session["current_checkpoint"]["decision_required"]
    assert session["market"]["curve_metrics"]["structure"] in {"contango", "backwardation", "flat"}


def test_replay_decision_scores_locally_and_reveals_model_strategy_only_after_submission() -> None:
    result = evaluate_replay_decision(
        "hormuz_2026_disruption",
        checkpoint=0,
        locale="en",
        strategy_legs=[
            {"leg_type": "physical", "market": "Middle East crude cargo", "side": "buy", "quantity": 100000, "tenor": "M+2"},
            {"leg_type": "future", "market": "ICE Brent", "side": "buy", "quantity": 70000, "tenor": "M+2"},
            {"leg_type": "option", "market": "Brent call", "side": "buy", "quantity": 30000, "tenor": "M+2"},
            {"leg_type": "capacity", "market": "VLCC freight", "side": "buy", "quantity": 1, "tenor": "M+2"},
        ],
        rationale="Cover flat price, calendar spread, option and freight risk; check margin, liquidity, limits, credit, and execution.",
    )

    assert result["evaluation"]["baseline_score"] >= 90
    assert result["next_checkpoint"] == 1
    assert result["model_strategy"]
    assert len(result["alternative_strategies"]) == 2
    assert {alternative["id"] for alternative in result["alternative_strategies"]} == {"staged", "option_weighted"}
    assert all(alternative["rationale"] and alternative["tradeoff"] for alternative in result["alternative_strategies"])
    assert all(alternative["legs"] != result["model_strategy"] for alternative in result["alternative_strategies"])
    assert result["outcome"]


def test_replay_decision_endpoint_returns_zero_for_an_empty_decision() -> None:
    response = client.post(
        "/api/v1/replays/hormuz_2026_disruption/decision",
        json={"checkpoint": 0, "locale": "zh", "strategy_legs": [], "rationale": ""},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["baseline_score"] == 0
    assert "missing_physical_leg" in payload["evaluation"]["mistake_tags"]
    assert payload["checkpoint"]["label"] == "供应通道受阻"
