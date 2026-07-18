from __future__ import annotations

import json
import os
import sys
import types

import pytest

from core.haineng_client import (
    HainengClient,
    HainengSettings,
    build_advisor_messages,
    build_exam_messages,
    build_haineng_tools,
    build_training_case_messages,
    effective_settings,
    load_persisted_settings,
    save_persisted_settings,
    redact_settings,
    settings_from_env,
    set_runtime_settings,
)


def test_redact_settings_never_returns_api_key() -> None:
    settings = HainengSettings(
        api_key="secret-key",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-flash",
        provider="deepseek",
    )
    redacted = redact_settings(settings)
    assert redacted["configured"] is True
    assert redacted["provider"] == "deepseek"
    assert redacted["resolved_model"] == "deepseek-v4-flash"
    assert "secret-key" not in str(redacted)


def test_advisor_messages_include_locale_and_not_key() -> None:
    settings = HainengSettings(api_key="secret-key", base_url="http://local/v1")
    messages = build_advisor_messages(
        locale="zh",
        scenario={"id": "europe_ttf_nbp_spread", "title": "欧洲 TTF/NBP 价差"},
        evaluation={"baseline_score": 82, "mistake_tags": []},
        user_rationale="卖出基差套保管理 TTF/NBP 价差风险",
    )
    text = str(messages)
    assert "Respond in Mandarin Chinese" in text
    assert "海能" in text
    assert settings.api_key not in text


def test_exam_messages_request_three_to_five_questions() -> None:
    messages = build_exam_messages(
        locale="en",
        scenario={"id": "europe_route_capacity_constraint", "title": "Europe Route Capacity Constraint"},
        attempt_history=[{"baseline_score": 62, "mistake_tags": ["ignores_capacity"]}],
    )
    text = str(messages)
    assert "3 to 5" in text
    assert "single-choice assessment" in text
    assert "correct_index" in text
    assert "Return only compact strict JSON" in text
    assert "Haineng" in text
    assert "europe_route_capacity_constraint" in text


def test_function_tools_have_required_shape() -> None:
    tools = build_haineng_tools()
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "get_attempt_metrics"
    assert "parameters" in tools[0]["function"]


def test_settings_from_env_parses_booleans(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HAINENG_API_KEY", "secret-key")
    monkeypatch.setenv("HAINENG_BASE_URL", "http://local/v1")
    monkeypatch.setenv("HAINENG_MODEL", "V4-Flash")
    monkeypatch.setenv("HAINENG_STREAMING", "true")
    monkeypatch.setenv("HAINENG_FUNCTION_CALLING", "0")

    settings = settings_from_env()

    assert settings.api_key == "secret-key"
    assert settings.base_url == ""
    assert settings.model == "DeepSeek-V4-Flash"
    assert settings.streaming is True
    assert settings.function_calling is False


def test_persisted_settings_survive_runtime_reset(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    config_file = tmp_path / "AI密钥.json"
    monkeypatch.setenv("COMMODITY_LAB_AI_SETTINGS_FILE", str(config_file))
    monkeypatch.delenv("COMMODITY_LAB_DISABLE_LOCAL_AI_SETTINGS", raising=False)
    set_runtime_settings(None)

    save_persisted_settings(
        HainengSettings(api_key="saved-secret-key", provider="deepseek", model="deepseek-v4-flash")
    )
    set_runtime_settings(None)

    persisted = load_persisted_settings()
    effective = effective_settings()

    assert persisted is not None
    assert persisted.api_key == "saved-secret-key"
    assert persisted.provider == "deepseek"
    assert effective.api_key == "saved-secret-key"
    assert redact_settings(effective)["configured"] is True
    assert "saved-secret-key" not in str(redact_settings(effective))
    raw_payload = json.loads(config_file.read_text(encoding="utf-8"))
    assert raw_payload["version"] == 2
    assert "api_key" not in raw_payload
    if os.name == "nt":
        assert raw_payload["credential"]["scheme"] == "windows_dpapi"
        assert "saved-secret-key" not in config_file.read_text(encoding="utf-8")
    else:
        assert raw_payload["credential"]["scheme"] == "restricted_file"
        assert config_file.stat().st_mode & 0o077 == 0
    set_runtime_settings(None)


def test_legacy_plaintext_settings_are_read_and_migrated_on_windows(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    config_file = tmp_path / "AI密钥.json"
    config_file.write_text(json.dumps({"provider": "deepseek", "api_key": "legacy-secret-key"}), encoding="utf-8")
    monkeypatch.setenv("COMMODITY_LAB_AI_SETTINGS_FILE", str(config_file))
    monkeypatch.delenv("COMMODITY_LAB_DISABLE_LOCAL_AI_SETTINGS", raising=False)

    persisted = load_persisted_settings()

    assert persisted is not None
    assert persisted.api_key == "legacy-secret-key"
    if os.name == "nt":
        raw_text = config_file.read_text(encoding="utf-8")
        assert "legacy-secret-key" not in raw_text
        assert json.loads(raw_text)["credential"]["scheme"] == "windows_dpapi"


def test_unconfigured_complete_raises() -> None:
    client = HainengClient(HainengSettings())

    with pytest.raises(RuntimeError, match="AI provider is not configured."):
        client.complete([{"role": "user", "content": "hello"}])


def test_health_check_reports_configuration_only() -> None:
    missing = HainengClient(HainengSettings()).health_check()
    configured = HainengClient(
        HainengSettings(api_key="secret-key", base_url="http://local/v1")
    ).health_check()

    assert missing["ok"] is False
    assert missing["reason"] == "missing_ai_provider_settings"
    assert configured["ok"] is True
    assert configured["configured"] is True
    assert "resolved_model" in configured
    assert "secret-key" not in str(missing)
    assert "secret-key" not in str(configured)


def test_prompt_scrubbing_redacts_settings_objects() -> None:
    settings = HainengSettings(api_key="secret-key", base_url="http://local/v1")

    advisor_messages = build_advisor_messages(
        locale="en",
        scenario={"id": "europe_ttf_nbp_spread", "settings": settings},
        evaluation={"baseline_score": 90},
        user_rationale="I pasted token=secret-key into the rationale.",
    )
    exam_messages = build_exam_messages(
        locale="en",
        scenario={"id": "europe_route_capacity_constraint"},
        attempt_history=[{"settings": settings}],
    )

    assert "secret-key" not in str(advisor_messages)
    assert "secret-key" not in str(exam_messages)
    assert "http://local/v1" not in str(advisor_messages)
    assert "http://local/v1" not in str(exam_messages)
    assert "[REDACTED]" in str(advisor_messages)
    assert "[REDACTED]" in str(exam_messages)


def test_complete_raises_when_model_requests_tool_call(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_payload: dict[str, object] = {}

    class Message:
        content = ""
        tool_calls = [{"id": "call_1"}]

    class Choice:
        message = Message()

    class Response:
        choices = [Choice()]

    class Completions:
        def create(self, **payload):
            captured_payload.update(payload)
            return Response()

    class Chat:
        completions = Completions()

    class FakeOpenAI:
        def __init__(self, api_key: str, base_url: str) -> None:
            assert api_key == "secret-key"
            assert base_url == "http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1"
            self.chat = Chat()

    fake_openai = types.SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    client = HainengClient(
        HainengSettings(api_key="secret-key", base_url="http://local/v1")
    )

    with pytest.raises(RuntimeError, match="tool call"):
        client.complete(
            [{"role": "user", "content": "review"}],
            tools=build_haineng_tools(),
        )

    assert captured_payload["model"] == "DeepSeek-V4-Flash"
    assert captured_payload["stream"] is False
    assert captured_payload["max_tokens"] == 4096
    assert captured_payload["extra_body"] == {"enable_thinking": False}
    assert captured_payload["tool_choice"] == "auto"


def test_haineng_provider_forces_current_v4_flash_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_payload: dict[str, object] = {}

    class Message:
        content = "ok"
        tool_calls = None

    class Choice:
        message = Message()

    class Response:
        choices = [Choice()]

    class Completions:
        def create(self, **payload):
            captured_payload.update(payload)
            return Response()

    class Chat:
        completions = Completions()

    class FakeOpenAI:
        def __init__(self, api_key: str, base_url: str) -> None:
            assert api_key == "secret-key"
            assert base_url == "http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1"
            self.chat = Chat()

    fake_openai = types.SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    client = HainengClient(
        HainengSettings(api_key="secret-key", provider="haineng", model="V4-Pro")
    )

    assert client.complete([{"role": "user", "content": "review"}]) == "ok"
    assert captured_payload["model"] == "DeepSeek-V4-Flash"
    assert captured_payload["extra_body"] == {"enable_thinking": False}


def test_deepseek_provider_uses_public_v4_flash_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_payload: dict[str, object] = {}

    class Message:
        content = "ok"
        tool_calls = None

    class Choice:
        message = Message()

    class Response:
        choices = [Choice()]

    class Completions:
        def create(self, **payload):
            captured_payload.update(payload)
            return Response()

    class Chat:
        completions = Completions()

    class FakeOpenAI:
        def __init__(self, api_key: str, base_url: str) -> None:
            assert api_key == "secret-key"
            assert base_url == "https://api.deepseek.com"
            self.chat = Chat()

    fake_openai = types.SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    client = HainengClient(
        HainengSettings(api_key="secret-key", provider="deepseek", model="deepseek-v4-flash")
    )

    assert client.complete([{"role": "user", "content": "review"}]) == "ok"
    assert captured_payload["model"] == "deepseek-v4-flash"
    assert captured_payload["extra_body"] == {"thinking": {"type": "disabled"}}


def test_stream_complete_yields_provider_text_deltas(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_payload: dict[str, object] = {}

    class Delta:
        def __init__(self, content: str | None) -> None:
            self.content = content

    class Choice:
        def __init__(self, content: str | None) -> None:
            self.delta = Delta(content)

    class Chunk:
        def __init__(self, content: str | None) -> None:
            self.choices = [Choice(content)]

    class Completions:
        def create(self, **payload):
            captured_payload.update(payload)
            return iter([Chunk('{"scenario":'), Chunk(None), Chunk('{"title":"Live"}}')])

    class Chat:
        completions = Completions()

    class FakeOpenAI:
        def __init__(self, api_key: str, base_url: str) -> None:
            assert api_key == "secret-key"
            assert base_url == "https://api.deepseek.com"
            self.chat = Chat()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    client = HainengClient(HainengSettings(api_key="secret-key", provider="deepseek"))

    assert list(client.stream_complete([{"role": "user", "content": "build"}])) == [
        '{"scenario":',
        '{"title":"Live"}}',
    ]
    assert captured_payload["stream"] is True
    assert captured_payload["model"] == "deepseek-v4-flash"
    assert captured_payload["extra_body"] == {"thinking": {"type": "disabled"}}


def test_training_case_prompt_requests_compact_complete_json() -> None:
    messages = build_training_case_messages(
        locale="zh",
        template={"id": "foundation_hedging_basics", "title": "套保入门", "coverage": ["outright_price"]},
        user_request="生成第一课练习",
        market_context={
            "curve_metrics": {"structure": "contango"},
            "provenance": {"mode": "ai_simulated", "source_tier": "synthetic"},
        },
    )
    text = "\n".join(message["content"] for message in messages)

    assert "compact strict JSON" in text
    assert "exactly 4 rows" in text
    assert "Use exactly 8 price points per curve" in text
    assert "under 120 words" in text
    assert "contango" in text
    assert "ai_simulated" in text
    assert "preserve its provenance" in text
