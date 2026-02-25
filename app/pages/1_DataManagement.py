# app/pages/1_DataManagement.py
"""
Data Management Page
Integrated search, import, and management of commodity data
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import timedelta, date
import pandas as pd
import streamlit as st
from datetime import datetime

# Add the workspace root to the Python path so core module can be imported
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from core.db import (
    default_db_path,
    get_conn,
    init_db,
    list_instruments,
    set_watch,
    get_last_price_date,
    upsert_prices_daily,
    log_refresh,
    list_refresh_log,
    upsert_instruments,
)
from core.yf_provider import search_yahoo, normalize_search_results
from core.yf_prices import fetch_history_daily
from core.refresh import refresh_many
from app.i18n import t, render_language_switcher, init_language

init_language()

st.set_page_config(page_title="Commodity Lab - Data Management", layout="wide")
render_language_switcher()

st.title(f"📊 {t('data_management')}")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = default_db_path(PROJECT_ROOT)

con = get_conn(DB_PATH)
init_db(con)


# ===== SIDEBAR CONTROLS =====
def download_and_upsert_one(tk: str, first_period: str, backfill_days: int) -> dict:
    """Download and upsert single ticker with backfill"""
    tk = (tk or "").strip()
    last_dt = get_last_price_date(con, tk)

    try:
        if last_dt is None:
            px = fetch_history_daily(tk, start=None, period_if_no_start=first_period)
        else:
            start = last_dt - timedelta(days=int(backfill_days))
            px = fetch_history_daily(tk, start=start, period_if_no_start=first_period)

        if px is None or px.empty:
            log_refresh(con, tk, status="empty", message="no data returned", last_success_date=last_dt)
            return {"ticker": tk, "status": "empty", "rows": 0, "last": last_dt}

        n = upsert_prices_daily(con, tk, px)
        last_success = px["date"].max() if "date" in px.columns and not px.empty else last_dt

        if n > 0:
            log_refresh(con, tk, status="success", message=f"upserted {n} rows", last_success_date=last_success)
            return {"ticker": tk, "status": "success", "rows": n, "last": last_success}
        else:
            log_refresh(con, tk, status="empty", message="no new rows", last_success_date=last_success)
            return {"ticker": tk, "status": "empty", "rows": 0, "last": last_success}

    except Exception as e:
        log_refresh(con, tk, status="error", message=str(e), last_success_date=last_dt)
        return {"ticker": tk, "status": "error", "rows": 0, "last": last_dt}


with st.sidebar:
    st.header("⚙️ " + t("refresh_settings"))
    
    col1, col2 = st.columns(2)
    with col1:
        first_period = st.selectbox(
            t("first_download_period"),
            ["max", "10y", "5y", "2y", "1y"],
            index=0
        )
    with col2:
        backfill_days = st.slider(t("backfill_days"), 0, 30, 7, 1)
    
    derived_backfill_days = st.slider(t("backfill_derived"), 0, 30, 7, 1)
    auto_download = st.checkbox(t("auto_download"), value=True)
    
    st.divider()
    
    inst = list_instruments(con, only_watched=False)
    watched = inst[inst["is_watched"] == True]["ticker"].tolist() if not inst.empty else []
    
    if st.button(f"🔄 {t('refresh_all')}", type="primary", use_container_width=True):
        if not watched:
            st.warning("暂无已关注的产品。请先在下方搜索并关注。")
        else:
            with st.spinner("刷新中..."):
                results = refresh_many(
                    con,
                    watched,
                    first_period=first_period,
                    backfill_days=backfill_days,
                    derived_backfill_days=derived_backfill_days,
                )
                ok = sum(1 for r in results if r["status"] == "success")
                st.success(f"✅ 刷新完成：{ok}/{len(results)} 成功")


# ===== MAIN CONTENT =====
# Create tabs for Search and Local Data
tab_search, tab_local, tab_logs = st.tabs(["🔍 搜索", "📁 本地数据", "📋 刷新日志"])

# ===== TAB 1: SEARCH =====
with tab_search:
    st.subheader(t("search") + " - Yahoo Finance")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            t("keywords"),
            placeholder="e.g., Brent, Natural Gas, TTF, EURUSD",
            key="search_input"
        )
    with col2:
        max_results = st.slider("数量", 5, 100, 20, 5)
    
    search_results = []
    if search_query:
        with st.spinner("搜索中..."):
            try:
                results = search_yahoo(search_query)
                search_results = normalize_search_results(results)
            except Exception as e:
                st.error(f"搜索出错: {str(e)}")
    
    if search_results:
        st.write(f"找到 {len(search_results)} 个结果")
        
        # Display in dataframe format with pagination
        df_results = pd.DataFrame([
            {
                "产品名称": r.get("shortname", r.get("symbol", "")),
                "代码": r.get("symbol", ""),
                "类型": r.get("quoteType", ""),
                "交易所": r.get("exchange", ""),
                "货币": r.get("currency", ""),
                "操作": "view"
            }
            for r in search_results[:max_results]
        ])
        
        st.dataframe(
            df_results,
            use_container_width=True,
            hide_index=True,
            column_config={
                "操作": st.column_config.SelectboxColumn(
                    options=["view"],
                    width="small"
                )
            }
        )
        
        # Detail view
        st.subheader("⭐ 产品详情")
        
        cols = st.columns(min(3, len(search_results)))
        for idx, result in enumerate(search_results[:max_results]):
            with cols[idx % len(cols)]:
                with st.container(border=True):
                    ticker = result.get("symbol", "N/A")
                    name = result.get("shortname", ticker)
                    quote_type = result.get("quoteType", "")
                    exchange = result.get("exchange", "")
                    currency = result.get("currency", "")
                    
                    st.write(f"**{name}**")
                    st.caption(f"代码: {ticker}")
                    
                    info = f"**类型**: {quote_type}\n\n**交易所**: {exchange}\n\n**货币**: {currency}"
                    st.markdown(info)
                    
                    # Check if already watched
                    is_watched = not inst.empty and ticker in inst[inst["is_watched"] == True]["ticker"].values
                    
                    if is_watched:
                        st.success("✅ 已关注")
                    else:
                        if st.button("➕ 添加关注", key=f"add_{ticker}", use_container_width=True):
                            # Add to instruments and optionally download
                            try:
                                upsert_instruments(
                                    con,
                                    pd.DataFrame([
                                        {
                                            "ticker": ticker,
                                            "name": name,
                                            "quote_type": quote_type,
                                            "exchange": exchange,
                                            "currency": currency,
                                            "category": "commodity",
                                        }
                                    ])
                                )
                                set_watch(con, [ticker], True)
                                
                                # Auto download if enabled
                                if auto_download:
                                    with st.spinner(f"下载 {ticker} 数据中..."):
                                        result = download_and_upsert_one(ticker, first_period, backfill_days)
                                        if result["status"] == "success":
                                            st.success(f"✅ {result['rows']} 行数据已导入")
                                        elif result["status"] == "empty":
                                            st.warning("⚠️ 未获得数据")
                                        else:
                                            st.error(f"❌ 下载失败")
                                
                                st.rerun()
                            except Exception as e:
                                st.error(f"操作失败: {str(e)}")


# ===== TAB 2: LOCAL DATA =====
with tab_local:
    st.subheader(t("local_data"))
    
    inst = list_instruments(con, only_watched=False)
    
    if inst.empty:
        st.info(t("no_local_data"))
    else:
        watched_inst = inst[inst["is_watched"] == True]
        
        if watched_inst.empty:
            st.info("暂无已关注的产品")
        else:
            # Display watched instruments with stats
            display_cols = ["ticker", "name", "exchange", "currency", "unit", "is_watched"]
            df_display = watched_inst[display_cols].copy()
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ticker": st.column_config.TextColumn("代码"),
                    "name": st.column_config.TextColumn("产品名称"),
                    "exchange": st.column_config.TextColumn("交易所"),
                    "currency": st.column_config.TextColumn("货币"),
                    "unit": st.column_config.TextColumn("单位"),
                    "is_watched": st.column_config.CheckboxColumn("已关注"),
                }
            )
            
            st.divider()
            st.subheader("📊 数据统计")
            
            # Get price stats for watched instruments
            stats_rows = []
            for _, row in watched_inst.iterrows():
                ticker = row["ticker"]
                last_date = get_last_price_date(con, ticker)
                
                if last_date:
                    today = date.today()
                    staleness = (today - last_date).days
                    stats_rows.append({
                        "代码": ticker,
                        "最后更新": last_date,
                        "陈旧度(天)": staleness,
                        "状态": "✅ 最新" if staleness <= 1 else f"⚠️ {staleness}天未更新"
                    })
                else:
                    stats_rows.append({
                        "代码": ticker,
                        "最后更新": "无",
                        "陈旧度(天)": "-",
                        "状态": "❌ 无数据"
                    })
            
            if stats_rows:
                st.dataframe(
                    pd.DataFrame(stats_rows),
                    use_container_width=True,
                    hide_index=True
                )


# ===== TAB 3: REFRESH LOG =====
with tab_logs:
    st.subheader(t("refresh_log"))
    
    refresh_log = list_refresh_log(con)
    
    if refresh_log.empty:
        st.info("暂无刷新日志")
    else:
        # Format display
        display_cols = ["ticker", "status", "message", "last_success_date", "last_attempt_at"]
        available_cols = [c for c in display_cols if c in refresh_log.columns]
        
        df_display = refresh_log[available_cols].copy()
        df_display.columns = ["代码", "状态", "信息", "最后成功日期", "最后尝试时间"]
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
