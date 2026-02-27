from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.db import (
    list_derived_recipes,
    query_series_long,
    upsert_derived_daily,
)

_ALLOWED_FUNCTIONS = {
    "abs",
    "log",
    "sqrt",
    "exp",
    "clip",
    "where",
    "lag",
    "rolling_mean",
    "rolling_std",
    "pct_change",
    "zscore",
}


class ExpressionValidationError(ValueError):
    pass


@dataclass
class Recipe:
    derived_ticker: str
    source_tickers: list[str]
    expression: str


def _sanitize_var_name(ticker: str) -> str:
    out = re.sub(r"[^0-9A-Za-z_]", "_", str(ticker).strip())
    if out and out[0].isdigit():
        out = f"T_{out}"
    return out or "T"


def _validate_expression(expression: str) -> None:
    expr = (expression or "").strip()
    if not expr:
        raise ExpressionValidationError("expression is required")

    tree = ast.parse(expr, mode="eval")
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Num,
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.Call,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.BoolOp,
        ast.And,
        ast.Or,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ExpressionValidationError(f"unsupported expression node: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCTIONS:
                raise ExpressionValidationError("only whitelisted functions are allowed")


def _eval_function(name: str, args: list):
    if name == "abs":
        return args[0].abs()
    if name == "log":
        return args[0].map(lambda x: pd.NA if pd.isna(x) or x <= 0 else float(np.log(x)))
    if name == "sqrt":
        return args[0].map(lambda x: pd.NA if pd.isna(x) or x < 0 else float(np.sqrt(x)))
    if name == "exp":
        return args[0].map(lambda x: pd.NA if pd.isna(x) else float(np.exp(x)))
    if name == "clip":
        lower = args[1] if len(args) > 1 else None
        upper = args[2] if len(args) > 2 else None
        return args[0].clip(lower=lower, upper=upper)
    if name == "where":
        return args[1].where(args[0], args[2])
    if name == "lag":
        return args[0].shift(int(args[1]))
    if name == "rolling_mean":
        return args[0].rolling(int(args[1])).mean()
    if name == "rolling_std":
        return args[0].rolling(int(args[1])).std()
    if name == "pct_change":
        period = int(args[1]) if len(args) > 1 else 1
        return args[0].pct_change(periods=period)
    if name == "zscore":
        window = int(args[1]) if len(args) > 1 else 20
        mean = args[0].rolling(window).mean()
        std = args[0].rolling(window).std()
        return (args[0] - mean) / std
    raise ExpressionValidationError(f"unsupported function: {name}")


def _eval_node(node: ast.AST, ctx: dict):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, ctx)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Name):
        if node.id not in ctx:
            raise ExpressionValidationError(f"unknown variable: {node.id}")
        return ctx[node.id]
    if isinstance(node, ast.UnaryOp):
        v = _eval_node(node.operand, ctx)
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return +v
    if isinstance(node, ast.BinOp):
        l = _eval_node(node.left, ctx)
        r = _eval_node(node.right, ctx)
        if isinstance(node.op, ast.Add):
            return l + r
        if isinstance(node.op, ast.Sub):
            return l - r
        if isinstance(node.op, ast.Mult):
            return l * r
        if isinstance(node.op, ast.Div):
            return l / r
        if isinstance(node.op, ast.Pow):
            return l**r
        if isinstance(node.op, ast.Mod):
            return l % r
    if isinstance(node, ast.Call):
        fn = node.func.id
        args = [_eval_node(a, ctx) for a in node.args]
        return _eval_function(fn, args)
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, ctx)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval_node(comp, ctx)
            if isinstance(op, ast.Gt):
                left = left > right
            elif isinstance(op, ast.GtE):
                left = left >= right
            elif isinstance(op, ast.Lt):
                left = left < right
            elif isinstance(op, ast.LtE):
                left = left <= right
            elif isinstance(op, ast.Eq):
                left = left == right
            elif isinstance(op, ast.NotEq):
                left = left != right
        return left
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(v, ctx) for v in node.values]
        out = values[0]
        for v in values[1:]:
            out = (out & v) if isinstance(node.op, ast.And) else (out | v)
        return out
    raise ExpressionValidationError("unsupported expression")


def evaluate_recipe(con, source_tickers: list[str], expression: str) -> pd.DataFrame:
    src = [str(t).strip() for t in source_tickers if str(t).strip()]
    if not src:
        raise ExpressionValidationError("at least one source ticker is required")

    _validate_expression(expression)

    long_df = query_series_long(con, src)
    if long_df.empty:
        raise ExpressionValidationError("selected source tickers have no data")

    pivot = long_df.pivot_table(index="date", columns="ticker", values="value", aggfunc="last").sort_index()
    required = [t for t in src if t in pivot.columns]
    if not required:
        raise ExpressionValidationError("no aligned source columns")

    calc = pivot[required].dropna(how="any").copy()
    if calc.empty:
        raise ExpressionValidationError("source intersection is empty")

    aliases: dict[str, pd.Series] = {}
    for i, tk in enumerate(required, start=1):
        aliases[f"S{i}"] = calc[tk]
        aliases[_sanitize_var_name(tk)] = calc[tk]

    tree = ast.parse(expression.strip(), mode="eval")
    result = _eval_node(tree, aliases)
    out = pd.DataFrame({"date": calc.index, "value": pd.Series(result, index=calc.index)})
    out = out.replace([float("inf"), float("-inf")], pd.NA).dropna(subset=["value"]).reset_index(drop=True)
    return out


def _load_recipe_map(con) -> dict[str, Recipe]:
    df = list_derived_recipes(con)
    out: dict[str, Recipe] = {}
    if df.empty:
        return out
    for _, row in df.iterrows():
        ticker = str(row.get("derived_ticker") or "").strip().upper()
        if not ticker:
            continue
        try:
            src = json.loads(row.get("source_tickers_json") or "[]")
        except Exception:
            src = []
        out[ticker] = Recipe(
            derived_ticker=ticker,
            source_tickers=[str(x).strip() for x in src if str(x).strip()],
            expression=str(row.get("expression") or "").strip(),
        )
    return out


def recompute_recipe_graph(con, target_ticker: str) -> list[dict]:
    """Recompute target recipe with both upstream dependencies and downstream dependents."""
    target = (target_ticker or "").strip().upper()
    if not target:
        raise ValueError("target_ticker is required")

    recipe_map = _load_recipe_map(con)
    if target not in recipe_map:
        raise ValueError(f"recipe not found: {target}")

    upstream_order: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(tk: str):
        if tk in visited:
            return
        if tk in visiting:
            raise ValueError(f"cycle detected at {tk}")
        visiting.add(tk)
        recipe = recipe_map.get(tk)
        if recipe:
            for src in recipe.source_tickers:
                src_u = src.upper()
                if src_u in recipe_map:
                    dfs(src_u)
            upstream_order.append(tk)
        visiting.remove(tk)
        visited.add(tk)

    dfs(target)

    # collect downstream dependents so updating a base recipe can propagate to children recipes
    reverse_deps: dict[str, set[str]] = {}
    for recipe_ticker, recipe in recipe_map.items():
        for src in recipe.source_tickers:
            src_u = str(src).strip().upper()
            reverse_deps.setdefault(src_u, set()).add(recipe_ticker)

    downstream: set[str] = set()
    stack = [target]
    while stack:
        curr = stack.pop()
        for child in reverse_deps.get(curr, set()):
            if child not in downstream:
                downstream.add(child)
                stack.append(child)

    nodes = set(upstream_order) | downstream

    # topological order on selected nodes
    final_order: list[str] = []
    visiting2: set[str] = set()
    visited2: set[str] = set()

    def topo(node: str):
        if node in visited2:
            return
        if node in visiting2:
            raise ValueError(f"cycle detected at {node}")
        visiting2.add(node)
        recipe = recipe_map.get(node)
        if recipe:
            for src in recipe.source_tickers:
                src_u = str(src).strip().upper()
                if src_u in nodes:
                    topo(src_u)
            final_order.append(node)
        visiting2.remove(node)
        visited2.add(node)

    for node in sorted(nodes):
        topo(node)

    results: list[dict] = []
    for tk in final_order:
        recipe = recipe_map[tk]
        calc = evaluate_recipe(con, recipe.source_tickers, recipe.expression)
        rows = upsert_derived_daily(con, tk, calc[["date", "value"]])
        results.append({"ticker": tk, "rows": rows, "status": "success"})
    return results
