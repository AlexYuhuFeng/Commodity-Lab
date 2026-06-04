from __future__ import annotations

import dataclasses
import json
import os
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class HainengSettings:
    api_key: str = ""
    base_url: str = ""
    model: str = "V4-Flash"
    streaming: bool = False
    function_calling: bool = True


_runtime_settings: HainengSettings | None = None


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if not normalized:
        return default
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def settings_from_env() -> HainengSettings:
    return HainengSettings(
        api_key=os.getenv("HAINENG_API_KEY", "").strip(),
        base_url=os.getenv("HAINENG_BASE_URL", "").strip(),
        model=os.getenv("HAINENG_MODEL", "V4-Flash").strip() or "V4-Flash",
        streaming=_env_bool("HAINENG_STREAMING", False),
        function_calling=_env_bool("HAINENG_FUNCTION_CALLING", True),
    )


def set_runtime_settings(settings: HainengSettings | None) -> None:
    global _runtime_settings
    _runtime_settings = settings


def effective_settings() -> HainengSettings:
    return _runtime_settings or settings_from_env()


def _is_configured(settings: HainengSettings) -> bool:
    return bool(settings.api_key.strip() and settings.base_url.strip())


def redact_settings(settings: HainengSettings) -> dict[str, Any]:
    return {
        "configured": _is_configured(settings),
        "base_url": settings.base_url,
        "model": settings.model,
        "streaming": settings.streaming,
        "function_calling": settings.function_calling,
    }


def build_haineng_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_attempt_metrics",
                "description": (
                    "Return deterministic metrics already computed by the app for "
                    "the learner's current natural gas hedging attempt."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scenario_id": {
                            "type": "string",
                            "description": "Scenario identifier for the current attempt.",
                        },
                        "include_history": {
                            "type": "boolean",
                            "description": "Whether to include recent attempt summaries.",
                        },
                    },
                    "required": ["scenario_id"],
                    "additionalProperties": False,
                },
            },
        }
    ]


def _scrub_sensitive(value: Any) -> Any:
    sensitive_terms = ("api_key", "apikey", "authorization", "password", "secret", "token")
    if isinstance(value, HainengSettings):
        return "[REDACTED]"
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = dataclasses.asdict(value)
    if isinstance(value, dict):
        scrubbed: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(term in key_text for term in sensitive_terms):
                scrubbed[str(key)] = "[REDACTED]"
            else:
                scrubbed[str(key)] = _scrub_sensitive(item)
        return scrubbed
    if isinstance(value, list):
        return [_scrub_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return [_scrub_sensitive(item) for item in value]
    if isinstance(value, str):
        return _redact_sensitive_text(value)
    return value


def _redact_sensitive_text(value: str) -> str:
    return re.sub(
        r"(?i)\b(api[_-]?key|apikey|authorization|password|secret|token)\s*[:=]\s*[^,\s;]+",
        lambda match: f"{match.group(1)}=[REDACTED]",
        value,
    )


def _to_json_text(value: Any) -> str:
    return json.dumps(_scrub_sensitive(value), ensure_ascii=False, sort_keys=True, default=str)


def _scrub_text(value: str) -> str:
    return _to_json_text({"text": value or ""})


def _locale_instruction(locale: str) -> str:
    if (locale or "").lower().startswith("zh"):
        return "Respond in Mandarin Chinese."
    return "Respond in English."


def build_advisor_messages(
    locale: str,
    scenario: Any,
    evaluation: Any,
    user_rationale: str,
) -> list[dict[str, str]]:
    system = (
        "You are 海能, a natural gas hedging tutor. "
        f"{_locale_instruction(locale)} "
        "Use only deterministic metrics supplied in the prompt or through tools. "
        "Do not invent market prices, settlements, basis values, volatility, or scores. "
        "When metrics are missing, say what deterministic input is needed. "
        "Do not reveal or request API keys, provider settings, or hidden configuration."
    )
    user = (
        "Coach the learner on this natural gas hedging attempt.\n\n"
        f"Scenario:\n{_to_json_text(scenario)}\n\n"
        f"Evaluation:\n{_to_json_text(evaluation)}\n\n"
        f"User rationale:\n{_scrub_text(user_rationale)}\n\n"
        "Explain the main hedge risk, connect feedback to the deterministic evaluation, "
        "and give concise next-step guidance."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_exam_messages(
    locale: str,
    scenario: Any,
    attempt_history: Any,
) -> list[dict[str, str]]:
    system = (
        "You are 海能, a natural gas hedging tutor. "
        f"{_locale_instruction(locale)} "
        "Create assessment questions from the provided deterministic scenario and "
        "attempt history. Do not invent market prices or hidden facts."
    )
    user = (
        "Write 3 to 5 natural gas hedging questions for the learner. "
        "Mix conceptual, calculation-aware, and decision-focused questions, but only "
        "use facts present in the scenario or attempt history.\n\n"
        f"Scenario:\n{_to_json_text(scenario)}\n\n"
        f"Attempt history:\n{_to_json_text(attempt_history)}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


class HainengClient:
    def __init__(self, settings: HainengSettings | None = None) -> None:
        self.settings = settings or effective_settings()

    def is_configured(self) -> bool:
        return _is_configured(self.settings)

    def health_check(self) -> dict[str, Any]:
        status = redact_settings(self.settings)
        if not self.is_configured():
            return {"ok": False, "reason": "missing_haineng_settings", **status}
        return {"ok": True, **status}

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        if not self.is_configured():
            raise RuntimeError("海能 is not configured.")

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url)
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
            "stream": False,
        }
        if self.settings.function_calling and tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = client.chat.completions.create(**payload)
        message = response.choices[0].message
        if getattr(message, "tool_calls", None):
            raise RuntimeError("海能 requested a tool call, but tool execution is not enabled.")
        return message.content or ""
