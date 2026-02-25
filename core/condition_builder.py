"""
自定义条件可视化编辑器 - 支持拖拽和直观的条件构建
"""
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime
import ast
import operator as _operator
import math


class OperatorType(Enum):
    """操作符类型"""
    # 数值比较
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    
    # 文本操作
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    
    # 逻辑操作
    IN_RANGE = "in_range"
    NOT_IN_RANGE = "not_in_range"
    
    # 时间操作
    AFTER = "after"
    BEFORE = "before"
    BETWEEN = "between"


class DataType(Enum):
    """数据类型"""
    NUMERIC = "numeric"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    LIST = "list"


@dataclass
class Condition:
    """单个条件"""
    field: str  # 字段名
    operator: OperatorType  # 操作符
    value: Any  # 比较值
    data_type: DataType = DataType.NUMERIC
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'field': self.field,
            'operator': self.operator.value,
            'value': self.value,
            'data_type': self.data_type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """从字典创建"""
        return cls(
            field=data['field'],
            operator=OperatorType(data['operator']),
            value=data['value'],
            data_type=DataType(data.get('data_type', 'numeric'))
        )
    
    def evaluate(self, actual_value: Any) -> bool:
        """评估条件是否满足"""
        op = self.operator
        val = self.value
        
        try:
            if op == OperatorType.EQUALS:
                return actual_value == val
            elif op == OperatorType.NOT_EQUALS:
                return actual_value != val
            elif op == OperatorType.GREATER_THAN:
                return float(actual_value) > float(val)
            elif op == OperatorType.LESS_THAN:
                return float(actual_value) < float(val)
            elif op == OperatorType.GREATER_EQUAL:
                return float(actual_value) >= float(val)
            elif op == OperatorType.LESS_EQUAL:
                return float(actual_value) <= float(val)
            elif op == OperatorType.CONTAINS:
                return str(val) in str(actual_value)
            elif op == OperatorType.NOT_CONTAINS:
                return str(val) not in str(actual_value)
            elif op == OperatorType.STARTS_WITH:
                return str(actual_value).startswith(str(val))
            elif op == OperatorType.ENDS_WITH:
                return str(actual_value).endswith(str(val))
            elif op == OperatorType.IN_RANGE:
                # val 应该是 (min, max) 元组
                min_val, max_val = val
                return float(min_val) <= float(actual_value) <= float(max_val)
            elif op == OperatorType.NOT_IN_RANGE:
                min_val, max_val = val
                return not (float(min_val) <= float(actual_value) <= float(max_val))
            else:
                return False
        except (TypeError, ValueError):
            return False


class LogicalOperator(Enum):
    """逻辑操作符"""
    AND = "and"
    OR = "or"


class ConditionGroup:
    """条件组 - 支持复杂逻辑"""
    
    def __init__(self, logical_op: LogicalOperator = LogicalOperator.AND):
        self.logical_op = logical_op
        self.conditions: List[Condition] = []
        self.sub_groups: List['ConditionGroup'] = []
    
    def add_condition(self, condition: Condition):
        """添加条件"""
        self.conditions.append(condition)
        
    def add_group(self, group: 'ConditionGroup'):
        """添加子条件组"""
        self.sub_groups.append(group)
        
    def remove_condition(self, index: int):
        """删除条件"""
        if 0 <= index < len(self.conditions):
            self.conditions.pop(index)
            
    def remove_group(self, index: int):
        """删除子组"""
        if 0 <= index < len(self.sub_groups):
            self.sub_groups.pop(index)
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """评估整个条件组"""
        # 评估直接条件
        condition_results = [
            cond.evaluate(data.get(cond.field))
            for cond in self.conditions
        ]
        
        # 评估子组
        group_results = [
            group.evaluate(data)
            for group in self.sub_groups
        ]
        
        all_results = condition_results + group_results
        
        if not all_results:
            return True
        
        if self.logical_op == LogicalOperator.AND:
            return all(all_results)
        else:  # OR
            return any(all_results)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'logical_op': self.logical_op.value,
            'conditions': [c.to_dict() for c in self.conditions],
            'sub_groups': [g.to_dict() for g in self.sub_groups]
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """从字典创建"""
        group = cls(LogicalOperator(data['logical_op']))
        
        for cond_data in data.get('conditions', []):
            group.add_condition(Condition.from_dict(cond_data))
        
        for group_data in data.get('sub_groups', []):
            group.add_group(cls.from_dict(group_data))
        
        return group
    
    def to_expression(self) -> str:
        """转换为易读的表达式"""
        parts = []
        
        # 条件表达式
        for cond in self.conditions:
            parts.append(f"{cond.field} {cond.operator.value} {cond.value}")
        
        # 子组表达式
        for group in self.sub_groups:
            parts.append(f"({group.to_expression()})")
        
        op_str = f" {self.logical_op.value.upper()} "
        return op_str.join(parts) if parts else "true"


class ConditionBuilder:
    """条件构建器 - 提供便利的API"""
    
    @staticmethod
    def create_simple(field: str, operator: OperatorType, value: Any) -> Condition:
        """创建简单条件"""
        return Condition(field=field, operator=operator, value=value)
    
    @staticmethod
    def create_comparison(field: str, comparator: str, value: Any) -> Condition:
        """
        创建比较条件 (更易用的API)
        
        Args:
            field: 字段名
            comparator: '>', '<', '>=', '<=', '==', '!='
            value: 值
        """
        operator_map = {
            '>': OperatorType.GREATER_THAN,
            '<': OperatorType.LESS_THAN,
            '>=': OperatorType.GREATER_EQUAL,
            '<=': OperatorType.LESS_EQUAL,
            '==': OperatorType.EQUALS,
            '!=': OperatorType.NOT_EQUALS
        }
        return Condition(
            field=field,
            operator=operator_map.get(comparator, OperatorType.EQUALS),
            value=value
        )
    
    @staticmethod
    def create_range(field: str, min_val: float, max_val: float) -> Condition:
        """创建范围条件"""
        return Condition(
            field=field,
            operator=OperatorType.IN_RANGE,
            value=(min_val, max_val)
        )
    
    @staticmethod
    def create_text_search(field: str, search_type: str, text: str) -> Condition:
        """
        创建文本搜索条件
        
        Args:
            field: 字段名
            search_type: 'contains', 'starts_with', 'ends_with'
            text: 搜索文本
        """
        operator_map = {
            'contains': OperatorType.CONTAINS,
            'starts_with': OperatorType.STARTS_WITH,
            'ends_with': OperatorType.ENDS_WITH
        }
        return Condition(
            field=field,
            operator=operator_map.get(search_type, OperatorType.CONTAINS),
            value=text,
            data_type=DataType.TEXT
        )
    
    @staticmethod
    def create_group(logical_op: str = 'and') -> ConditionGroup:
        """创建条件组"""
        op = LogicalOperator.AND if logical_op.lower() == 'and' else LogicalOperator.OR
        return ConditionGroup(op)


class ConditionTemplate:
    """预定义的条件模板"""
    
    # 商品对象的常用字段
    COMMODITY_FIELDS = {
        'price': DataType.NUMERIC,
        'volume': DataType.NUMERIC,
        'volatility': DataType.NUMERIC,
        'zscore': DataType.NUMERIC,
        'days_since_update': DataType.NUMERIC,
        'missing_percent': DataType.NUMERIC,
        'correlation': DataType.NUMERIC,
        'name': DataType.TEXT,
        'category': DataType.TEXT,
        'last_update': DataType.DATETIME
    }
    
    @staticmethod
    def price_above(threshold: float) -> Condition:
        """价格高于"""
        return ConditionBuilder.create_comparison('price', '>', threshold)
    
    @staticmethod
    def price_below(threshold: float) -> Condition:
        """价格低于"""
        return ConditionBuilder.create_comparison('price', '<', threshold)
    
    @staticmethod
    def price_in_range(min_price: float, max_price: float) -> Condition:
        """价格在范围内"""
        return ConditionBuilder.create_range('price', min_price, max_price)
    
    @staticmethod
    def high_volatility(threshold: float) -> Condition:
        """高波动率"""
        return ConditionBuilder.create_comparison('volatility', '>', threshold)
    
    @staticmethod
    def high_zscore(threshold: float) -> Condition:
        """高Z分数 (异常"""
        return ConditionBuilder.create_comparison('zscore', '>', threshold)
    
    @staticmethod
    def data_stale(days: int) -> Condition:
        """数据过期"""
        return ConditionBuilder.create_comparison('days_since_update', '>', days)
    
    @staticmethod
    def data_missing(percent_threshold: float) -> Condition:
        """数据缺失"""
        return ConditionBuilder.create_comparison('missing_percent', '>', percent_threshold)
    
    @staticmethod
    def category_filter(category: str) -> Condition:
        """分类过滤"""
        return ConditionBuilder.create_comparison('category', '==', category)
    
    @staticmethod
    def name_contains(text: str) -> Condition:
        """名称包含"""
        return ConditionBuilder.create_text_search('name', 'contains', text)


class ConditionValidator:
    """条件验证器"""
    
    @staticmethod
    def validate_condition(condition: Condition) -> Tuple[bool, str]:
        """
        验证单个条件
        
        Returns:
            (是否有效, 错误消息)
        """
        if not condition.field:
            return False, "字段名不能为空"
        
        if condition.data_type == DataType.NUMERIC:
            if condition.operator in [OperatorType.GREATER_THAN, OperatorType.LESS_THAN,
                                     OperatorType.GREATER_EQUAL, OperatorType.LESS_EQUAL]:
                try:
                    float(condition.value)
                except (TypeError, ValueError):
                    return False, f"值 '{condition.value}' 不是有效的数字"
            
            elif condition.operator == OperatorType.IN_RANGE:
                if not isinstance(condition.value, (tuple, list)) or len(condition.value) != 2:
                    return False, "范围值应该是 (min, max) 元组"
                try:
                    float(condition.value[0])
                    float(condition.value[1])
                except (TypeError, ValueError):
                    return False, "范围值必须是数字"
        
        return True, ""


class ConditionEvaluator:
    """安全评估自定义条件表达式的评估器。

    支持基本算术、比较和逻辑运算，以及来自上下文的名称和少量安全函数。
    """

    _safe_funcs = {
        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
        'int': int,
        'float': float,
        'math': math
    }

    def evaluate(self, expr: str, context: Dict[str, Any]) -> Any:
        """Evaluate expression `expr` using values from `context`.

        Raises ValueError on invalid/unsafe expressions.
        """
        if not expr:
            return False

        try:
            node = ast.parse(expr, mode='eval')
            return self._eval(node.body, context)
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")

    def _eval(self, node, context):
        if isinstance(node, ast.BinOp):
            left = self._eval(node.left, context)
            right = self._eval(node.right, context)
            op_type = type(node.op)
            ops = {
                ast.Add: _operator.add,
                ast.Sub: _operator.sub,
                ast.Mult: _operator.mul,
                ast.Div: _operator.truediv,
                ast.Mod: _operator.mod,
                ast.Pow: _operator.pow,
            }
            if op_type in ops:
                return ops[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand, context)
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.UAdd):
                return +operand
        elif isinstance(node, ast.BoolOp):
            values = [self._eval(v, context) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
        elif isinstance(node, ast.Compare):
            left = self._eval(node.left, context)
            result = True
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval(comparator, context)
                if isinstance(op, ast.Eq):
                    result = result and (left == right)
                elif isinstance(op, ast.NotEq):
                    result = result and (left != right)
                elif isinstance(op, ast.Lt):
                    result = result and (left < right)
                elif isinstance(op, ast.LtE):
                    result = result and (left <= right)
                elif isinstance(op, ast.Gt):
                    result = result and (left > right)
                elif isinstance(op, ast.GtE):
                    result = result and (left >= right)
                else:
                    raise ValueError(f"Unsupported comparator: {op}")
                left = right
            return result
        elif isinstance(node, ast.Call):
            # Only allow safe function names
            if isinstance(node.func, ast.Attribute):
                # e.g., math.sqrt(x)
                value = self._eval(node.func.value, context)
                attr = node.func.attr
                func = getattr(value, attr, None)
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
                func = self._safe_funcs.get(func_name)
            else:
                func = None

            if not callable(func):
                raise ValueError(f"Unsafe function in expression: {ast.dump(node.func)}")

            args = [self._eval(a, context) for a in node.args]
            return func(*args)
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            if node.id in self._safe_funcs:
                return self._safe_funcs[node.id]
            raise ValueError(f"Unknown name: {node.id}")
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):
            return node.n

        raise ValueError(f"Unsupported expression node: {type(node).__name__}")
    
    @staticmethod
    def validate_group(group: ConditionGroup) -> Tuple[bool, str]:
        """验证条件组"""
        if not group.conditions and not group.sub_groups:
            return False, "条件组不能为空"
        
        # 验证所有条件
        for i, cond in enumerate(group.conditions):
            is_valid, msg = ConditionValidator.validate_condition(cond)
            if not is_valid:
                return False, f"条件 {i+1}: {msg}"
        
        # 验证所有子组
        for i, subgroup in enumerate(group.sub_groups):
            is_valid, msg = ConditionValidator.validate_group(subgroup)
            if not is_valid:
                return False, f"条件组 {i+1}: {msg}"
        
        return True, ""


# 使用示例
if __name__ == "__main__":
    # 创建复杂条件组
    builder = ConditionBuilder()
    
    # 条件1: 价格 > 100
    cond1 = builder.create_comparison('price', '>', 100)
    
    # 条件2: 波动率 > 0.2
    cond2 = builder.create_comparison('volatility', '>', 0.2)
    
    # 条件组: (price > 100) AND (volatility > 0.2)
    group1 = builder.create_group('and')
    group1.add_condition(cond1)
    group1.add_condition(cond2)
    
    # 条件3: 分类 == "贵金属"
    cond3 = builder.create_comparison('category', '==', '贵金属')
    
    # 最终组: ((price > 100) AND (volatility > 0.2)) OR (category == "贵金属")
    final_group = builder.create_group('or')
    final_group.add_group(group1)
    final_group.add_condition(cond3)
    
    # 测试评估
    test_data = {
        'price': 150,
        'volatility': 0.3,
        'category': '农产品'
    }
    
    result = final_group.evaluate(test_data)
    print(f"条件评估结果: {result}")
    print(f"表达式: {final_group.to_expression()}")
    print(f"JSON: {json.dumps(final_group.to_dict(), indent=2)}")



class ConditionEvaluator:
    """Simple expression evaluator for scheduler/backward compatibility."""

    @staticmethod
    def evaluate(expression: str, context: dict[str, Any]) -> Any:
        if not expression:
            return False
        safe_locals = {
            "price": context.get("price"),
            "threshold": context.get("threshold"),
            "mean": context.get("mean"),
            "std": context.get("std"),
            **{k: v for k, v in context.items() if isinstance(k, str)},
        }
        return eval(expression, {"__builtins__": {}}, safe_locals)
