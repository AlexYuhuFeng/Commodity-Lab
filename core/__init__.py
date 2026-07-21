"""Commodity Lab core package.

Keep provider compatibility patches here so the established Haineng client
contract remains stable while provider-specific capabilities can be enabled
without rewriting its prompts, tools, or default request options.
"""

from __future__ import annotations

from typing import Any


def _is_structured_json_request(messages: list[dict[str, str]]) -> bool:
    text = "\n".join(str(message.get("content", "")) for message in messages).lower()
    markers = (
        "compact strict json",
        "strict json only",
        "return only one valid json object",
        "return only compact strict json",
        "required json shape",
    )
    return any(marker in text for marker in markers)


def _install_deepseek_json_mode() -> None:
    from . import haineng_client as module

    original_complete = module.HainengClient.complete
    original_stream_complete = module.HainengClient.stream_complete

    def complete(
        self: Any,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        if module._provider_name(self.settings) != "deepseek" or not _is_structured_json_request(messages):
            return original_complete(self, messages, tools=tools)
        if not self.is_configured():
            raise RuntimeError("AI provider is not configured.")

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.api_key, base_url=module._provider_base_url(self.settings))
        payload: dict[str, Any] = {
            "model": module._provider_model_name(self.settings),
            "messages": messages,
            "stream": False,
            **module._provider_request_options(self.settings),
            "response_format": {"type": "json_object"},
        }
        if self.settings.function_calling and tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = client.chat.completions.create(**payload)
        message = response.choices[0].message
        if getattr(message, "tool_calls", None):
            raise RuntimeError("AI provider requested a tool call, but tool execution is not enabled.")
        content = message.content or ""
        if content.strip():
            return content

        # DeepSeek may rarely return an empty body in JSON mode. Retry once
        # with the same deterministic request instead of surfacing a JSON
        # decoder error to the desktop application.
        response = client.chat.completions.create(**payload)
        message = response.choices[0].message
        if getattr(message, "tool_calls", None):
            raise RuntimeError("AI provider requested a tool call, but tool execution is not enabled.")
        return message.content or ""

    def stream_complete(
        self: Any,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
    ):
        if module._provider_name(self.settings) != "deepseek" or not _is_structured_json_request(messages):
            yield from original_stream_complete(self, messages, tools=tools)
            return
        if not self.is_configured():
            raise RuntimeError("AI provider is not configured.")

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.api_key, base_url=module._provider_base_url(self.settings))
        payload: dict[str, Any] = {
            "model": module._provider_model_name(self.settings),
            "messages": messages,
            "stream": True,
            **module._provider_request_options(self.settings),
            "response_format": {"type": "json_object"},
        }
        if self.settings.function_calling and tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = client.chat.completions.create(**payload)
        for chunk in response:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            content = getattr(delta, "content", None) if delta is not None else None
            if content:
                yield content

    module.HainengClient.complete = complete
    module.HainengClient.stream_complete = stream_complete


_install_deepseek_json_mode()
