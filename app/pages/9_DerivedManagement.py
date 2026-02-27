from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher
from core.db import (
    default_db_path,
    delete_derived_recipe,
    delete_instruments,
    get_conn,
    init_db,
    list_derived_recipes,
    list_instruments,
    query_series_long,
    upsert_derived_daily,
    upsert_derived_recipe,
    upsert_instruments,
)
from core.derived_engine import (
    ExpressionValidationError,
    evaluate_recipe,
    recompute_recipe_graph,
)

init_language()
st.set_page_config(page_title="Commodity Lab - Derived Management", layout="wide")
render_language_switcher()
lang = get_language()


def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en


def _var_name(ticker: str) -> str:
    out = re.sub(r"[^0-9A-Za-z_]", "_", str(ticker).strip())
    if out and out[0].isdigit():
        out = f"T_{out}"
    return out or "T"


def _compute_expression(con, source_tickers: list[str], expression: str) -> pd.DataFrame:
    src = [str(t).strip() for t in source_tickers if str(t).strip()]
    if not src:
        raise ValueError("请选择至少一个源序列")

    long_df = query_series_long(con, src)
    if long_df.empty:
        raise ValueError("所选源序列没有可用数据")

    pivot = long_df.pivot_table(index="date", columns="ticker", values="value", aggfunc="last").sort_index()
    required = [t for t in src if t in pivot.columns]
    if not required:
        raise ValueError("源序列对齐后无有效列")
    calc = pivot[required].dropna(how="any").copy()
    if calc.empty:
        raise ValueError("源序列日期交集为空，请调整源序列")

    aliases = {}
    for i, tk in enumerate(required, start=1):
        aliases[f"S{i}"] = calc[tk]
        aliases[_var_name(tk)] = calc[tk]

    try:
        result = pd.eval((expression or "").strip(), local_dict=aliases, engine="numexpr")
    except Exception as exc:
        raise ValueError(f"表达式计算失败: {exc}") from exc

    out = pd.DataFrame({"date": calc.index, "value": pd.Series(result, index=calc.index)})
    out = out.replace([float("inf"), float("-inf")], pd.NA).dropna(subset=["value"]).reset_index(drop=True)
    return out


st.title(l("🔗 Derived Management", "🔗 派生序列管理"))
st.caption(l(
    "Derived and raw tickers are equal citizens here. Build derived from any mix using expression-based formulas.",
    "在这里，派生与原始序列完全平等。可基于任意混合序列使用表达式构建派生序列。",
))

con = get_conn(default_db_path(workspace_root))
init_db(con)
inst = list_instruments(con, only_watched=False)
all_tickers = sorted(inst["ticker"].dropna().astype(str).tolist()) if not inst.empty else []

st.subheader(l("Create / Update Derived", "创建 / 更新派生序列"))
regex = st.text_input(l("Regex filter for source tickers", "源序列正则筛选"), value="")
if regex:
    try:
        pat = re.compile(regex)
        filtered = [x for x in all_tickers if pat.search(x)]
        st.caption(l(f"Regex matched {len(filtered)} tickers", f"正则匹配到 {len(filtered)} 个代码"))
    except re.error as exc:
        filtered = all_tickers
        st.warning(l(f"Invalid regex: {exc}", f"正则无效: {exc}"))
else:
    filtered = all_tickers

sources = st.multiselect(
    l("Source tickers (raw or derived)", "源序列（raw 或 derived）"),
    options=filtered,
    default=filtered[:2] if len(filtered) >= 2 else filtered,
)

if sources:
    example = " + ".join([f"S{i+1}" for i in range(len(sources))])
    st.caption(l(
        f"Available aliases: {', '.join([f'S{i+1}' for i in range(len(sources))])}. You can also use sanitized ticker names.",
        f"可用别名: {', '.join([f'S{i+1}' for i in range(len(sources))])}。也可直接使用处理后的ticker变量名。",
    ))
else:
    example = "S1 - S2"

expression = st.text_input(
    l("Expression", "表达式"),
    value=example,
    help=l("Supports + - * / and parentheses. Example: (S1*0.29307107)/S2", "支持 + - * / 与括号。示例: (S1*0.29307107)/S2"),
)
out_name = st.text_input(l("Derived ticker", "派生代码"), value="DERIVED_EXAMPLE")

preview_df = pd.DataFrame()
if st.button(l("Preview expression", "预览表达式"), type="secondary"):
    try:
        preview_df = _compute_expression(con, sources, expression)
        st.success(l(f"Preview rows: {len(preview_df)}", f"预览完成，行数: {len(preview_df)}"))
    except Exception as exc:
        st.error(str(exc))

if not preview_df.empty:
    st.plotly_chart(px.line(preview_df, x="date", y="value", title=l("Preview", "预览")), width="stretch")
    st.dataframe(preview_df.tail(200), width="stretch", hide_index=True)

if st.button(l("Save Derived", "保存派生序列"), type="primary"):
    save = (out_name or "").strip().upper()
    if not save:
        st.error(l("Derived ticker is required", "派生代码不能为空"))
    else:
        try:
            calc_df = _compute_expression(con, sources, expression)
            rows = upsert_derived_daily(con, save, calc_df[["date", "value"]])
            upsert_derived_recipe(con, save, sources, expression)
            upsert_instruments(
                con,
                pd.DataFrame([
                    {
                        "ticker": save,
                        "name": save,
                        "quote_type": "derived",
                        "exchange": "local",
                        "currency": "",
                        "unit": "",
                        "category": "derived",
                        "source": "derived_management",
                    }
                ]),
            )
            con.execute("UPDATE instruments SET is_watched=TRUE WHERE ticker=?", [save])
            st.success(l(f"Saved {rows} rows -> {save}", f"已保存 {rows} 行 -> {save}"))
        except Exception as exc:
            st.error(str(exc))

st.divider()
st.subheader(l("Existing Derived Recipes", "已保存派生配方"))
recipes = list_derived_recipes(con)
if recipes.empty:
    st.info(l("No derived recipes yet.", "暂无派生配方。"))
else:
    for _, row in recipes.iterrows():
        dt = row.get("derived_ticker")
        expr = row.get("expression") or ""
        try:
            src = json.loads(row.get("source_tickers_json") or "[]")
        except Exception:
            src = []

        with st.expander(f"🔧 {dt}"):
            st.code(expr, language="text")
            st.caption(l(f"Sources: {', '.join(src)}", f"源序列: {', '.join(src)}"))
            c1, c2 = st.columns(2)
            if c1.button(l("Recompute", "重算"), key=f"recompute_{dt}"):
                try:
                    calc_df = _compute_expression(con, src, expr)
                    rows = upsert_derived_daily(con, dt, calc_df[["date", "value"]])
                    st.success(l(f"Recomputed {dt}: {rows} rows", f"重算完成 {dt}: {rows} 行"))
                except Exception as exc:
                    st.error(str(exc))
            if c2.button(l("Delete derived", "删除派生"), key=f"delete_{dt}"):
                delete_derived_recipe(con, dt)
                delete_instruments(con, [dt], delete_prices=False)
                st.success(l(f"Deleted {dt}", f"已删除 {dt}"))
                st.rerun()
