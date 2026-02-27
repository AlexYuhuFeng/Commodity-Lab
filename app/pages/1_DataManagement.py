from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
from core.db import (
    default_db_path,
    delete_instruments,
    get_conn,
    get_last_price_date,
    init_db,
    list_instruments,
    list_refresh_log,
    log_refresh,
    set_watch,
    upsert_instruments,
    upsert_prices_daily,
)
from core.refresh import refresh_many
from core.yf_provider import normalize_search_results, search_yahoo

init_language()
st.set_page_config(page_title="Commodity Lab - Data Management", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title(f"📊 {t('data_management')}")

con = get_conn(default_db_path(workspace_root))
init_db(con)

with st.expander(l("Refresh settings", "刷新设置"), expanded=False):
    first_period = st.selectbox(l("Initial download period", "首次下载周期"), ["max", "10y", "5y", "2y", "1y"], index=0)
    backfill_days = st.slider(l("Backfill days", "回补天数"), 0, 30, 7, 1)
    synthetic_backfill_days = st.slider(l("Synthetic series backfill days", "合成序列回补天数"), 0, 30, 7, 1)

    watched = list_instruments(con, only_watched=True)
    if st.button(l("Refresh all watched", "刷新全部关注"), type="primary", width="stretch"):
        tickers = watched["ticker"].tolist() if not watched.empty else []
        if not tickers:
            st.warning(l("No watched tickers.", "暂无已关注代码。"))
        else:
            results = refresh_many(con, tickers, first_period, backfill_days, synthetic_backfill_days)
            ok = sum(1 for r in results if r.get("status") == "success")
            st.success(l(f"Refresh done: {ok}/{len(results)} success", f"刷新完成：{ok}/{len(results)} 成功"))


search_tab, local_tab, upload_tab, log_tab = st.tabs([
    l("🔍 Search", "🔍 搜索"),
    l("📁 Local", "📁 本地"),
    l("⤴️ CSV Upload", "⤴️ CSV上传"),
    l("📋 Refresh Log", "📋 刷新日志"),
])

with search_tab:
    query = st.text_input(l("Keywords", "关键词"), placeholder="Brent / TTF / HH / EURUSD")
    max_results = st.slider(l("Max results", "最大结果数"), 5, 50, 15)
    if query:
        try:
            rows = normalize_search_results(search_yahoo(query))[:max_results]
            for idx, r in enumerate(rows):
                ticker = r.get("ticker") or r.get("symbol")
                if not ticker:
                    continue
                with st.container(border=True):
                    st.write(f"**{ticker}** - {r.get('name','')}")
                    c1, c2 = st.columns([1, 1])
                    c1.caption(f"{r.get('exchange','')} / {r.get('currency','')}")
                    if c2.button(l("Watch", "关注"), key=f"watch_{ticker}_{idx}"):
                        upsert_instruments(con, pd.DataFrame([{
                            "ticker": ticker,
                            "name": r.get("name", ticker),
                            "quote_type": r.get("quote_type", ""),
                            "exchange": r.get("exchange", ""),
                            "currency": r.get("currency", ""),
                            "category": "commodity",
                        }]))
                        set_watch(con, [ticker], True)
                        st.success(l("Added to watchlist", "已加入关注"))
                        st.rerun()
        except Exception as e:
            st.error(str(e))

with local_tab:
    inst = list_instruments(con, only_watched=False)
    watched = inst[inst["is_watched"] == True] if not inst.empty else pd.DataFrame()
    st.subheader(l("Watched tickers", "已关注代码"))
    if watched.empty:
        st.info(l("No watched tickers.", "暂无已关注代码。"))
    else:
        st.dataframe(watched[["ticker", "name", "exchange", "currency", "unit"]], width="stretch", hide_index=True)

        pick = st.multiselect(l("Select tickers", "选择代码"), watched["ticker"].tolist())
        c1, c2 = st.columns(2)
        if c1.button(l("Unwatch selected (hard delete)", "取消关注选中（彻底删除）"), disabled=not pick):
            delete_instruments(con, pick, delete_prices=True)
            st.success(l("Deleted from watchlist and storage.", "已取消关注并彻底删除。"))
            st.rerun()
        if c2.button(l("Delete selected (with prices)", "删除选中（含价格）"), disabled=not pick):
            delete_instruments(con, pick, delete_prices=True)
            st.success(l("Deleted.", "已删除。"))
            st.rerun()

        stats = []
        for tk in watched["ticker"].tolist():
            last = get_last_price_date(con, tk)
            stale = None if last is None else (date.today() - last).days
            stats.append({"ticker": tk, "last_date": last, "staleness_days": stale})
        st.dataframe(pd.DataFrame(stats), width="stretch", hide_index=True)

with upload_tab:
    st.markdown(l("Upload CSV to create/update a raw series. Required columns: `date`, `close`; optional: `open,high,low,adj_close,volume`.", "上传CSV创建/更新原始序列。必需列：`date`,`close`；可选：`open,high,low,adj_close,volume`。"))
    ticker = st.text_input(l("Target raw ticker", "目标raw代码"), placeholder="TTF_MANUAL")
    name = st.text_input(l("Display name", "显示名称"), value="Manual Uploaded Series")
    file = st.file_uploader("CSV", type=["csv"])
    if file is not None and st.button(l("Import CSV", "导入CSV"), type="primary"):
        try:
            df = pd.read_csv(file)
            req = {"date", "close"}
            if not req.issubset(df.columns):
                st.error(l("CSV must include date and close columns.", "CSV必须包含date和close列。"))
            else:
                df["date"] = pd.to_datetime(df["date"]).dt.date
                for c in ["open", "high", "low", "adj_close", "volume"]:
                    if c not in df.columns:
                        df[c] = pd.NA
                tk = (ticker or "").strip().upper()
                if not tk:
                    st.error(l("Ticker is required.", "代码不能为空。"))
                else:
                    upsert_instruments(con, pd.DataFrame([{
                        "ticker": tk,
                        "name": name or tk,
                        "quote_type": "manual",
                        "exchange": "local",
                        "currency": "",
                        "category": "commodity",
                        "source": "csv_upload",
                    }]))
                    set_watch(con, [tk], True)
                    n = upsert_prices_daily(con, tk, df)
                    log_refresh(con, tk, "success", f"csv upload rows={n}", df["date"].max())
                    st.success(l(f"Imported {n} rows into {tk}.", f"已导入 {n} 行到 {tk}。"))
        except Exception as e:
            st.error(str(e))

with log_tab:
    logs = list_refresh_log(con)
    st.dataframe(logs, width="stretch", hide_index=True) if not logs.empty else st.info(l("No logs.", "暂无日志。"))
