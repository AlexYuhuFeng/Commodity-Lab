# app/pages/4_Analytics.py
"""Analytics workspace with spread comparison tools."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import init_language, render_language_switcher, t
from core.db import default_db_path, get_conn, init_db, list_instruments, query_prices_long

init_language()
st.set_page_config(page_title="Commodity Lab - Analytics", layout="wide")
render_language_switcher()

st.title(f"📊 {t('analytics.title')}")
st.caption(t("analytics.subtitle"))

project_root = Path(__file__).resolve().parents[2]
db_path = default_db_path(project_root)
con = get_conn(db_path)
init_db(con)

instruments = list_instruments(con, only_watched=True)
if instruments.shape[0] < 2:
    instruments = list_instruments(con, only_watched=False)

if instruments.shape[0] < 2:
    st.warning(t("analytics.need_two"))
    st.stop()

ticker_options = instruments["ticker"].dropna().unique().tolist()

st.markdown(f"### {t('analytics.spread_lab')}")

col_a, col_b, col_start, col_end = st.columns(4)
with col_a:
    ticker_a = st.selectbox(t("analytics.ticker_a"), ticker_options, index=0)
with col_b:
    default_b_idx = 1 if len(ticker_options) > 1 else 0
    ticker_b = st.selectbox(t("analytics.ticker_b"), ticker_options, index=default_b_idx)
with col_start:
    start_date = st.date_input(t("analytics.start_date"), value=pd.Timestamp.today().date() - pd.Timedelta(days=365))
with col_end:
    end_date = st.date_input(t("analytics.end_date"), value=pd.Timestamp.today().date())

ctl1, ctl2 = st.columns(2)
with ctl1:
    spread_mode = st.radio(
        t("analytics.mode"),
        options=["difference", "ratio"],
        horizontal=True,
        format_func=lambda x: t(f"analytics.{x}"),
    )
with ctl2:
    z_window = st.slider(t("analytics.z_window"), min_value=10, max_value=120, value=30, step=5)

if ticker_a == ticker_b:
    st.info("A/B 请选择不同产品。" if t("language.name") == "简体中文" else "Please choose two different instruments.")
    st.stop()

px = query_prices_long(
    con,
    [ticker_a, ticker_b],
    start=start_date,
    end=end_date,
    field="close",
)

if px.empty:
    st.warning(t("analytics.no_data"))
    st.stop()

pivot = px.pivot_table(index="date", columns="ticker", values="value", aggfunc="last").sort_index()
if ticker_a not in pivot.columns or ticker_b not in pivot.columns:
    st.warning(t("analytics.no_data"))
    st.stop()

pair = pivot[[ticker_a, ticker_b]].dropna().copy()
if pair.empty:
    st.warning(t("analytics.no_data"))
    st.stop()

if spread_mode == "difference":
    pair["spread"] = pair[ticker_a] - pair[ticker_b]
else:
    pair["spread"] = pair[ticker_a] / pair[ticker_b].replace(0, pd.NA)

pair["spread_mean"] = pair["spread"].rolling(z_window).mean()
pair["spread_std"] = pair["spread"].rolling(z_window).std()
pair["zscore"] = (pair["spread"] - pair["spread_mean"]) / pair["spread_std"]
pair["rolling_corr"] = pair[ticker_a].pct_change().rolling(z_window).corr(pair[ticker_b].pct_change())

last_spread = pair["spread"].dropna().iloc[-1] if pair["spread"].dropna().shape[0] else None
last_z = pair["zscore"].dropna().iloc[-1] if pair["zscore"].dropna().shape[0] else None
last_corr = pair["rolling_corr"].dropna().iloc[-1] if pair["rolling_corr"].dropna().shape[0] else None

m1, m2, m3 = st.columns(3)
m1.metric(t("analytics.latest_spread"), f"{last_spread:.4f}" if last_spread is not None else t("common.none"))
m2.metric(t("analytics.latest_zscore"), f"{last_z:.2f}" if last_z is not None else t("common.none"))
m3.metric(t("analytics.rolling_corr"), f"{last_corr:.3f}" if last_corr is not None else t("common.none"))

fig_price = go.Figure()
fig_price.add_trace(go.Scatter(x=pair.index, y=pair[ticker_a], name=ticker_a, mode="lines"))
fig_price.add_trace(go.Scatter(x=pair.index, y=pair[ticker_b], name=ticker_b, mode="lines"))
fig_price.update_layout(title=t("analytics.price_compare"), height=360)
st.plotly_chart(fig_price, width="stretch")

fig_spread = go.Figure()
fig_spread.add_trace(go.Scatter(x=pair.index, y=pair["spread"], name=t("analytics.spread_series"), mode="lines"))
fig_spread.update_layout(title=t("analytics.spread_series"), height=320)
st.plotly_chart(fig_spread, width="stretch")

fig_z = go.Figure()
fig_z.add_trace(go.Scatter(x=pair.index, y=pair["zscore"], name=t("analytics.zscore_series"), mode="lines"))
fig_z.add_hline(y=2.0, line_dash="dot", line_color="red")
fig_z.add_hline(y=0.0, line_dash="dash", line_color="gray")
fig_z.add_hline(y=-2.0, line_dash="dot", line_color="green")
fig_z.update_layout(title=t("analytics.zscore_series"), height=320)
st.plotly_chart(fig_z, width="stretch")

st.dataframe(
    pair[[ticker_a, ticker_b, "spread", "zscore", "rolling_corr"]].tail(120),
    width="stretch",
)
