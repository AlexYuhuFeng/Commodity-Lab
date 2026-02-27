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


def test_validate_group_supports_nested_group_recursion():
    from core.condition_builder import Condition, ConditionGroup, ConditionEvaluator, DataType, LogicalOperator, OperatorType

    parent = ConditionGroup(LogicalOperator.AND)
    child = ConditionGroup(LogicalOperator.OR)
    child.add_condition(Condition(field="value", operator=OperatorType.GREATER_THAN, value=1, data_type=DataType.NUMERIC))
    parent.add_group(child)

    ok, msg = ConditionEvaluator.validate_group(parent)
    assert ok is True
    assert msg == ""
