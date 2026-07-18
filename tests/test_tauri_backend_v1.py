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
            assert "contango" in text
            assert "ai_simulated" in text
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
        json={
            "template_id": "procurement_beach_to_germany",
            "locale": "en",
            "user_request": "UK to Germany",
            "market_mode": "ai_simulated",
            "market_regime": "contango",
            "market_seed": 7,
            "market_as_of": "2026-07-17",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["template"]["id"] == "procurement_beach_to_germany"
    assert payload["case"]["scenario"]["title"] == "Generated gas case"
    assert [curve["id"] for curve in payload["case"]["market"]["curves"]] == ["TTF", "NBP"]
    assert payload["case"]["market"]["curve_metrics"]["structure"] == "contango"
    assert payload["case"]["market"]["provenance"]["mode"] == "ai_simulated"


def test_general_course_uses_the_selected_product_market() -> None:
    from core.training_templates import get_template
    from tauri.backend.main import TrainingCaseGenerateRequest, _resolve_training_market

    payload = TrainingCaseGenerateRequest(
        template_id="foundation_hedging_basics",
        product_scope="crude_oil",
        locale="en",
        market_mode="ai_simulated",
    )
    market = _resolve_training_market(payload, get_template("foundation_hedging_basics", "en"))

    assert market["commodity"] == "crude_oil"
    assert market["benchmark"] == "Brent"


def test_live_training_market_uses_entitled_adapter_when_available(monkeypatch) -> None:
    from core.training_templates import get_template
    from tauri.backend.main import TrainingCaseGenerateRequest, _resolve_training_market

    entitled = {
        "commodity": "natural_gas",
        "benchmark": "TTF",
        "unit": "EUR/MWh",
        "as_of": "2026-07-17",
        "forward_curve": [{"tenor": "M+1", "price": 31.0}, {"tenor": "M+2", "price": 32.0}],
        "history": [],
        "curve_metrics": {"structure": "contango"},
        "provenance": {"mode": "live", "is_live": True, "source": "Platts"},
    }
    monkeypatch.setattr(
        "core.platts_market.PlattsMarketClient.fetch_market_context",
        lambda self, commodity, locale="en": entitled,
    )
    payload = TrainingCaseGenerateRequest(
        template_id="foundation_hedging_basics",
        product_scope="natural_gas",
        locale="en",
        market_mode="live",
    )

    market = _resolve_training_market(payload, get_template("foundation_hedging_basics", "en"))

    assert market is entitled
    assert market["provenance"]["is_live"] is True


def test_live_training_market_fallback_is_explicit(monkeypatch) -> None:
    from core.platts_market import PlattsConfigurationError
    from core.training_templates import get_template
    from tauri.backend.main import TrainingCaseGenerateRequest, _resolve_training_market

    def unavailable(self, commodity, locale="en"):
        raise PlattsConfigurationError("missing", code="platts_symbol_map_missing")

    monkeypatch.setattr("core.platts_market.PlattsMarketClient.fetch_market_context", unavailable)
    payload = TrainingCaseGenerateRequest(
        template_id="foundation_hedging_basics",
        product_scope="natural_gas",
        locale="en",
        market_mode="live",
    )

    market = _resolve_training_market(payload, get_template("foundation_hedging_basics", "en"))

    assert market["provenance"]["mode"] == "ai_simulated"
    assert market["provenance"]["fallback_reason"] == "platts_symbol_map_missing"
    assert market["provenance"]["quality"] == "explicit_simulation_fallback"


def test_ai_training_case_stream_emits_market_before_real_model_deltas(monkeypatch) -> None:
    captured_prompt: list[str] = []
    answer = """{
      "scenario": {
        "id": "stream-case",
        "title": "Streaming procurement hedge",
        "summary": "A compact streamed training case.",
        "business_type": "Gas procurement",
        "knowledge_points": ["exposure_objective"],
        "exposure": {"direction": "long", "volume_mmbtu": 1000, "risk": "TTF price"}
      },
      "market": {"curves": [], "events": [], "markers": []},
      "target_actions": [{"leg_type": "swap", "market": "TTF", "side": "buy", "quantity": 1000, "tenor": "M+1"}],
      "rubric": [{"id": "direction", "label": "Direction", "points": 100, "rule": "Buy TTF"}],
      "prompt": "### Decision task"
    }"""

    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def stream_complete(self, messages, tools=None):
            captured_prompt.append("\n".join(message["content"] for message in messages))
            midpoint = len(answer) // 2
            yield answer[:midpoint]
            yield answer[midpoint:]

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/training-case/stream",
        json={
            "template_id": "foundation_hedging_basics",
            "locale": "en",
            "user_request": "Build a first lesson",
            "market_mode": "ai_simulated",
            "market_regime": "backwardation",
            "knowledge_coverage": [{"id": f"item-{index}", "title": "x"} for index in range(20)],
            "gas_trading_models": [{"id": f"model-{index}", "title": "x"} for index in range(20)],
        },
    )

    assert response.status_code == 200
    body = response.text
    assert body.index("event: market") < body.index("event: model_delta")
    assert body.count("event: model_delta") == 2
    assert "event: case" in body
    assert '"received"' in body
    assert len(captured_prompt) == 1
    assert "item-7" in captured_prompt[0]
    assert "item-8" not in captured_prompt[0]
    assert "model-5" in captured_prompt[0]
    assert "model-6" not in captured_prompt[0]


def test_ai_training_case_recovers_positive_crude_volume_from_target_legs(monkeypatch) -> None:
    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            return """{
              "scenario": {
                "id": "crude-volume-case",
                "title": "Brent procurement hedge",
                "summary": "A 100,000 bbl procurement case.",
                "business_type": "Crude procurement",
                "knowledge_points": ["crude_benchmark_basis"],
                "exposure": {"direction": "long", "volume_mmbtu": 580000, "volume_unit": "bbl", "risk": "flat price decline and Brent basis"}
              },
              "market": {"unit": "USD/bbl", "curves": [{"id": "WTI", "label": "WTI", "points": [{"date": "2027-03-01", "close": 80}]}], "events": []},
              "target_actions": [
                {"leg_type": "physical", "market": "Brent cargo", "side": "buy", "quantity": 580000, "tenor": "M+3"},
                {"leg_type": "future", "market": "ICE Brent", "side": "sell", "quantity": 580000, "tenor": "M+3"}
              ],
              "rubric": [{"id": "direction", "label": "Direction", "points": 100, "rule": "Buy Brent"}],
              "prompt": "\u5bf910\u4e07\u6876 Brent \u91c7\u8d2d\u505a\u5957\u4fdd\uff0c\u5b9e\u8d27\u4e0e\u7eb8\u8d27\u6570\u91cf\u4e25\u683c\u5339\u914d\u3002"
            }"""

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/training-case",
        json={"template_id": "crude_oil_hedging_basics", "locale": "zh", "user_request": "\u5bf910\u4e07\u6876 Brent \u91c7\u8d2d\u505a\u5957\u4fdd"},
    )

    assert response.status_code == 200
    generated = response.json()["case"]
    assert generated["scenario"]["exposure"]["volume_mmbtu"] == 100000
    assert generated["scenario"]["exposure"]["volume_unit"] == "bbl"
    assert "price increase" in generated["scenario"]["exposure"]["risk"]
    assert generated["target_actions"][0]["quantity"] == 100000
    assert generated["target_actions"][1]["quantity"] == 100000
    assert generated["target_actions"][1]["side"] == "buy"
    assert max(point["date"] for point in generated["market"]["curves"][1]["points"]) <= generated["market"]["as_of"]


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


def test_historical_replay_training_case_hides_model_actions_until_submission(monkeypatch) -> None:
    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def complete(self, messages, tools=None):
            return """
            {
              "scenario": {
                "id": "replay-case",
                "title": "Hormuz replay",
                "summary": "Point-in-time crude procurement replay",
                "business_type": "Crude procurement / sales hedging",
                "knowledge_points": ["crude_benchmark_basis"],
                "exposure": {"direction": "long", "volume_mmbtu": 100000, "risk": "price and freight"}
              },
              "market": {
                "unit": "USD/bbl",
                "curves": [{"id": "WTI", "label": "WTI", "points": [{"date": "2026-12-01", "close": 88.0}]}],
                "events": []
              },
              "target_actions": [{"leg_type": "future", "market": "ICE Brent", "side": "buy", "quantity": 70000, "tenor": "M+2"}],
              "rubric": [{"id": "paper", "label": "Paper", "points": 100, "rule": "Buy Brent"}],
              "prompt": "The model answer is to buy Brent."
            }
            """

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/training-case",
        json={
            "template_id": "crude_oil_hedging_basics",
            "locale": "en",
            "market_mode": "historical_replay",
            "replay_id": "hormuz_2026_disruption",
        },
    )

    assert response.status_code == 200
    case = response.json()["case"]
    assert case["target_actions"] == []
    assert sum(item["points"] for item in case["rubric"]) == 100
    assert case["market"]["replay"]["current_checkpoint"]["index"] == 0
    assert case["market"]["replay"]["next_checkpoint"] == 1
    assert case["scenario"]["title"] == "2026 Strait of Hormuz supply-shock replay"
    assert case["scenario"]["exposure"]["direction"] == "long"
    assert case["scenario"]["exposure"]["unit"] == "bbl"
    assert [curve["id"] for curve in case["market"]["curves"]] == ["Brent"]
    assert max(point["date"] for point in case["market"]["curves"][0]["points"]) <= "2026-04-01"
    assert "buy Brent" not in case["prompt"]


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


def test_live_assistant_stream_compacts_context_and_emits_actions(monkeypatch) -> None:
    captured_prompt: list[str] = []
    answer = json.dumps(
        {
            "answer": "Buy TTF paper against the future procurement exposure.",
            "actions": [
                {
                    "type": "set_strategy_legs",
                    "label": "Fill the hedge",
                    "payload": {
                        "legs": [
                            {"leg_type": "swap", "market": "TTF Q4", "side": "buy", "quantity": 70000, "tenor": "Q4"}
                        ]
                    },
                }
            ],
        }
    )

    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def stream_complete(self, messages, tools=None):
            captured_prompt.append("\n".join(message["content"] for message in messages))
            midpoint = len(answer) // 2
            yield answer[:midpoint]
            yield answer[midpoint:]

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/live-assistant/stream",
        json={
            "locale": "en",
            "message": "Fill the strategy for this procurement obligation.",
            "workspace_state": {
                "active_page": "workbench",
                "product_scope": "natural_gas",
                "case": {
                    "scenario": {"title": "Winter delivery", "exposure": {"direction": "long", "risk": "TTF upside"}},
                    "prompt": "Cover a future fixed-price customer delivery obligation.",
                    "market": {
                        "benchmark": "TTF",
                        "source_notes": [{"symbol": "raw-source-secret"}],
                        "curves": [
                            {
                                "id": "TTF",
                                "points": [{"date": f"2022-01-{day:02d}", "close": day} for day in range(1, 21)],
                            }
                        ],
                    },
                },
                "strategy_legs": [],
            },
        },
    )

    assert response.status_code == 200
    body = response.text
    assert body.count("event: model_delta") == 2
    assert body.index("event: stage") < body.index("event: model_delta") < body.index("event: result")
    assert '"set_strategy_legs"' in body
    assert captured_prompt
    assert "Do not pair a physical purchase with a paper sale" in captured_prompt[0]
    assert "raw-source-secret" not in captured_prompt[0]
    assert "2022-01-01" not in captured_prompt[0]
    assert "2022-01-20" in captured_prompt[0]


def test_streamed_advisor_uses_the_active_replay_instead_of_the_registry_default(monkeypatch) -> None:
    captured_prompt: list[str] = []

    class FakeClient:
        def is_configured(self) -> bool:
            return True

        def stream_complete(self, messages, tools=None):
            captured_prompt.append("\n".join(message["content"] for message in messages))
            yield "## Verdict\n- Keep the procurement hedge aligned with Q4 delivery."

    monkeypatch.setattr("core.haineng_client.HainengClient", lambda: FakeClient())
    response = client.post(
        "/api/v1/ai/advisor-review/stream",
        json={
            "capability": "advisor_review",
            "scenario_id": "europe_ttf_nbp_spread",
            "locale": "en",
            "rationale": "Buy TTF paper and reserve regas capacity.",
            "evaluation": {"baseline_score": 78, "mistake_tags": ["missing_execution_controls"]},
            "market_context": {
                "case": {
                    "scenario": {
                        "title": "2022 European gas crisis replay",
                        "summary": "A winter procurement obligation during pipeline supply cuts.",
                        "exposure": {"direction": "long", "risk": "TTF procurement cost upside"},
                    },
                    "market": {
                        "benchmark": "TTF",
                        "as_of": "2022-06-14",
                        "source_symbol": "licensed-secret-symbol",
                        "replay": {"current_checkpoint": {"label": "Supply tightening", "decision_required": "Cover Q4 procurement."}},
                    },
                },
                "strategy_legs": [{"leg_type": "future", "market": "TTF Q4", "side": "buy", "quantity": 70000}],
            },
        },
    )

    assert response.status_code == 200
    assert "event: review" in response.text
    assert captured_prompt
    assert "2022 European gas crisis replay" in captured_prompt[0]
    assert "TTF Q4" in captured_prompt[0]
    assert "licensed-secret-symbol" not in captured_prompt[0]


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
