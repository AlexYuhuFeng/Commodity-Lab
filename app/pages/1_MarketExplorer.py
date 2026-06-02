from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
from core.data_source import available_sources, fetch_price_history, search_market
from core.db import (
    default_db_path,
    get_conn,
    init_db,
    get_last_price_date,
    list_instruments,
    log_refresh,
    upsert_instruments,
    upsert_prices_daily,
)
from core.refresh import refresh_one

init_language()
st.set_page_config(page_title="Hedge Lab - Market Explorer", layout="wide")
render_language_switcher()
lang = get_language()


def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title("📈 Market Explorer")
st.caption(l("Discover contracts and load real market history from Yahoo Finance or Platts.", "从 Yahoo Finance 或 Platts 发现合约并加载真实历史数据。"))

con = get_conn(default_db_path(workspace_root))
init_db(con)

source = st.selectbox(l("Data source", "数据来源"), options=available_sources(), index=0)
search_col, refresh_col = st.columns([3, 1])
with search_col:
    query = st.text_input(l("Search contract", "搜索合约"), placeholder="Brent, HH, TTF, CL")
with refresh_col:
    refresh_days = st.number_input(l("Refresh lookback days", "刷新回看天数"), min_value=0, max_value=30, value=7, step=1)

st.divider()
search_results = []
if query:
    try:
        search_results = search_market(query, source=source, max_results=20)
    except Exception as exc:
        st.error(str(exc))

if search_results:
    st.subheader(l("Search results", "搜索结果"))
    for idx, row in enumerate(search_results):
        ticker = row.get("ticker") or row.get("symbol")
        if not ticker:
            continue
        with st.container():
            cols = st.columns([2, 1, 1])
            cols[0].markdown(f"**{ticker}**  {row.get('name', '')}")
            cols[1].caption(f"{row.get('exchange', '')} / {row.get('currency', '')}")
            if cols[2].button(l("Watch & load", "关注并加载"), key=f"watch_{source}_{ticker}_{idx}"):
                instrument = pd.DataFrame([
                    {
                        "ticker": ticker,
                        "name": row.get("name", ticker),
                        "quote_type": row.get("quote_type", "commodity"),
                        "exchange": row.get("exchange", source.upper()),
                        "currency": row.get("currency", "USD"),
                        "category": "commodity",
                        "source": source,
                    }
                ])
                upsert_instruments(con, instrument)
                prices = fetch_price_history(ticker, source=source, period_if_no_start="5y")
                if not prices.empty:
                    upsert_prices_daily(con, ticker, prices)
                    log_refresh(con, ticker, "success", f"Loaded {len(prices)} rows from {source}", prices["date"].max())
                    st.success(l(f"{ticker} is now watched and price history has been loaded.", f"{ticker} 已关注并加载历史价格。"))
                else:
                    st.warning(l("No history was returned for this contract.", "该合约未返回历史数据。"))
                st.experimental_rerun()

st.divider()

st.subheader(l("Watchlist & refresh", "关注列表与刷新"))
instruments = list_instruments(con, only_watched=True)
if instruments.empty:
    st.info(l("No watched instruments yet. Search to add contracts.", "暂无关注合约。请搜索添加。"))
else:
    table_data = []
    for _, inst in instruments.iterrows():
        last_date = get_last_price_date(con, inst["ticker"])
        table_data.append(
            {
                "Ticker": inst["ticker"],
                "Name": inst["name"],
                "Source": inst["source"],
                "Exchange": inst["exchange"],
                "Currency": inst["currency"],
                "Last price date": last_date,
            }
        )
    st.dataframe(pd.DataFrame(table_data), width="stretch", hide_index=True)

    selected = st.multiselect(l("Refresh selected tickers", "刷新选定合约"), options=instruments["ticker"].tolist())
    if st.button(l("Refresh historical data", "刷新历史数据"), type="primary"):
        if not selected:
            st.warning(l("Select at least one ticker first.", "请先选择至少一个合约。"))
        else:
            for tk in selected:
                source_for_tk = instruments.loc[instruments["ticker"] == tk, "source"].iloc[0] if tk in instruments["ticker"].values else source
                result = refresh_one(con, tk, source=source_for_tk, first_period="5y", backfill_days=int(refresh_days), derived_backfill_days=0)
                if result["status"] == "success":
                    st.success(l(f"Refreshed {tk}", f"已刷新 {tk}"))
                else:
                    st.warning(l(f"Failed to refresh {tk}: {result['message']}", f"刷新 {tk} 失败：{result['message']}"))
            st.experimental_rerun()

try:
    con.close()
except Exception:
    pass
