from __future__ import annotations

import pandas as pd
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
    assert {source["label"] for source in payload["data_sources"]} >= {"Platts", "Yahoo Finance", "Simulated"}


def test_scenarios_endpoint_returns_natural_gas_only() -> None:
    response = client.get("/api/v1/scenarios", params={"locale": "en"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["categories"][0]["id"] == "natural_gas"
    assert payload["scenarios"]
    assert {scenario["commodity"] for scenario in payload["scenarios"]} == {"natural_gas"}
    assert {scenario["region"] for scenario in payload["scenarios"]} >= {"europe", "north_america"}


def test_provider_settings_endpoint_accepts_user_key_without_echoing_secret(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    response = client.post(
        "/api/v1/provider-settings",
        json={"api_key": "user-secret-key", "base_url": "http://localhost:9999/v1", "model": "V4-Flash"},
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
    assert payload["market"]["data_source"] == "simulated"
    assert payload["market"]["symbol"] == "NG=F"
    assert payload["capacity"]["congestion_status"] == "constrained"


def test_context_endpoint_uses_yahoo_finance_when_available(monkeypatch) -> None:
    def fake_fetch_history_daily(ticker, period_if_no_start="3mo", start=None):
        assert ticker == "NG=F"
        assert period_if_no_start == "3mo"
        return pd.DataFrame(
            [
                {"date": pd.Timestamp("2026-05-01").date(), "close": 3.1111},
                {"date": pd.Timestamp("2026-05-02").date(), "close": 3.2222},
            ]
        )

    monkeypatch.setattr("core.yf_prices.fetch_history_daily", fake_fetch_history_daily)
    response = client.get(
        "/api/v1/scenarios/winter_load_spike/context",
        params={"locale": "en", "source": "Yahoo Finance"},
    )
    assert response.status_code == 200
    market = response.json()["market"]
    assert market["source"] == "yfinance"
    assert market["data_source"] == "yfinance"
    assert market["latest_price"] == 3.2222
    assert market["metadata"]["is_fallback"] is False


def test_context_endpoint_falls_back_when_yahoo_finance_is_empty(monkeypatch) -> None:
    monkeypatch.setattr("core.yf_prices.fetch_history_daily", lambda *args, **kwargs: pd.DataFrame())
    response = client.get(
        "/api/v1/scenarios/winter_load_spike/context",
        params={"locale": "en", "source": "yfinance"},
    )
    assert response.status_code == 200
    market = response.json()["market"]
    assert market["source"] == "yfinance"
    assert market["data_source"] == "simulated"
    assert market["metadata"]["is_fallback"] is True


def test_evaluate_endpoint_returns_deterministic_result() -> None:
    response = client.post(
        "/api/v1/attempts/evaluate",
        json={
            "scenario_id": "producer_short_hedge",
            "locale": "en",
            "order": {"side": "sell", "quantity": 80000, "hedge_type": "short_hedge"},
            "rationale": "Sell futures to protect production revenue if prices fall.",
        },
    )
    assert response.status_code == 200
    evaluation = response.json()["evaluation"]
    assert evaluation["valid"] is True
    assert evaluation["baseline_score"] >= 80
    assert evaluation["score_inputs"]["actual_side"] == "sell"


def test_ai_generate_requires_haineng_when_missing(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    response = client.post(
        "/api/v1/ai/generate",
        json={"capability": "case_generation", "scenario_id": "europe_ttf_nbp_spread", "locale": "en"},
    )
    assert response.status_code == 428
    assert "海能 is required" in response.json()["detail"]


def test_legacy_advisor_and_exam_require_haineng_when_missing(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
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
        json={"scenario_id": "producer_short_hedge", "locale": "en", "attempt_history": [{"baseline_score": 95}]},
    )
    assert advisor_response.status_code == 428
    assert exam_response.status_code == 428


def test_ai_capabilities_cover_realistic_europe_gas_workflows(monkeypatch) -> None:
    captured_prompts: list[str] = []

    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            text = "\n".join(message["content"] for message in messages)
            captured_prompts.append(text)
            assert "secret-key" not in text
            assert "Europe" in text or "TTF" in text or "NBP" in text
            if "business case" in text:
                return "Case background: European gas marketer hedges TTF/NBP spread. Exposure: basis and capacity. Decision task: choose hedge ratio."
            if "event-driven" in text:
                return "Event transmission path: Norwegian outage affects TTF supply risk. Checklist: verify outage, storage, nominations."
            if "Teach one energy trading concept" in text:
                return "Plain-language definition: Basis is the difference between locations. Practical example: TTF/NBP spread."
            if "pre-trade playbook" in text:
                return "Objective and exposure: lock European gas margin. Pre-trade checklist: liquidity, units, FX, capacity, credit, limits."
            if "assessment questions" in text:
                return "Q1: Why normalize NBP and TTF units? Answer key: units and FX affect spread comparison."
            return "Decision diagnosis: hedge side and basis risk reviewed."

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    base_payload = {"scenario_id": "europe_ttf_nbp_spread", "locale": "en", "source": "sample"}
    requests = [
        {**base_payload, "capability": "case_generation", "user_request": "Build a case for TTF/NBP spread margin training."},
        {**base_payload, "capability": "event_drill", "event_context": "Norwegian offshore maintenance reduces flows into Northwest Europe."},
        {**base_payload, "capability": "concept_tutor", "concept": "TTF/NBP basis and unit normalization"},
        {**base_payload, "capability": "trade_playbook", "commercial_goal": "Prepare a pre-trade checklist for a TTF-NBP spread hedge."},
        {**base_payload, "capability": "exam", "attempt_history": [{"baseline_score": 72, "mistake_tags": ["basis_risk"]}]},
    ]
    for payload in requests:
        response = client.post("/api/v1/ai/generate", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["capability"] == payload["capability"]
        assert body["scenario"]["id"] == "europe_ttf_nbp_spread"
        assert body["answer"]
    assert len(captured_prompts) == len(requests)
    assert any("Norwegian offshore maintenance" in prompt for prompt in captured_prompts)
    assert any("pre-trade checklist" in prompt for prompt in captured_prompts)


def test_legacy_advisor_and_exam_return_haineng_answers_when_configured(monkeypatch) -> None:
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
        json={"scenario_id": "producer_short_hedge", "locale": "en", "attempt_history": [{"baseline_score": 95}]},
    )
    assert advisor_response.status_code == 200
    assert advisor_response.json()["answer"] == "provider answer"
    assert exam_response.status_code == 200
    assert exam_response.json()["exam"] == "provider answer"


def test_haineng_provider_failure_returns_structured_502(monkeypatch) -> None:
    class FailingClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            raise RuntimeError("provider rejected token=secret-key")

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FailingClient())
    response = client.post(
        "/api/v1/ai/generate",
        json={"capability": "case_generation", "scenario_id": "europe_ttf_nbp_spread", "locale": "en"},
    )
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == "haineng_request_failed"
    assert "secret-key" not in str(detail)
    assert "token=[REDACTED]" in detail["provider_message"]


def test_unknown_scenario_returns_404() -> None:
    response = client.get("/api/v1/scenarios/not-a-scenario/context")
    assert response.status_code == 404
    assert "Unknown scenario" in response.json()["detail"]
