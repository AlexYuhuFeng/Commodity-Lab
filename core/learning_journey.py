"""Adaptive learning journey engine for Commodity Lab.

This module turns the platform from a static scenario list into a guided learning
loop. It uses learner profile weaknesses, scenario tags, and AI capabilities to
recommend the next practical training step.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.learner_profile import LearnerProfile
from core.scenario_registry import DEFAULT_SCENARIO_REGISTRY, ScenarioRegistry

SKILL_TO_TAGS: dict[str, tuple[str, ...]] = {
    "price_risk": ("outright", "producer", "hedge"),
    "basis": ("basis", "hub", "ttf", "nbp"),
    "spread": ("spread", "calendar_spread", "seasonality"),
    "storage": ("storage", "calendar_spread", "seasonality"),
    "capacity_route": ("capacity", "route", "europe_gas"),
    "units_fx": ("units_fx", "nbp", "ttf"),
    "controls": ("risk", "limits", "checklist"),
    "operations": ("capacity", "route", "nomination"),
}

SKILL_TO_AI_CAPABILITY: dict[str, str] = {
    "price_risk": "advisor_review",
    "basis": "socratic_coach",
    "spread": "socratic_coach",
    "storage": "case_generation",
    "capacity_route": "trade_playbook",
    "units_fx": "concept_tutor",
    "controls": "trade_playbook",
    "operations": "event_drill",
}


@dataclass(frozen=True)
class JourneyRecommendation:
    scenario_id: str
    title: str
    region: str
    skill_id: str
    ai_capability: str
    reason: str
    priority: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "region": self.region,
            "skill_id": self.skill_id,
            "ai_capability": self.ai_capability,
            "reason": self.reason,
            "priority": self.priority,
        }


def _scenario_match_score(scenario: dict[str, Any], skill_id: str) -> int:
    tags = {str(tag).lower() for tag in scenario.get("tags", [])}
    expected_tags = set(SKILL_TO_TAGS.get(skill_id, ()))
    score = len(tags & expected_tags) * 10
    if scenario.get("region") == "europe":
        score += 5
    if scenario.get("status") == "enabled":
        score += 20
    if scenario.get("metadata", {}).get("v1_focus"):
        score += 10
    return score


def recommend_next_steps(
    profile: LearnerProfile | dict[str, Any],
    *,
    locale: str = "en",
    registry: ScenarioRegistry = DEFAULT_SCENARIO_REGISTRY,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Recommend next training steps from weak skills and enabled scenarios."""
    if isinstance(profile, LearnerProfile):
        profile_data = profile.as_dict()
    else:
        profile_data = profile

    weakest = profile_data.get("weakest_skills", []) or []
    if not weakest and "skills" in profile_data:
        weakest = sorted(profile_data["skills"].values(), key=lambda item: item.get("score", 100))[:limit]

    enabled_scenarios = registry.enabled(commodity="natural_gas", locale=locale)
    recommendations: list[JourneyRecommendation] = []

    for index, skill in enumerate(weakest[: max(limit, 1)]):
        skill_id = str(skill.get("skill_id", "controls"))
        ranked = sorted(enabled_scenarios, key=lambda scenario: _scenario_match_score(scenario, skill_id), reverse=True)
        if not ranked:
            continue
        scenario = ranked[0]
        capability = SKILL_TO_AI_CAPABILITY.get(skill_id, "socratic_coach")
        reason = _reason_text(skill_id, scenario, locale)
        recommendations.append(
            JourneyRecommendation(
                scenario_id=scenario["id"],
                title=scenario["title"],
                region=scenario.get("region", "europe"),
                skill_id=skill_id,
                ai_capability=capability,
                reason=reason,
                priority=index + 1,
            )
        )

    deduped: list[JourneyRecommendation] = []
    seen: set[tuple[str, str]] = set()
    for item in recommendations:
        key = (item.scenario_id, item.skill_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return [item.as_dict() for item in deduped[:limit]]


def build_learning_journey(
    profile: LearnerProfile | dict[str, Any],
    *,
    locale: str = "en",
    registry: ScenarioRegistry = DEFAULT_SCENARIO_REGISTRY,
) -> dict[str, Any]:
    if isinstance(profile, LearnerProfile):
        profile_data = profile.as_dict()
    else:
        profile_data = profile
    recommendations = recommend_next_steps(profile_data, locale=locale, registry=registry, limit=3)
    return {
        "mode": "adaptive",
        "current_focus": {"commodity": "natural_gas", "region": "europe"},
        "profile": profile_data,
        "recommendations": recommendations,
        "journey_loop": [
            "market_context",
            "case_generation_or_socratic_coach",
            "learner_decision",
            "deterministic_scoring",
            "profile_update",
            "adaptive_next_step",
        ],
    }


def _reason_text(skill_id: str, scenario: dict[str, Any], locale: str) -> str:
    if (locale or "").lower().startswith("zh"):
        labels = {
            "basis": "基差能力较弱，建议用欧洲枢纽价差场景强化 TTF/NBP 逻辑。",
            "spread": "价差能力较弱，建议训练枢纽价差或储气月差。",
            "storage": "储气经济性较弱，建议训练注采季节价差。",
            "capacity_route": "路径和运力能力较弱，建议用欧洲天然气路径/容量场景强化交易前检查。",
            "units_fx": "单位和汇率归一化较弱，建议围绕 NBP/TTF 进行概念教学。",
            "controls": "风控检查较弱，建议生成交易预案并检查流动性、信用、容量和限额。",
        }
        return labels.get(skill_id, f"根据画像，建议继续训练：{scenario['title']}。")
    labels = {
        "basis": "Basis skill is weak; use the Europe hub-spread scenario to reinforce TTF/NBP logic.",
        "spread": "Spread skill is weak; train hub spread or storage calendar spread reasoning.",
        "storage": "Storage economics is weak; practice injection-withdrawal seasonal spread logic.",
        "capacity_route": "Capacity and route skill is weak; use Europe gas route/capacity checks before trade execution.",
        "units_fx": "Unit and FX normalization is weak; use NBP/TTF concept tutoring before spread decisions.",
        "controls": "Risk-control skill is weak; generate a trade playbook covering liquidity, credit, capacity, and limits.",
    }
    return labels.get(skill_id, f"Profile indicates this learner should continue with {scenario['title']}.")
