"""Policy-aware simulation guardrails, independent of financial scoring.

This module describes training permissions, not live-trading authorization.
All quantities in one check must use a common, explicitly supplied unit,
period and commodity. Higher-level callers must verify eligibility and
matching before using this simple volume gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class TrainingPolicy:
    name: str
    maximum_hedge_ratio: float | None
    physical_backing_required: bool = True
    options_permitted: bool = False

    def __post_init__(self) -> None:
        ratio = self.maximum_hedge_ratio
        if ratio is not None and (not isfinite(ratio) or ratio < 0):
            raise ValueError("maximum_hedge_ratio must be finite and non-negative")


CORPORATE_EXAMPLE = TrainingPolicy("corporate-example", 0.80)
PROFESSIONAL_ACADEMY = TrainingPolicy(
    "professional-academy", None, physical_backing_required=False,
    options_permitted=True,
)


def check_training_hedge(
    *,
    policy: TrainingPolicy,
    eligible_physical_volume: float,
    proposed_paper_volume: float,
    instrument_kind: str,
    volumes_comparable: bool = True,
) -> dict:
    """Evaluate a proposed training order against explicit policy constraints.

    This *illustrative* quantity check is not a compliance determination.
    It does not validate direction, maturity, basis, aggregation, existing
    hedges, netting permissions, or organizational entitlements.
    """
    for name, value in (("eligible_physical_volume", eligible_physical_volume),
                        ("proposed_paper_volume", proposed_paper_volume)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite non-negative number")
    if not isinstance(instrument_kind, str) or not instrument_kind.strip():
        raise ValueError("instrument_kind is required")
    if not volumes_comparable:
        return {"permitted": False, "reasons": ["volumes_not_comparable"], "hedge_ratio": None}

    kind = instrument_kind.strip().lower()
    reasons = []
    if kind in {"option", "options", "call", "put"} and not policy.options_permitted:
        reasons.append("options_prohibited")
    if proposed_paper_volume > 0 and eligible_physical_volume == 0 and policy.physical_backing_required:
        reasons.append("physical_backing_required")

    ratio = proposed_paper_volume / eligible_physical_volume if eligible_physical_volume else None
    if policy.maximum_hedge_ratio is not None and proposed_paper_volume > (
        eligible_physical_volume * policy.maximum_hedge_ratio + 1e-9
    ):
        reasons.append("maximum_hedge_ratio_exceeded")
    return {"permitted": not reasons, "reasons": reasons, "hedge_ratio": ratio}
