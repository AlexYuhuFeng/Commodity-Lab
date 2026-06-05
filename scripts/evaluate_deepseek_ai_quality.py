"""Optional DeepSeek quality evaluation for Commodity Lab AI design.

Run locally only. Nothing is stored in the repository.

PowerShell:
    $env:DEEPSEEK_AUTH="<your value>"
    python scripts/evaluate_deepseek_ai_quality.py

Optional:
    $env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
    $env:DEEPSEEK_MODEL="deepseek-v4-flash"
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openai import OpenAI

from core.gas_scenarios import get_capacity_context, get_market_context, get_scenario
from core.haineng_client import (
    build_case_generation_messages,
    build_concept_tutor_messages,
    build_socratic_coach_messages,
    build_trade_playbook_messages,
)
from core.learner_profile import LearnerProfile

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    messages: list[dict[str, str]]
    required_terms: tuple[str, ...]
    blocked_terms: tuple[str, ...] = ()
    min_questions: int = 0


@dataclass(frozen=True)
class EvaluationResult:
    name: str
    passed: bool
    score: int
    reasons: list[str]
    answer_preview: str


def _client() -> OpenAI:
    auth = os.getenv("DEEPSEEK_AUTH", "").strip()
    if not auth:
        raise RuntimeError("DEEPSEEK_AUTH is required for this optional local evaluation.")
    base_url = os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    return OpenAI(**{"api_key": auth, "base_url": base_url})


def _build_cases() -> list[EvaluationCase]:
    scenario = get_scenario("europe_ttf_nbp_spread", locale="en")
    market = get_market_context("europe_ttf_nbp_spread", source="sample")
    capacity = get_capacity_context("europe_ttf_nbp_spread")
    context = {"market": market, "capacity": capacity}
    profile = LearnerProfile.create_default()
    profile.apply_evaluation(
        {
            "baseline_score": 62,
            "mistake_tags": ["basis_risk", "unit_conversion"],
            "score_inputs": {"actual_hedge_type": "basis_hedge"},
        }
    )

    return [
        EvaluationCase(
            name="case_generation_europe_gas",
            messages=build_case_generation_messages(
                "en",
                scenario,
                {**context, "user_request": "Create a realistic TTF/NBP spread training case after a Northwest Europe supply disruption."},
                "intermediate",
            ),
            required_terms=("TTF", "NBP", "basis", "assumption", "decision"),
            blocked_terms=("guaranteed profit", "risk-free"),
        ),
        EvaluationCase(
            name="socratic_coach_ttf_short",
            messages=build_socratic_coach_messages(
                "en",
                scenario,
                "I think I should short TTF because NBP looks expensive and I want to lock the spread.",
                context,
                profile.as_dict(),
            ),
            required_terms=("TTF", "NBP", "basis", "capacity"),
            blocked_terms=("final answer", "guaranteed"),
            min_questions=2,
        ),
        EvaluationCase(
            name="concept_tutor_unit_fx",
            messages=build_concept_tutor_messages(
                "en",
                "TTF/NBP unit and FX normalization",
                scenario,
                "intermediate",
            ),
            required_terms=("TTF", "NBP", "unit", "FX", "MWh"),
            blocked_terms=("risk-free",),
        ),
        EvaluationCase(
            name="trade_playbook_pre_trade",
            messages=build_trade_playbook_messages(
                "en",
                scenario,
                context,
                "Prepare a pre-trade checklist for a TTF-NBP spread hedge before quoting a delivered European gas margin.",
            ),
            required_terms=("liquidity", "FX", "capacity", "credit", "limit"),
            blocked_terms=("risk-free",),
        ),
    ]


def _call_model(client: OpenAI, messages: list[dict[str, str]]) -> str:
    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def _score_case(case: EvaluationCase, answer: str) -> EvaluationResult:
    reasons: list[str] = []
    score = 100
    lower = answer.lower()

    for term in case.required_terms:
        if term.lower() not in lower:
            score -= 12
            reasons.append(f"Missing required concept: {term}")

    for term in case.blocked_terms:
        if term.lower() in lower:
            score -= 20
            reasons.append(f"Contains unsafe framing: {term}")

    if case.min_questions:
        question_count = answer.count("?")
        if question_count < case.min_questions:
            score -= 20
            reasons.append(f"Expected at least {case.min_questions} probing questions, got {question_count}")

    if "assumption" not in lower and case.name != "socratic_coach_ttf_short":
        score -= 8
        reasons.append("Does not clearly label assumptions or caveats")

    if len(answer.strip()) < 300:
        score -= 10
        reasons.append("Answer is too short for a professional training response")

    passed = score >= 75 and not any("unsafe" in reason.lower() for reason in reasons)
    return EvaluationResult(
        name=case.name,
        passed=passed,
        score=max(0, score),
        reasons=reasons,
        answer_preview=answer[:1200],
    )


def main() -> int:
    client = _client()
    results: list[EvaluationResult] = []
    for case in _build_cases():
        print(f"Running {case.name}...")
        answer = _call_model(client, case.messages)
        result = _score_case(case, answer)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {case.name}: score={result.score}")
        for reason in result.reasons:
            print(f"  - {reason}")

    report = {
        "model": os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        "base_url": os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
        "results": [result.__dict__ for result in results],
        "passed": all(result.passed for result in results),
    }
    output_path = PROJECT_ROOT / "deepseek_ai_quality_report.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
