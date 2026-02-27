from __future__ import annotations

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
    get_conn,
    init_db,
    list_instruments,
    query_derived_long,
    query_prices_long,
    upsert_derived_daily,
    upsert_instruments,
)

init_language()
st.set_page_config(page_title="Commodity Lab - Derived Management", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title(l("🔗 Derived Management", "🔗 派生序列管理"))
st.caption(l("Create/edit spread-derived tickers as first-class series.", "将价差序列作为一等派生序列创建与管理。"))

con = get_conn(default_db_path(workspace_root))
init_db(con)
inst = list_instruments(con, only_watched=False)
all_tickers = sorted(inst["ticker"].dropna().astype(str).tolist()) if not inst.empty else []

if len(all_tickers) < 2:
    st.warning(l("Need at least two local tickers.", "至少需要两个本地代码。"))
    st.stop()

c1, c2, c3 = st.columns(3)
left = c1.selectbox(l("Left ticker", "左侧代码"), all_tickers)
right = c2.selectbox(l("Right ticker", "右侧代码"), all_tickers, index=1 if len(all_tickers) > 1 else 0)
formula = c3.selectbox(l("Formula", "公式"), ["L-R", "L/R", "(L-R)/R"])

m1, m2 = st.columns(2)
lm = m1.number_input(l("Left multiplier", "左侧倍率"), value=1.0, step=0.1)
rm = m2.number_input(l("Right multiplier", "右侧倍率"), value=1.0, step=0.1)

name_default = f"SPREAD_{left}_{right}_{formula.replace('/','DIV').replace('-','MINUS')}"
out_name = st.text_input(l("Derived ticker name", "派生代码名"), value=name_default)

# load both sides raw first then derived fallback
left_raw = query_prices_long(con, [left], field="close")
if left_raw.empty:
    left_raw = query_derived_long(con, [left])
right_raw = query_prices_long(con, [right], field="close")
if right_raw.empty:
    right_raw = query_derived_long(con, [right])

if left_raw.empty or right_raw.empty:
    st.error(l("Selected pair has missing data.", "选择的序列有一侧无数据。"))
    st.stop()

ldf = left_raw[["date", "value"]].rename(columns={"value": "L"})
rdf = right_raw[["date", "value"]].rename(columns={"value": "R"})
merged = pd.merge(ldf, rdf, on="date", how="inner").dropna().sort_values("date")
if merged.empty:
    st.error(l("No overlapping dates between selected series.", "所选序列没有重叠日期。"))
    st.stop()
merged["L"] = merged["L"] * float(lm)
merged["R"] = merged["R"] * float(rm)

if formula == "L-R":
    merged["value"] = merged["L"] - merged["R"]
elif formula == "L/R":
    merged["value"] = merged["L"] / merged["R"].replace(0, pd.NA)
else:
    merged["value"] = (merged["L"] - merged["R"]) / merged["R"].replace(0, pd.NA)

merged = merged.dropna(subset=["value"])
if merged.empty:
    st.error(l("Formula produced empty result (check divide-by-zero).", "计算结果为空（请检查除零问题）。"))
    st.stop()

st.plotly_chart(px.line(merged, x="date", y="value", title=l("Derived spread preview", "派生价差预览")), width="stretch")
st.dataframe(merged[["date", "L", "R", "value"]].tail(250), width="stretch", hide_index=True)

if st.button(l("Save derived series", "保存派生序列"), type="primary"):
    save = (out_name or "").strip().upper()
    if not save:
        st.error(l("Derived name required.", "派生名不能为空。"))
    else:
        rows = upsert_derived_daily(con, save, merged[["date", "value"]])
        upsert_instruments(con, pd.DataFrame([{
            "ticker": save,
            "name": save,
            "quote_type": "derived",
            "exchange": "local",
            "currency": "",
            "unit": "",
            "category": "spread",
            "source": "derived_management",
        }]))
        con.execute("UPDATE instruments SET is_watched=TRUE WHERE ticker=?", [save])
        st.success(l(f"Saved {rows} rows -> {save}", f"已保存 {rows} 行 -> {save}"))
        st.rerun()
