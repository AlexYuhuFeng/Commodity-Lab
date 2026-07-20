from __future__ import annotations

import base64
import dataclasses
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Iterable

DEFAULT_PROVIDER = "haineng"
HAINENG_FLASH_BASE_URL = "http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1"
HAINENG_PRO_BASE_URL = "http://model.ai.cnooc/member1/deepseek-v4-pro-1-5t/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

_PROVIDER_MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "haineng": {
        "label": "Haineng",
        "default_model": "DeepSeek-V4-Flash",
        "models": {
            "DeepSeek-V4-Flash": {"resolved_model": "DeepSeek-V4-Flash", "base_url": HAINENG_FLASH_BASE_URL},
            "DeepSeek-V4": {"resolved_model": "DeepSeek-V4", "base_url": HAINENG_PRO_BASE_URL},
        },
    },
    "deepseek": {
        "label": "DeepSeek",
        "default_model": "deepseek-v4-flash",
        "models": {
            "deepseek-v4-flash": {"resolved_model": "deepseek-v4-flash", "base_url": DEEPSEEK_BASE_URL},
            "deepseek-v4-pro": {"resolved_model": "deepseek-v4-pro", "base_url": DEEPSEEK_BASE_URL},
        },
    },
}


@dataclass
class HainengSettings:
    api_key: str = ""
    base_url: str = ""
    model: str = "DeepSeek-V4-Flash"
    provider: str = DEFAULT_PROVIDER
    streaming: bool = False
    function_calling: bool = True


_runtime_settings: HainengSettings | None = None
LOCAL_SETTINGS_FILE_ENV = "COMMODITY_LAB_AI_SETTINGS_FILE"
DISABLE_LOCAL_SETTINGS_ENV = "COMMODITY_LAB_DISABLE_LOCAL_AI_SETTINGS"
LOCAL_SETTINGS_VERSION = 2


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def normalize_provider(provider: str | None, base_url: str | None = None) -> str:
    value = (provider or "").strip().lower().replace("_", "-").replace(" ", "")
    if value in {"deepseek", "deep-seek", "ds"} or (not value and "api.deepseek.com" in (base_url or "").lower()):
        return "deepseek"
    return "haineng"


def _provider_name(settings: HainengSettings) -> str:
    return normalize_provider(settings.provider, settings.base_url)


def _provider_model_key(settings: HainengSettings) -> str:
    provider = _provider_name(settings)
    requested = (settings.model or "").strip()
    models = _PROVIDER_MODEL_CATALOG[provider]["models"]
    if requested in models:
        return requested
    return str(_PROVIDER_MODEL_CATALOG[provider]["default_model"])


def _provider_base_url(settings: HainengSettings) -> str:
    provider = _provider_name(settings)
    model = _provider_model_key(settings)
    return str(_PROVIDER_MODEL_CATALOG[provider]["models"][model]["base_url"])


def _provider_model_name(settings: HainengSettings) -> str:
    provider = _provider_name(settings)
    model = _provider_model_key(settings)
    return str(_PROVIDER_MODEL_CATALOG[provider]["models"][model]["resolved_model"])


def settings_from_env() -> HainengSettings:
    provider = normalize_provider(os.getenv("COMMODITY_LAB_AI_PROVIDER") or os.getenv("AI_PROVIDER"))
    prefix = "DEEPSEEK" if provider == "deepseek" else "HAINENG"
    return HainengSettings(
        api_key=os.getenv(f"{prefix}_API_KEY", "").strip(),
        provider=provider,
        model=str(_PROVIDER_MODEL_CATALOG[provider]["default_model"]),
        streaming=_env_bool("HAINENG_STREAMING", False),
        function_calling=_env_bool("HAINENG_FUNCTION_CALLING", True),
    )


def set_runtime_settings(settings: HainengSettings | None) -> None:
    global _runtime_settings
    _runtime_settings = settings


def _user_config_dir() -> str:
    if os.name == "nt":
        return os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    return os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))


def local_settings_path() -> str:
    return os.getenv(LOCAL_SETTINGS_FILE_ENV, "").strip() or os.path.join(_user_config_dir(), "Commodity Lab", "AI密钥.json")


def _windows_dpapi(data: bytes, *, protect: bool) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DataBlob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = DataBlob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    operation = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    operation.restype = wintypes.BOOL
    if protect:
        ok = operation(ctypes.byref(source), "Commodity Lab AI credential", None, None, None, 0x1, ctypes.byref(target))
    else:
        ok = operation(ctypes.byref(source), None, None, None, None, 0x1, ctypes.byref(target))
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(target.pbData, ctypes.c_void_p))


def _credential_payload(api_key: str) -> dict[str, str]:
    secret = api_key.strip()
    if os.name == "nt":
        encrypted = _windows_dpapi(secret.encode("utf-8"), protect=True)
        return {"scheme": "windows_dpapi", "ciphertext": base64.b64encode(encrypted).decode("ascii")}
    return {"scheme": "restricted_file", "secret": secret}


def _credential_from_payload(payload: dict[str, Any]) -> str:
    credential = payload.get("credential")
    if not isinstance(credential, dict):
        return str(payload.get("api_key", "")).strip()
    scheme = str(credential.get("scheme", "")).lower()
    if scheme == "windows_dpapi" and os.name == "nt":
        try:
            encrypted = base64.b64decode(str(credential.get("ciphertext", "")), validate=True)
            return _windows_dpapi(encrypted, protect=False).decode("utf-8").strip()
        except Exception:
            return ""
    if scheme == "restricted_file":
        return str(credential.get("secret", "")).strip()
    return ""


def save_persisted_settings(settings: HainengSettings) -> str:
    path = local_settings_path()
    if _env_bool(DISABLE_LOCAL_SETTINGS_ENV, False):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "version": LOCAL_SETTINGS_VERSION,
        "provider": _provider_name(settings),
        "credential": _credential_payload(settings.api_key),
        "streaming": bool(settings.streaming),
        "function_calling": bool(settings.function_calling),
    }
    temp = f"{path}.tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    os.replace(temp, path)
    return path


def load_persisted_settings() -> HainengSettings | None:
    if _env_bool(DISABLE_LOCAL_SETTINGS_ENV, False):
        return None
    try:
        with open(local_settings_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    api_key = _credential_from_payload(payload)
    if not api_key:
        return None
    provider = normalize_provider(str(payload.get("provider", "")))
    return HainengSettings(api_key=api_key, provider=provider, model=str(_PROVIDER_MODEL_CATALOG[provider]["default_model"]))


def effective_settings() -> HainengSettings:
    return _runtime_settings or load_persisted_settings() or settings_from_env()


def _is_configured(settings: HainengSettings) -> bool:
    return bool(settings.api_key.strip() and _provider_base_url(settings))


def redact_settings(settings: HainengSettings) -> dict[str, Any]:
    provider = _provider_name(settings)
    return {
        "configured": _is_configured(settings),
        "provider": provider,
        "provider_label": _PROVIDER_MODEL_CATALOG[provider]["label"],
        "base_url": _provider_base_url(settings),
        "model": _provider_model_key(settings),
        "resolved_model": _provider_model_name(settings),
        "streaming": settings.streaming,
        "function_calling": settings.function_calling,
    }


def provider_catalog() -> dict[str, Any]:
    return {
        provider: {
            "label": config["label"],
            "default_model": config["default_model"],
            "models": [
                {"id": key, "label": key, "resolved_model": value["resolved_model"], "base_url": value["base_url"]}
                for key, value in config["models"].items()
            ],
        }
        for provider, config in _PROVIDER_MODEL_CATALOG.items()
    }


def _scrub_sensitive(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = dataclasses.asdict(value)
    if isinstance(value, dict):
        return {str(k): ("[REDACTED]" if any(term in str(k).lower() for term in ("key", "token", "secret", "password")) else _scrub_sensitive(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub_sensitive(item) for item in value]
    return value


def _to_json_text(value: Any) -> str:
    return json.dumps(_scrub_sensitive(value), ensure_ascii=False, sort_keys=True, default=str)


def _base_system(locale: str) -> str:
    language = "Respond in Mandarin Chinese." if (locale or "").lower().startswith("zh") else "Respond in English."
    return f"You are Haineng, an AI commodity trading and hedging coach. {language} Be concise, practical, and never reveal credentials."


def _messages(locale: str, task: str, context: Any, *, strict_json: bool = False) -> list[dict[str, str]]:
    suffix = " Return only one valid JSON object, with no Markdown fence or surrounding prose." if strict_json else ""
    return [{"role": "system", "content": _base_system(locale)}, {"role": "user", "content": f"{task}\n\nContext:\n{_to_json_text(context)}{suffix}"}]


def build_advisor_messages(locale: str, scenario: Any, evaluation: Any, user_rationale: str) -> list[dict[str, str]]:
    return _messages(locale, "Review this scored hedging decision and give the verdict, strongest point, largest gap, and next drill.", {"scenario": scenario, "evaluation": evaluation, "rationale": user_rationale})


def build_socratic_coach_messages(locale: str, scenario: Any, learner_message: str, market_context: Any | None = None, learner_profile: Any | None = None) -> list[dict[str, str]]:
    return _messages(locale, "Run one Socratic coaching turn. Ask two focused questions and give at most one hint.", {"scenario": scenario, "message": learner_message, "market": market_context or {}, "profile": learner_profile or {}})


def build_exam_messages(locale: str, scenario: Any, attempt_history: Any, curriculum_context: Any | None = None) -> list[dict[str, str]]:
    return _messages(locale, 'Create 3-5 single-choice questions using shape {"title":"...","questions":[{"id":"q1","prompt":"...","options":["A","B"],"correct_index":0,"explanation":"...","skills":["exposure"]}]}.', {"scenario": scenario, "attempt_history": attempt_history, "curriculum": curriculum_context or {}}, strict_json=True)


def build_case_generation_messages(locale: str, scenario: Any, market_context: Any, learner_level: str = "intermediate") -> list[dict[str, str]]:
    return _messages(locale, "Generate one realistic commodity trading training case with background, exposure, decision task, caveats, and learning outcome.", {"scenario": scenario, "market": market_context, "level": learner_level})


def build_event_drill_messages(locale: str, scenario: Any, event_context: str, market_context: Any) -> list[dict[str, str]]:
    return _messages(locale, "Create an event-driven commodity trading drill with transmission path, checklist, hedge candidates, questions, and assumptions.", {"scenario": scenario, "event": event_context, "market": market_context})


def build_concept_tutor_messages(locale: str, concept: str, scenario: Any | None = None, learner_level: str = "intermediate") -> list[dict[str, str]]:
    return _messages(locale, "Teach the requested commodity trading concept with one practical example, one common mistake, and one mini exercise.", {"concept": concept, "scenario": scenario or {}, "level": learner_level})


def build_trade_playbook_messages(locale: str, scenario: Any, market_context: Any, commercial_goal: str) -> list[dict[str, str]]:
    return _messages(locale, "Draft a concise pre-trade playbook covering exposure, instruments, checks, execution, monitoring, and adjustment triggers.", {"goal": commercial_goal, "scenario": scenario, "market": market_context})


def build_live_assistant_messages(locale: str, user_message: str, workspace_state: Any, available_actions: Any) -> list[dict[str, str]]:
    return _messages(locale, 'Act as the workspace copilot. Return JSON shape {"answer":"...","actions":[]}.', {"message": user_message, "workspace": workspace_state, "available_actions": available_actions}, strict_json=True)


def build_training_case_messages(locale: str, template: Any, user_request: str = "", knowledge_coverage: Any | None = None, gas_trading_models: Any | None = None, market_context: Any | None = None) -> list[dict[str, str]]:
    shape = {"scenario": {"id": "string", "title": "string", "summary": "string", "business_type": "string", "knowledge_points": ["string"], "exposure": {"direction": "long|short|spread", "volume_mmbtu": 100000, "volume_unit": "MMBtu|bbl|MWh", "risk": "string"}}, "market": {"unit": "string", "curves": [], "events": []}, "target_actions": [], "rubric": [], "prompt": "string"}
    return _messages(locale, f"Generate one complete Commodity Lab training case using exactly this top-level JSON shape: {_to_json_text(shape)}. Keep target_actions to 2-4 legs and rubric to exactly four rows totalling 100.", {"template": template, "request": user_request, "knowledge": knowledge_coverage or [], "models": gas_trading_models or [], "market": market_context or {}}, strict_json=True)


def build_haineng_tools() -> list[dict[str, Any]]:
    return []


def _wants_json(messages: Iterable[dict[str, str]]) -> bool:
    text = "\n".join(str(message.get("content", "")) for message in messages).lower()
    return "strict json" in text or "valid json object" in text or "json shape" in text or "return only one valid json" in text


def _request_options(settings: HainengSettings, *, json_mode: bool = False) -> dict[str, Any]:
    options: dict[str, Any] = {"max_tokens": 8192}
    if json_mode:
        options["response_format"] = {"type": "json_object"}
    if "flash" in _provider_model_name(settings).lower():
        options["extra_body"] = {"thinking": {"type": "disabled"}}
    return options


class HainengClient:
    def __init__(self, settings: HainengSettings | None = None) -> None:
        self.settings = settings or effective_settings()

    def is_configured(self) -> bool:
        return _is_configured(self.settings)

    def health_check(self) -> dict[str, Any]:
        status = redact_settings(self.settings)
        return {"ok": self.is_configured(), **status, **({} if self.is_configured() else {"reason": "missing_ai_provider_settings"})}

    def complete(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> str:
        if not self.is_configured():
            raise RuntimeError("AI provider is not configured.")
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.api_key, base_url=_provider_base_url(self.settings))
        json_mode = _wants_json(messages)
        payload: dict[str, Any] = {"model": _provider_model_name(self.settings), "messages": messages, "stream": False, **_request_options(self.settings, json_mode=json_mode)}
        if self.settings.function_calling and tools:
            payload.update({"tools": tools, "tool_choice": "auto"})
        last_content = ""
        for attempt in range(2):
            response = client.chat.completions.create(**payload)
            message = response.choices[0].message
            if getattr(message, "tool_calls", None):
                raise RuntimeError("AI provider requested a tool call, but tool execution is not enabled.")
            last_content = (message.content or "").strip()
            if last_content:
                return last_content
            if not json_mode or attempt:
                break
            payload["messages"] = [*messages, {"role": "user", "content": "Return the requested complete JSON object now. Do not return an empty response."}]
        raise RuntimeError("AI provider returned an empty response.")

    def stream_complete(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None):
        if not self.is_configured():
            raise RuntimeError("AI provider is not configured.")
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.api_key, base_url=_provider_base_url(self.settings))
        payload: dict[str, Any] = {"model": _provider_model_name(self.settings), "messages": messages, "stream": True, **_request_options(self.settings, json_mode=_wants_json(messages))}
        if self.settings.function_calling and tools:
            payload.update({"tools": tools, "tool_choice": "auto"})
        for chunk in client.chat.completions.create(**payload):
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            content = getattr(delta, "content", None) if delta is not None else None
            if content:
                yield content
