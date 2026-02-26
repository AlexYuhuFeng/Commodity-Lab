from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
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
st.set_page_config(page_title="Commodity Lab - Analytics", layout="wide")
render_language_switcher()

lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title(f"📊 {t('analytics')}")
st.caption(l("Compare raw/derived series and persist spreads as reusable derived series.", "比较原始/派生序列，并将价差保存为可复用派生序列。"))

con = get_conn(default_db_path(workspace_root))
init_db(con)
inst = list_instruments(con, only_watched=False)
raw_tickers = sorted(inst["ticker"].dropna().astype(str).tolist()) if not inst.empty else []
derived_df = con.execute("SELECT DISTINCT derived_ticker FROM derived_daily ORDER BY 1").df()
derived_tickers = derived_df["derived_ticker"].tolist() if not derived_df.empty else []

all_tickers = sorted(set(raw_tickers + derived_tickers))

colA, colB, colC = st.columns(3)
left_ticker = colA.selectbox(l("Left series", "左侧序列"), all_tickers, index=0 if all_tickers else None)
right_ticker = colB.selectbox(l("Right series", "右侧序列"), all_tickers, index=1 if len(all_tickers) > 1 else 0)

mode = colC.selectbox(
    l("Spread formula", "价差计算方式"),
    ["L-R", "L/R", "(L-R)/R"],
)

n1, n2 = st.columns(2)
left_mult = n1.number_input(l("Left multiplier", "左侧倍率"), value=1.0, step=0.1)
right_mult = n2.number_input(l("Right multiplier", "右侧倍率"), value=1.0, step=0.1)

if not all_tickers:
    st.warning(l("No data found. Please import data first.", "未找到可用数据，请先导入数据。"))
    st.stop()


def load_series(ticker: str) -> pd.DataFrame:
    raw = query_prices_long(con, [ticker], field="close")
    if not raw.empty:
        return raw[["date", "value"]].rename(columns={"value": ticker})
    der = query_derived_long(con, [ticker])
    if not der.empty:
        return der[["date", "value"]].rename(columns={"value": ticker})
    return pd.DataFrame(columns=["date", ticker])


left_df = load_series(left_ticker)
right_df = load_series(right_ticker)
if left_df.empty or right_df.empty:
    st.error(l("One side has no data in local DB.", "某一侧在本地数据库中无数据。"))
    st.stop()

merged = pd.merge(left_df, right_df, on="date", how="inner").dropna().sort_values("date")
merged["left_norm"] = merged[left_ticker] * float(left_mult)
merged["right_norm"] = merged[right_ticker] * float(right_mult)

if mode == "L-R":
    merged["spread"] = merged["left_norm"] - merged["right_norm"]
elif mode == "L/R":
    merged["spread"] = merged["left_norm"] / merged["right_norm"]
else:
    merged["spread"] = (merged["left_norm"] - merged["right_norm"]) / merged["right_norm"]

chart_df = merged[["date", "left_norm", "right_norm", "spread"]].copy()
fig = px.line(chart_df, x="date", y=["left_norm", "right_norm", "spread"], title=l("Comparison + spread", "对比与价差"))
st.plotly_chart(fig, width="stretch")

st.dataframe(chart_df.tail(200), width="stretch", hide_index=True)

st.subheader(l("Save spread as derived series", "将价差保存为派生序列"))
default_name = f"SPREAD_{left_ticker}_{right_ticker}_{mode.replace('/','DIV').replace('-','MINUS')}"
derived_name = st.text_input(l("Derived ticker", "派生代码"), value=default_name)
notes = st.text_area(l("Description", "描述"), value=f"{left_ticker} {mode} {right_ticker}; left_mult={left_mult}; right_mult={right_mult}")

if st.button(l("Save derived spread", "保存派生价差"), type="primary"):
    clean = (derived_name or "").strip().upper()
    if not clean:
        st.error(l("Derived ticker is required.", "派生代码不能为空。"))
    else:
        save_df = merged[["date", "spread"]].rename(columns={"spread": "value"})
        rows = upsert_derived_daily(con, clean, save_df)
        upsert_instruments(
            con,
            pd.DataFrame([
                {
                    "ticker": clean,
                    "name": clean,
                    "quote_type": "derived",
                    "exchange": "local",
                    "currency": "",
                    "unit": "",
                    "category": "spread",
                    "source": "analytics",
                }
            ]),
        )
        con.execute("UPDATE instruments SET is_watched=TRUE WHERE ticker=?", [clean])
        st.success(l(f"Saved {rows} rows to {clean}.", f"已保存 {rows} 行到 {clean}。"))
        if notes:
            st.caption(notes)
