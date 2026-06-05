from __future__ import annotations

from fastapi.testclient import TestClient

from tauri.backend.main import app


client = TestClient(app)


def _clear_haineng_env(monkeypatch) -> None:
    from core.haineng_client import set_runtime_settings

    set_runtime_settings(None)
    monkeypatch.delenv("HAINENG_API_KEY", raising=False)
    monkeypatch.delenv("HAINENG_BASE_URL", raising=False)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "commodity-lab-backend"}


def test_instruments_limit_is_bounded() -> None:
    response = client.get("/api/instruments", params={"limit": 0})

    assert response.status_code == 422


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


def test_provider_settings_endpoint_accepts_user_key_without_echoing_secret(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)

    response = client.post(
        "/api/v1/provider-settings",
        json={
            "api_key": "user-secret-key",
            "base_url": "http://localhost:9999/v1",
            "model": "V4-Flash",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["haineng"]["ok"] is True
    assert payload["haineng"]["base_url"] == "http://localhost:9999/v1"
    assert payload["haineng"]["model"] == "V4-Flash"
    assert "user-secret-key" not in str(payload)

    _clear_haineng_env(monkeypatch)


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


def test_advisor_and_exam_return_haineng_answers_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("HAINENG_API_KEY", "secret-key")
    monkeypatch.setenv("HAINENG_BASE_URL", "http://local/v1")

    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            assert tools is None
            assert messages
            return "provider answer"

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())

    advisor_response = client.post(
        "/api/v1/advisor/review",
        json={
            "scenario_id": "producer_short_hedge",
            "locale": "en",
            "order": {"side": "sell", "quantity": 80000, "hedge_type": "short_hedge"},
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

    assert advisor_response.status_code == 200
    assert advisor_response.json()["answer"] == "provider answer"
    assert exam_response.status_code == 200
    assert exam_response.json()["exam"] == "provider answer"


def test_haineng_provider_failure_returns_structured_502(monkeypatch) -> None:
    monkeypatch.setenv("HAINENG_API_KEY", "secret-key")
    monkeypatch.setenv("HAINENG_BASE_URL", "http://local/v1")

    class FailingClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            raise RuntimeError("provider rejected token=secret-key")

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FailingClient())

    response = client.post(
        "/api/v1/advisor/review",
        json={
            "scenario_id": "producer_short_hedge",
            "locale": "en",
            "order": {"side": "sell", "quantity": 80000, "hedge_type": "short_hedge"},
            "rationale": "Sell futures to hedge production.",
            "evaluation": {"valid": True, "baseline_score": 95},
        },
    )

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == "haineng_request_failed"
    assert detail["message"] == "海能 request failed."
    assert "secret-key" not in str(detail)
    assert "token=[REDACTED]" in detail["provider_message"]


def test_unknown_scenario_returns_404() -> None:
    response = client.get("/api/v1/scenarios/not-a-scenario/context")

    assert response.status_code == 404
    assert "Unknown scenario" in response.json()["detail"]
