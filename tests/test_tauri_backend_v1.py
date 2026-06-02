from __future__ import annotations

from fastapi.testclient import TestClient

from tauri.backend.main import app


client = TestClient(app)


def _clear_haineng_env(monkeypatch) -> None:
    monkeypatch.delenv("HAINENG_API_KEY", raising=False)
    monkeypatch.delenv("HAINENG_BASE_URL", raising=False)


def test_provider_status_reports_missing_haineng_without_secret(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    monkeypatch.setenv("PLATTS_API_KEY", "platts-secret-value")

    response = client.get("/api/v1/provider-status")

    assert response.status_code == 200
    payload = response.json()
    payload_text = str(payload).lower()
    assert "haineng" in payload
    assert payload["haineng"]["ok"] is False
    assert "api_key" not in payload_text
    assert "platts-secret-value" not in payload_text
    assert {source["label"] for source in payload["data_sources"]} >= {
        "Platts",
        "Yahoo Finance",
        "Simulated",
    }


def test_scenarios_endpoint_returns_natural_gas_only() -> None:
    response = client.get("/api/v1/scenarios", params={"locale": "en"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["categories"][0]["id"] == "natural_gas"
    assert payload["scenarios"]
    assert {scenario["commodity"] for scenario in payload["scenarios"]} == {"natural_gas"}


def test_context_endpoint_returns_market_and_capacity() -> None:
    response = client.get(
        "/api/v1/scenarios/pipeline_capacity_constraint/context",
        params={"locale": "en", "source": "sample"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"]["id"] == "pipeline_capacity_constraint"
    assert payload["market"]["scenario_id"] == "pipeline_capacity_constraint"
    assert payload["market"]["source"] == "sample"
    assert payload["market"]["source_label"] == "Simulated"
    assert payload["market"]["data_source"] == "simulated"
    assert payload["market"]["data_source_label"] == "Simulated"
    assert payload["market"]["symbol"] == "NG=F"
    assert payload["capacity"]["scenario_id"] == "pipeline_capacity_constraint"
    assert payload["capacity"]["congestion_status"] == "constrained"


def test_context_endpoint_supports_yahoo_finance_label_with_simulated_fallback() -> None:
    response = client.get(
        "/api/v1/scenarios/winter_load_spike/context",
        params={"locale": "en", "source": "Yahoo Finance"},
    )

    assert response.status_code == 200
    market = response.json()["market"]
    assert market["source"] == "yfinance"
    assert market["source_label"] == "Yahoo Finance"
    assert market["data_source"] == "simulated"
    assert market["data_source_label"] == "Simulated"
    assert market["metadata"]["requested_source_label"] == "Yahoo Finance"
    assert market["metadata"]["returned_source_label"] == "Simulated"
    assert market["metadata"]["is_fallback"] is True


def test_evaluate_endpoint_returns_deterministic_result() -> None:
    response = client.post(
        "/api/v1/attempts/evaluate",
        json={
            "scenario_id": "producer_short_hedge",
            "locale": "en",
            "order": {
                "side": "sell",
                "quantity": 80000,
                "hedge_type": "short_hedge",
            },
            "rationale": "Sell futures to protect production revenue if prices fall.",
        },
    )

    assert response.status_code == 200
    evaluation = response.json()["evaluation"]
    assert evaluation["valid"] is True
    assert evaluation["baseline_score"] >= 80
    assert evaluation["score_inputs"]["actual_side"] == "sell"


def test_advisor_and_exam_require_haineng_when_missing(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    advisor_response = client.post(
        "/api/v1/advisor/review",
        json={
            "scenario_id": "producer_short_hedge",
            "locale": "en",
            "order": {
                "side": "sell",
                "quantity": 80000,
                "hedge_type": "short_hedge",
            },
            "rationale": "Sell futures to hedge production.",
            "evaluation": {"valid": True, "baseline_score": 95},
        },
    )
    exam_response = client.post(
        "/api/v1/exam/generate",
        json={
            "scenario_id": "producer_short_hedge",
            "locale": "en",
            "attempt_history": [{"baseline_score": 95, "mistake_tags": []}],
        },
    )

    assert advisor_response.status_code == 428
    assert "海能 is required before advisor review." in advisor_response.json()["detail"]
    assert exam_response.status_code == 428
    assert "海能 is required before exam generation." in exam_response.json()["detail"]


def test_unknown_scenario_returns_404() -> None:
    response = client.get("/api/v1/scenarios/not-a-scenario/context")

    assert response.status_code == 404
    assert "Unknown scenario" in response.json()["detail"]
