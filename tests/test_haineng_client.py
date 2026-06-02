from __future__ import annotations

import pytest

from core.haineng_client import (
    HainengClient,
    HainengSettings,
    build_advisor_messages,
    build_exam_messages,
    build_haineng_tools,
    redact_settings,
    settings_from_env,
)


def test_redact_settings_never_returns_api_key() -> None:
    settings = HainengSettings(
        api_key="secret-key",
        base_url="http://model.ai.cnooc/member1/deepseek-v4-pro-1-5t/v1",
        model="DeepSeek-V4",
    )
    redacted = redact_settings(settings)
    assert redacted["configured"] is True
    assert "secret-key" not in str(redacted)


def test_advisor_messages_include_locale_and_not_key() -> None:
    settings = HainengSettings(api_key="secret-key", base_url="http://local/v1")
    messages = build_advisor_messages(
        locale="zh",
        scenario={"id": "producer_short_hedge", "title": "生产商卖出套保"},
        evaluation={"baseline_score": 82, "mistake_tags": []},
        user_rationale="卖出期货保护价格下跌风险",
    )
    text = str(messages)
    assert "Respond in Mandarin Chinese" in text
    assert "海能" in text
    assert settings.api_key not in text


def test_exam_messages_request_three_to_five_questions() -> None:
    messages = build_exam_messages(
        locale="en",
        scenario={"id": "pipeline_capacity_constraint", "title": "Pipeline Capacity Constraint"},
        attempt_history=[{"baseline_score": 62, "mistake_tags": ["ignores_capacity"]}],
    )
    text = str(messages)
    assert "3 to 5" in text
    assert "pipeline_capacity_constraint" in text


def test_function_tools_have_required_shape() -> None:
    tools = build_haineng_tools()
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "get_attempt_metrics"
    assert "parameters" in tools[0]["function"]


def test_settings_from_env_parses_booleans(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HAINENG_API_KEY", "secret-key")
    monkeypatch.setenv("HAINENG_BASE_URL", "http://local/v1")
    monkeypatch.setenv("HAINENG_MODEL", "DeepSeek-V4-Flash")
    monkeypatch.setenv("HAINENG_STREAMING", "true")
    monkeypatch.setenv("HAINENG_FUNCTION_CALLING", "0")

    settings = settings_from_env()

    assert settings.api_key == "secret-key"
    assert settings.base_url == "http://local/v1"
    assert settings.model == "DeepSeek-V4-Flash"
    assert settings.streaming is True
    assert settings.function_calling is False


def test_unconfigured_complete_raises() -> None:
    client = HainengClient(HainengSettings())

    with pytest.raises(RuntimeError, match="海能 is not configured."):
        client.complete([{"role": "user", "content": "hello"}])


def test_health_check_reports_configuration_only() -> None:
    missing = HainengClient(HainengSettings()).health_check()
    configured = HainengClient(
        HainengSettings(api_key="secret-key", base_url="http://local/v1")
    ).health_check()

    assert missing["ok"] is False
    assert missing["reason"] == "missing_haineng_settings"
    assert configured["ok"] is True
    assert configured["configured"] is True
    assert "secret-key" not in str(missing)
    assert "secret-key" not in str(configured)


def test_prompt_scrubbing_redacts_settings_objects() -> None:
    settings = HainengSettings(api_key="secret-key", base_url="http://local/v1")

    advisor_messages = build_advisor_messages(
        locale="en",
        scenario={"id": "producer_short_hedge", "settings": settings},
        evaluation={"baseline_score": 90},
        user_rationale="I sell futures.",
    )
    exam_messages = build_exam_messages(
        locale="en",
        scenario={"id": "pipeline_capacity_constraint"},
        attempt_history=[{"settings": settings}],
    )

    assert "secret-key" not in str(advisor_messages)
    assert "secret-key" not in str(exam_messages)
    assert "[REDACTED]" in str(advisor_messages)
    assert "[REDACTED]" in str(exam_messages)
