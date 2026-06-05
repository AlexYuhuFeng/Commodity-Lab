"""Learner profile primitives for Commodity Lab."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

DEFAULT_SKILLS: tuple[str, ...] = (
    "price_risk",
    "basis",
    "spread",
    "storage",
    "capacity_route",
    "units_fx",
    "controls",
    "operations",
)

TAG_TO_SKILL: dict[str, str] = {
    "wrong_side": "price_risk",
    "wrong_hedge_type": "basis",
    "basis_risk": "basis",
    "spread_risk": "spread",
    "storage_spread": "storage",
    "capacity_risk": "capacity_route",
    "route_risk": "capacity_route",
    "unit_conversion": "units_fx",
    "fx_risk": "units_fx",
    "missing_control": "controls",
    "operations": "operations",
}


@dataclass
class SkillScore:
    skill_id: str
    score: float = 50.0
    attempts: int = 0
    last_updated: str | None = None

    def update(self, delta: float) -> None:
        self.score = min(100.0, max(0.0, round(self.score + delta, 2)))
        self.attempts += 1
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LearnerProfile:
    learner_id: str = "local"
    skills: dict[str, SkillScore] = field(default_factory=dict)
    attempt_count: int = 0

    @classmethod
    def create_default(cls, learner_id: str = "local") -> "LearnerProfile":
        return cls(learner_id=learner_id, skills={skill: SkillScore(skill) for skill in DEFAULT_SKILLS})

    def ensure_skill(self, skill_id: str) -> SkillScore:
        if skill_id not in self.skills:
            self.skills[skill_id] = SkillScore(skill_id)
        return self.skills[skill_id]

    def apply_evaluation(self, evaluation: dict[str, Any]) -> dict[str, Any]:
        self.attempt_count += 1
        baseline = float(evaluation.get("baseline_score", 0) or 0)
        general_delta = (baseline - 70.0) / 20.0
        tags = [str(tag) for tag in evaluation.get("mistake_tags", [])]

        touched: set[str] = set()
        for tag in tags:
            skill_id = TAG_TO_SKILL.get(tag, "controls")
            self.ensure_skill(skill_id).update(-6.0)
            touched.add(skill_id)

        text = str(evaluation).lower()
        if "basis" in text:
            touched.add("basis")
        if "spread" in text:
            touched.add("spread")
        if "capacity" in text or "route" in text:
            touched.add("capacity_route")
        if "fx" in text or "unit" in text:
            touched.add("units_fx")

        if not touched:
            touched.update({"price_risk", "controls"})

        for skill_id in touched:
            self.ensure_skill(skill_id).update(general_delta)

        return self.as_dict()

    def weakest_skills(self, limit: int = 3) -> list[dict[str, Any]]:
        return [score.as_dict() for score in sorted(self.skills.values(), key=lambda item: item.score)[:limit]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "learner_id": self.learner_id,
            "attempt_count": self.attempt_count,
            "skills": {key: value.as_dict() for key, value in self.skills.items()},
            "weakest_skills": self.weakest_skills(),
        }
