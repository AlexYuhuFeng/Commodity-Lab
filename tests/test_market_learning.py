from __future__ import annotations

from fastapi.testclient import TestClient

from core.market_learning import (
    build_replay_session,
    build_simulated_market_context,
    classify_forward_curve,
    evaluate_replay_decision,
    market_capability_catalog,
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
    assert session["source_notes"][0]["url"].startswith("https://www.eia.gov/")


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
