from __future__ import annotations

import os
from typing import Any

import requests


class DeepseekError(RuntimeError):
    pass


def build_prompt(question: str, context: str | None = None, mode: str = "Performance review", history: list[dict[str, str]] | None = None) -> str:
    history_text = "\n".join(
        f"Q: {entry['question']}\nA: {entry['answer']}" for entry in (history or [])[-5:]
    )
    mode_instruction = {
        "Performance review": (
            "Evaluate the hedge exposure, recent order performance, and risk balance. "
            "Provide constructive feedback and highlight potential weaknesses."
        ),
        "Guidance & mentoring": (
            "Act like a hedge mentor. Ask clarifying questions, explain your reasoning, and coach the user through their next decision."
        ),
        "Hints and next steps": (
            "Provide concise, practical hints or specific next actions the user can take to improve their hedge plan."
        ),
    }.get(mode, "Provide helpful guidance on hedge decisions and risk management.")

    prompt = (
        f"You are an expert hedge learning advisor. {mode_instruction}\n\n"
        f"User request: {question}\n"
        f"Context: {context or 'No additional context provided.'}\n"
    )
    if history_text:
        prompt += f"\nRecent advisor exchange:\n{history_text}\n"
    prompt += (
        "\nRespond in a supportive tone, focus on understanding the user's challenge, and "
        "offer guidance rather than just judging performance. If the user asks for a hint, provide one clear next step."
    )
    return prompt


def ask_deepseek(
    question: str,
    context: str | None = None,
    mode: str = "Performance review",
    history: list[dict[str, str]] | None = None,
) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.ai/v1/analysis").rstrip("/")
    if not api_key:
        return (
            "DEEPSEEK API key is missing. Configure DEEPSEEK_API_KEY in the environment "
            "or app settings to enable analysis."
        )
    if not question:
        return "Please ask a question about your hedge operations or market exposure."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "question": build_prompt(question, context=context, mode=mode, history=history),
        "context": context or "",
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-large"),
    }
    try:
        response = requests.post(f"{api_url}", json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            raise DeepseekError(
                f"DEEPSEEK API error {response.status_code}: {response.text}"
            )
        data = response.json()
        answer = data.get("answer") or data.get("output") or data.get("text")
        if not answer:
            raise DeepseekError("DEEPSEEK returned an unexpected response format.")
        return str(answer)
    except requests.RequestException as exc:
        raise DeepseekError(f"DEEPSEEK request failed: {exc}") from exc
