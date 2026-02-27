import pytest

from core.condition_builder import ConditionEvaluator


def test_condition_evaluator_basic_boolean_expression():
    result = ConditionEvaluator.evaluate("value > threshold * 1.05", {"value": 106.0, "threshold": 100.0})
    assert result is True


def test_condition_evaluator_rejects_unsafe_name():
    with pytest.raises(ValueError):
        ConditionEvaluator.evaluate("__import__('os').system('echo hacked')", {"value": 1, "threshold": 1})


def test_condition_evaluator_rejects_unsafe_attribute_chain():
    with pytest.raises(ValueError):
        ConditionEvaluator.evaluate("(1).__class__.__mro__", {"value": 1, "threshold": 1})
