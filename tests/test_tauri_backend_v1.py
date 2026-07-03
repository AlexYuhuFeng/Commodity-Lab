from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from tauri.backend.main import app


client = TestClient(app)


def _clear_haineng_env(monkeypatch) -> None:
    from core.haineng_client import set_runtime_settings

    set_runtime_settings(None)
    monkeypatch.delenv("HAINENG_API_KEY", raising=False)
    monkeypatch.delenv("HAINENG_BASE_URL", raising=False)
    monkeypatch.setenv("COMMODITY_LAB_DISABLE_LOCAL_AI_SETTINGS", "1")


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "commodity-lab-backend"}


def test_instruments_limit_is_bounded() -> None:
    response = client.get("/api/instruments", params={"limit": 0})
    assert response.status_code == 422


def test_provider_status_reports_missing_haineng_without_secret(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    monkeypatch.setenv("UNRELATED_SECRET", "unrelated-secret-value")
    response = client.get("/api/v1/provider-status")
    assert response.status_code == 200
    payload = response.json()
    payload_text = str(payload).lower()
    assert "haineng" in payload
    assert payload["haineng"]["ok"] is False
    assert "api_key" not in payload_text
    assert "unrelated-secret-value" not in payload_text
    assert "data_sources" not in payload
    assert payload["training_data"] == {"mode": "ai_generated", "configured": False}
    assert set(payload["ai_providers"]) >= {"haineng", "deepseek"}


def test_version_endpoint_exposes_developer_and_repo_metadata() -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    payload = response.json()
    assert payload["current_version"]
    assert payload["organization"] == "天然气中心"
    assert payload["project_lead"] == "杨敏"
    assert payload["repository"] == "AlexYuhuFeng/Commodity-Lab"


def test_windows_installer_metadata_matches_release_requirements() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config = json.loads((repo_root / "tauri" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    bundle = config["tauri"]["bundle"]
    nsis_template = repo_root / "tauri" / "src-tauri" / bundle["windows"]["nsis"]["template"]
    template_text = nsis_template.read_text(encoding="utf-8")

    assert bundle["publisher"] == "天然气中心"
    assert bundle["targets"] == ["nsis", "msi"]
    assert bundle["windows"]["wix"]["language"] == "zh-CN"
    assert bundle["windows"]["nsis"]["installerIcon"] == "icons/icon.ico"
    assert "https://github.com/AlexYuhuFeng/Commodity-Lab" in template_text
    assert "🎵疯狂疯狂星期四，原味鸡两块九块九🎵" in template_text


def test_scenarios_endpoint_returns_natural_gas_only() -> None:
    response = client.get("/api/v1/scenarios", params={"locale": "en"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["categories"][0]["id"] == "natural_gas"
    assert payload["scenarios"]
    assert {scenario["commodity"] for scenario in payload["scenarios"]} == {"natural_gas"}
    assert {scenario["region"] for scenario in payload["scenarios"]} == {"europe"}


def test_business_templates_endpoint_returns_procurement_and_sales_workflows() -> None:
    response = client.get("/api/v1/business-templates", params={"locale": "en"})
    assert response.status_code == 200
    payload = response.json()
    assert {group["id"] for group in payload["groups"]} >= {"crude", "procurement", "sales"}
    assert {template["group"] for template in payload["templates"]} >= {"crude", "procurement", "sales"}
    assert any("beach" in template["business_type"].lower() for template in payload["templates"])
    assert any("LNG" in template["business_type"] for template in payload["templates"])
    assert any(template["id"] == "crude_oil_hedging_basics" for template in payload["templates"])


def test_provider_settings_endpoint_accepts_user_key_without_echoing_secret(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    response = client.post(
        "/api/v1/provider-settings",
        json={
            "api_key": "user-secret-key",
            "provider": "haineng",
            "base_url": "http://localhost:9999/v1",
            "model": "V4-Flash",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["haineng"]["ok"] is True
    assert payload["haineng"]["provider"] == "haineng"
    assert payload["haineng"]["base_url"] == "http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1"
    assert payload["haineng"]["model"] == "DeepSeek-V4-Flash"
    assert "user-secret-key" not in str(payload)
    _clear_haineng_env(monkeypatch)


def test_provider_settings_persists_to_local_user_config(monkeypatch, tmp_path) -> None:
    from core.haineng_client import HainengClient, set_runtime_settings

    set_runtime_settings(None)
    monkeypatch.delenv("COMMODITY_LAB_DISABLE_LOCAL_AI_SETTINGS", raising=False)
    monkeypatch.setenv("COMMODITY_LAB_AI_SETTINGS_FILE", str(tmp_path / "AI密钥.json"))
    response = client.post(
        "/api/v1/provider-settings",
        json={"api_key": "persisted-secret-key", "provider": "deepseek"},
    )
    assert response.status_code == 200
    assert "persisted-secret-key" not in str(response.json())

    set_runtime_settings(None)
    status = HainengClient().health_check()

    assert status["ok"] is True
    assert status["provider"] == "deepseek"
    assert status["resolved_model"] == "deepseek-v4-flash"
    assert "persisted-secret-key" not in str(status)
    _clear_haineng_env(monkeypatch)


def test_provider_settings_endpoint_forces_haineng_flash_contract(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    response = client.post(
        "/api/v1/provider-settings",
        json={"api_key": "user-secret-key", "provider": "haineng", "base_url": "", "model": "V4-Pro"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["haineng"]["provider"] == "haineng"
    assert payload["haineng"]["base_url"] == "http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1"
    assert payload["haineng"]["resolved_model"] == "DeepSeek-V4-Flash"
    assert "user-secret-key" not in str(payload)
    _clear_haineng_env(monkeypatch)


def test_provider_settings_endpoint_accepts_deepseek_contract(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    response = client.post(
        "/api/v1/provider-settings",
        json={
            "api_key": "user-secret-key",
            "provider": "deepseek",
            "base_url": "",
            "model": "deepseek-v4-pro",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["haineng"]["provider"] == "deepseek"
    assert payload["haineng"]["base_url"] == "https://api.deepseek.com"
    assert payload["haineng"]["resolved_model"] == "deepseek-v4-flash"
    assert "user-secret-key" not in str(payload)
    _clear_haineng_env(monkeypatch)


def test_context_endpoint_returns_market_and_capacity() -> None:
    response = client.get(
        "/api/v1/scenarios/europe_route_capacity_constraint/context",
        params={"locale": "en", "source": "ai_generated_training"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"]["id"] == "europe_route_capacity_constraint"
    assert payload["market"]["scenario_id"] == "europe_route_capacity_constraint"
    assert payload["market"]["source"] == "ai_generated_training"
    assert payload["market"]["data_source"] == "ai_generated_training"
    assert payload["market"]["symbol"] == "NG=F"
    assert payload["capacity"]["congestion_status"] == "constrained"


def test_context_endpoint_ignores_removed_external_source_names() -> None:
    response = client.get(
        "/api/v1/scenarios/europe_route_capacity_constraint/context",
        params={"locale": "en", "source": "removed_external_provider"},
    )
    assert response.status_code == 200
    market = response.json()["market"]
    assert market["source"] == "ai_generated_training"
    assert market["data_source"] == "ai_generated_training"
    assert market["metadata"]["requested_source"] == "ai_generated_training"
    assert market["metadata"]["is_fallback"] is False


def test_evaluate_endpoint_returns_deterministic_result() -> None:
    response = client.post(
        "/api/v1/attempts/evaluate",
        json={
            "scenario_id": "europe_route_capacity_constraint",
            "locale": "en",
            "order": {"side": "sell", "quantity": 60000, "hedge_type": "basis_hedge"},
            "rationale": "Sell a basis hedge to protect delivered European gas margin when capacity is tight.",
        },
    )
    assert response.status_code == 200
    evaluation = response.json()["evaluation"]
    assert evaluation["valid"] is True
    assert evaluation["baseline_score"] >= 80
    assert evaluation["score_inputs"]["actual_side"] == "sell"


def test_ai_generate_requires_provider_when_missing(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    response = client.post(
        "/api/v1/ai/generate",
        json={"capability": "case_generation", "scenario_id": "europe_ttf_nbp_spread", "locale": "en"},
    )
    assert response.status_code == 428
    assert "AI provider is required" in response.json()["detail"]


def test_compat_advisor_and_exam_require_provider_when_missing(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    advisor_response = client.post(
        "/api/v1/advisor/review",
        json={
            "scenario_id": "europe_ttf_nbp_spread",
            "locale": "en",
            "order": {"side": "sell", "quantity": 70000, "hedge_type": "basis_hedge"},
            "rationale": "Sell a basis hedge to manage TTF/NBP spread risk.",
            "evaluation": {"valid": True, "baseline_score": 95},
        },
    )
    exam_response = client.post(
        "/api/v1/exam/generate",
        json={"scenario_id": "europe_ttf_nbp_spread", "locale": "en", "attempt_history": [{"baseline_score": 95}]},
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
    base_payload = {"scenario_id": "europe_ttf_nbp_spread", "locale": "en", "source": "ai_generated_training"}
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


def test_ai_training_case_endpoint_parses_generated_json(monkeypatch) -> None:
    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            text = "\n".join(message["content"] for message in messages)
            assert "Business template" in text
            assert "AI-generated training data" in text
            return """
            {
              "scenario": {
                "id": "ai-case",
                "title": "Generated gas case",
                "summary": "Generated case summary",
                "business_type": "Upstream beach delivery GSA",
                "knowledge_points": ["basis_spread"],
                "exposure": {"direction": "spread", "volume_mmbtu": 60000, "risk": "basis and FX"}
              },
              "market": {
                "unit": "training index",
                "curves": [
                  {"id": "TTF", "label": "TTF", "color": "#38bdf8", "points": [{"date": "2026-01-01", "open": 1, "high": 2, "low": 1, "close": 1.5}]},
                  {"id": "NBP", "label": "NBP", "color": "#f59e0b", "points": [{"date": "2026-01-01", "open": 3, "high": 4, "low": 3, "close": 3.5}]}
                ],
                "events": []
              },
              "target_actions": [{"leg_type": "basis", "market": "TTF/NBP", "side": "sell", "quantity": 60000, "tenor": "M+1", "rationale": "Lock spread"}],
              "rubric": [{"id": "basis", "label": "Basis", "points": 40, "rule": "Use basis hedge"}],
              "prompt": "### Decision task"
            }
            """

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/training-case",
        json={"template_id": "procurement_beach_to_germany", "locale": "en", "user_request": "UK to Germany"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["template"]["id"] == "procurement_beach_to_germany"
    assert payload["case"]["scenario"]["title"] == "Generated gas case"
    assert [curve["id"] for curve in payload["case"]["market"]["curves"]] == ["TTF", "NBP"]


def test_ai_training_case_endpoint_repairs_common_llm_json_errors(monkeypatch) -> None:
    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            return """
            ```json
            {
              "scenario": {
                "id": "repair-case",
                "title": "Repaired gas case",
                "summary": "Generated case summary",
                "business_type": "Natural Gas Hedging Foundations",
                "knowledge_points": ["physical_paper_matching"],
                "exposure": {"direction": "long", "volume_mmbtu": 60000, "risk": "flat price"}
              }
              "market": {
                "unit": "training index",
                "curves": [
                  {"id": "TTF", "label": "TTF", "points": [{"date": "2026-01-01", "open": 1, "high": 2, "low": 1, "close": 1.5}],}
                ],
                "events": [],
              },
              "target_actions": [{"leg_type": "swap", "market": "TTF", "side": "sell", "quantity": 60000, "tenor": "M+1"}],
              "rubric": [{"id": "paper", "label": "Paper", "points": 40, "rule": "Use swap"}],
              "prompt": "### Decision task",
            }
            ```
            """

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/training-case",
        json={"template_id": "foundation_hedging_basics", "locale": "en", "user_request": "starter"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case"]["scenario"]["title"] == "Repaired gas case"
    assert payload["case"]["market"]["curves"][0]["id"] == "TTF"


def test_ai_training_case_endpoint_hides_raw_json_parse_errors(monkeypatch) -> None:
    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            return '{"scenario": {"title": "Broken case"} "market": {}'

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/training-case",
        json={"template_id": "foundation_hedging_basics", "locale": "en", "user_request": "starter"},
    )

    assert response.status_code == 502
    payload = response.json()
    assert payload["detail"]["code"] == "ai_response_parse_failed"
    assert "Expecting" not in str(payload)
    assert "delimiter" not in str(payload)


def test_live_assistant_endpoint_returns_safe_action_cards(monkeypatch) -> None:
    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            text = "\n".join(message["content"] for message in messages)
            assert "Allowed action types" in text
            assert "track_id=foundation" in text
            return """
            {
              "answer": "### Plan\\nShow high/low/close and add an FX leg.",
              "actions": [
                {"type": "set_chart_fields", "label": "Show high/low/close", "payload": {"fields": ["high", "low", "close"]}},
                {"type": "run_ai_capability", "label": "Explain basis", "payload": {"capability": "concept_tutor"}}
              ]
            }
            """

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/live-assistant",
        json={"locale": "en", "message": "Show more chart detail", "workspace_state": {"case": {"scenario": {"title": "x"}}}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].startswith("### Plan")
    assert [action["type"] for action in payload["actions"]] == ["set_chart_fields", "run_ai_capability"]


def test_compat_advisor_and_exam_return_haineng_answers_when_configured(monkeypatch) -> None:
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
            "scenario_id": "europe_ttf_nbp_spread",
            "locale": "en",
            "order": {"side": "sell", "quantity": 70000, "hedge_type": "basis_hedge"},
            "rationale": "Sell a basis hedge to manage TTF/NBP spread risk.",
            "evaluation": {"valid": True, "baseline_score": 95},
        },
    )
    exam_response = client.post(
        "/api/v1/exam/generate",
        json={"scenario_id": "europe_ttf_nbp_spread", "locale": "en", "attempt_history": [{"baseline_score": 95}]},
    )
    assert advisor_response.status_code == 200
    assert advisor_response.json()["answer"] == "provider answer"
    assert exam_response.status_code == 200
    assert exam_response.json()["exam"] == "provider answer"


def test_compat_assistant_uses_haineng_contract(monkeypatch) -> None:
    _clear_haineng_env(monkeypatch)
    missing = client.post("/api/assistant", json={"question": "How should I hedge TTF/NBP basis?"})
    assert missing.status_code == 428

    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            text = "\n".join(message["content"] for message in messages)
            assert "TTF/NBP" in text
            assert "Haineng" in text
            return "compatibility provider answer"

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post("/api/assistant", json={"question": "How should I hedge TTF/NBP basis?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "compatibility provider answer"


def test_haineng_provider_failure_returns_structured_502(monkeypatch) -> None:
    class FailingClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            raise RuntimeError("provider rejected token=secret-key; Your api key: ****96a2 is invalid; raw sk-abcdef1234567890")

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FailingClient())
    response = client.post(
        "/api/v1/ai/generate",
        json={"capability": "case_generation", "scenario_id": "europe_ttf_nbp_spread", "locale": "en"},
    )
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == "ai_provider_request_failed"
    assert "secret-key" not in str(detail)
    assert "96a2" not in str(detail)
    assert "sk-abcdef1234567890" not in str(detail)
    assert "token=[REDACTED]" in detail["provider_message"]
    assert "api key=[REDACTED]" in detail["provider_message"]


def test_unknown_scenario_returns_404() -> None:
    response = client.get("/api/v1/scenarios/not-a-scenario/context")
    assert response.status_code == 404
    assert "Unknown scenario" in response.json()["detail"]
