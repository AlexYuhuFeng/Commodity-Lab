"""Regression tests for illustrative, non-production policy checks."""
import math
import pytest

from core.training_policy import (
    CORPORATE_EXAMPLE, PROFESSIONAL_ACADEMY, TrainingPolicy, check_training_hedge,
)


def assess(policy=CORPORATE_EXAMPLE, physical=100_000, paper=80_000, kind="future", comparable=True):
    return check_training_hedge(
        policy=policy, eligible_physical_volume=physical, proposed_paper_volume=paper,
        instrument_kind=kind, volumes_comparable=comparable,
    )


def test_example_policy_accepts_exactly_eighty_percent():
    assert assess()["permitted"] is True
    assert assess()["hedge_ratio"] == pytest.approx(0.8)


def test_example_policy_rejects_excess_paper():
    outcome = assess(paper=80_001)
    assert outcome["permitted"] is False
    assert "maximum_hedge_ratio_exceeded" in outcome["reasons"]


def test_example_policy_requires_physical_backing():
    outcome = assess(physical=0, paper=10)
    assert "physical_backing_required" in outcome["reasons"]


def test_example_policy_prohibits_options():
    assert "options_prohibited" in assess(kind="call")["reasons"]


def test_academy_is_not_bound_by_corporate_illustrative_rules():
    assert assess(policy=PROFESSIONAL_ACADEMY, physical=0, paper=120_000, kind="put")["permitted"]


def test_noncomparable_volumes_are_rejected_before_ratio_check():
    assert assess(comparable=False)["reasons"] == ["volumes_not_comparable"]


@pytest.mark.parametrize("volume", [-1, math.inf, math.nan, True])
def test_invalid_quantity_rejected(volume):
    with pytest.raises(ValueError):
        assess(paper=volume)


def test_negative_policy_limit_rejected():
    with pytest.raises(ValueError):
        TrainingPolicy("bad", -0.5)
