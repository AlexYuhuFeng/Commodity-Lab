# app/pages/2_DataShowcase.py
"""
Data Showcase Page
Complete data display with tabs: Overview, Price Chart, QC, Properties, Derived, Operations
Inspired by broker stock detail pages
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Add the workspace root to the Python path so core module can be imported
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from core.db import (
    default_db_path,
    get_conn,
    init_db,
    list_instruments,
    query_prices_long,
    query_derived_long,
    list_transforms,
    upsert_transform,
    delete_transform,
)
from core.qc import run_qc_report, summarize_qc_reports
from core.transforms import recompute_transform
from app.i18n import t, render_language_switcher, init_language

init_language()

st.set_page_config(page_title="Commodity Lab - Data Showcase", layout="wide")
render_language_switcher()

st.title(f"🔍 {t('data_showcase.title')}")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = default_db_path(PROJECT_ROOT)

con = get_conn(DB_PATH)
init_db(con)


# ===== TOP: TICKER SELECTOR =====
inst = list_instruments(con, only_watched=True)
if inst.empty:
    st.warning("暂无已关注的产品。请先在数据管理页面关注产品。")
    st.stop()

sel_col1, sel_col2 = st.columns([3, 2])
ticker_options = inst["ticker"].tolist()
selected_ticker = sel_col1.selectbox(
    "选择产品",
    ticker_options,
    format_func=lambda x: f"{x} - {inst[inst['ticker']==x]['name'].iloc[0] if inst[inst['ticker']==x]['name'].iloc[0] else x}",
)
sel_col2.caption("衍生序列编辑、价差创建已集中到“派生管理”页签。")


# ===== GET DATA FOR SELECTED TICKER =====
ticker_info = inst[inst["ticker"] == selected_ticker].iloc[0]

# Get price data
prices = query_prices_long(con, [selected_ticker], field="close")
if prices.empty:
    st.error(f"❌ 未找到 {selected_ticker} 的价格数据")
    st.stop()

# Get derived series
transforms = list_transforms(con, enabled_only=False)
derived_tickers = transforms[transforms["base_ticker"] == selected_ticker]["derived_ticker"].tolist() if not transforms.empty else []

derived_data = {}
if derived_tickers:
    derived_df = query_derived_long(con, derived_tickers)
    if not derived_df.empty:
        for dt in derived_tickers:
            derived_data[dt] = derived_df[derived_df["ticker"] == dt].copy()


# ===== MAIN CONTENT WITH TABS =====
tabs = st.tabs([
    f"{t('data_showcase.tabs.overview')} 📊",
    f"{t('data_showcase.tabs.price_chart')} 📈",
    f"{t('data_showcase.tabs.qc_report')} ✓",
    f"{t('data_showcase.tabs.properties')} 🏷️",
    f"{t('data_showcase.tabs.derived')} 🔗",
    f"{t('data_showcase.tabs.operations')} ⚙️",
])


# ===== TAB 0: OVERVIEW =====
with tab_overview:
    st.subheader(f"产品概览 - {selected_ticker}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            st.metric(
                "产品代码",
                selected_ticker,
            )
    
    with col2:
        with st.container(border=True):
            if not prices.empty:
                latest_price = prices.iloc[-1]["value"]
                st.metric(
                    "最新价格",
                    f"{latest_price:.4f}" if latest_price else "N/A",
                )
    
    with col3:
        with st.container(border=True):
            if not prices.empty:
                latest_date = prices.iloc[-1]["date"].date()
                st.metric(
                    "最后更新",
                    str(latest_date),
                )
    
    with col4:
        with st.container(border=True):
            exchange = ticker_info.get("exchange", "N/A")
            st.metric(
                "交易所",
                exchange,
            )
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            currency = ticker_info.get("currency", "N/A")
            st.metric("货币", currency)
    
    with col2:
        with st.container(border=True):
            unit = ticker_info.get("unit", "N/A")
            st.metric("单位", unit)
    
    with col3:
        with st.container(border=True):
            category = ticker_info.get("category", "N/A")
            st.metric("类别", category)
    
    with col4:
        with st.container(border=True):
            if not prices.empty:
                total_rows = len(prices)
                st.metric("数据行数", total_rows)
    
    # Price statistics
    st.subheader("价格统计")
    
    if not prices.empty:
        price_values = prices["value"].dropna()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("最高价", f"{price_values.max():.4f}")
        with col2:
            st.metric("最低价", f"{price_values.min():.4f}")
        with col3:
            st.metric("平均价", f"{price_values.mean():.4f}")
        with col4:
            st.metric("标准差", f"{price_values.std():.4f}")
        with col5:
            st.metric("波动率", f"{(price_values.std() / price_values.mean() * 100):.2f}%")


# ===== TAB 1: PRICE CHART =====
with tab_price:
    st.subheader(f"价格走势 - {selected_ticker}")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期",
            value=min(prices["date"]).date() if not prices.empty else date.today()
        )
    with col2:
        end_date = st.date_input(
            "结束日期",
            value=max(prices["date"]).date() if not prices.empty else date.today()
        )
    
    # Filter data by date range
    mask = (prices["date"] >= pd.Timestamp(start_date)) & (prices["date"] <= pd.Timestamp(end_date))
    filtered_prices = prices[mask].copy()
    
    if filtered_prices.empty:
        st.warning("所选日期范围内无数据")
    else:
        # Create chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=filtered_prices["date"],
            y=filtered_prices["value"],
            mode='lines',
            name=selected_ticker,
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)',
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>价格: %{y:.4f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"{selected_ticker} 价格历程",
            xaxis_title="日期",
            yaxis_title="价格",
            hovermode='x unified',
            template="plotly_white",
            height=500,
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Statistics for selected period
        st.subheader("选定期间统计")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        price_values = filtered_prices["value"].dropna()
        
        with col1:
            st.metric("期间高点", f"{price_values.max():.4f}")
        with col2:
            st.metric("期间低点", f"{price_values.min():.4f}")
        with col3:
            change = price_values.iloc[-1] - price_values.iloc[0]
            pct_change = (change / price_values.iloc[0] * 100) if price_values.iloc[0] != 0 else 0
            st.metric("变化", f"{change:.4f}", f"{pct_change:+.2f}%")
        with col4:
            st.metric("平均价", f"{price_values.mean():.4f}")
        with col5:
            st.metric("波动率", f"{(price_values.std() / price_values.mean() * 100):.2f}%")


# ===== TAB 2: QC REPORT =====
with tab_qc:
    st.subheader(f"数据质量检查 - {selected_ticker}")
    
    # QC parameters
    col1, col2 = st.columns(2)
    with col1:
        zscore_threshold = st.slider("Z分数阈值", 1.0, 5.0, 3.0, 0.5)
    with col2:
        missing_threshold = st.slider("缺失值阈值 (%)", 0.0, 50.0, 5.0, 1.0)
    
    # Run QC
    try:
        df_qc = prices[["date", "ticker"]].copy()
        df_qc["close"] = prices["value"]
        
        report = run_qc_report(df_qc, selected_ticker)
        
        # Display QC results
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            missing_pct = (report.get("missing_values", 0) / len(prices) * 100) if len(prices) > 0 else 0
            color = "🟢" if missing_pct < missing_threshold else "🔴"
            st.metric(f"{color} 缺失值", f"{report.get('missing_values', 0)} ({missing_pct:.2f}%)")
        
        with col2:
            st.metric("🟢 重复值" if report.get("duplicates", 0) == 0 else "🔴 重复值", report.get("duplicates", 0))
        
        with col3:
            outliers = report.get("outliers", 0)
            color = "🟢" if outliers == 0 else "🔴"
            st.metric(f"{color} 异常值 (Z>3)", outliers)
        
        with col4:
            staleness = report.get("staleness_days", 0)
            color = "🟢" if staleness <= 1 else "🟡" if staleness <= 7 else "🔴"
            st.metric(f"{color} 陈旧度 (天)", staleness)
        
        with col5:
            missing_bdays = report.get("missing_bdays", 0)
            color = "🟢" if missing_bdays == 0 else "🟡" if missing_bdays < 5 else "🔴"
            st.metric(f"{color} 缺失业务日", missing_bdays)
        
        # QC status
        st.divider()
        
        issues = []
        if missing_pct > missing_threshold:
            issues.append(f"缺失值过高: {missing_pct:.2f}% > {missing_threshold:.2f}%")
        if report.get("duplicates", 0) > 0:
            issues.append(f"发现 {report['duplicates']} 个重复值")
        if report.get("outliers", 0) > 0:
            issues.append(f"发现 {report['outliers']} 个异常值 (Z > {zscore_threshold})")
        if report.get("staleness_days", 0) > 1:
            issues.append(f"数据已陈旧 {report['staleness_days']} 天")
        
        if issues:
            st.warning("🚨 发现以下问题:")
            for issue in issues:
                st.write(f"• {issue}")
        else:
            st.success("✅ 数据质量良好！")
    
    except Exception as e:
        st.error(f"QC检查出错: {str(e)}")


# ===== TAB 3: PROPERTIES =====
with tab_properties:
    st.subheader(f"产品属性 - {selected_ticker}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("**基本信息**")
            st.write(f"**代码**: {ticker_info.get('ticker', 'N/A')}")
            st.write(f"**名称**: {ticker_info.get('name', 'N/A')}")
            st.write(f"**类型**: {ticker_info.get('quote_type', 'N/A')}")
            st.write(f"**来源**: {ticker_info.get('source', 'N/A')}")
            st.write(f"**创建时间**: {ticker_info.get('created_at', 'N/A')}")
            st.write(f"**更新时间**: {ticker_info.get('updated_at', 'N/A')}")
    
    with col2:
        with st.container(border=True):
            st.markdown("**标准化信息**")
            st.write(f"**货币**: {ticker_info.get('currency', 'N/A')}")
            st.write(f"**单位**: {ticker_info.get('unit', 'N/A')}")
            st.write(f"**交易所**: {ticker_info.get('exchange', 'N/A')}")
            st.write(f"**分类**: {ticker_info.get('category', 'N/A')}")
    
    # Edit properties section
    st.divider()
    st.subheader("编辑属性")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        new_currency = st.text_input(
            "货币",
            value=ticker_info.get("currency", ""),
            key="edit_currency"
        )
    
    with col2:
        new_unit = st.text_input(
            "单位",
            value=ticker_info.get("unit", ""),
            key="edit_unit"
        )
    
    with col3:
        new_category = st.text_input(
            "分类",
            value=ticker_info.get("category", ""),
            key="edit_category"
        )
    
    with col4:
        if st.button("💾 保存属性", width='stretch'):
            from core.db import update_instrument_meta
            
            try:
                meta_df = pd.DataFrame([{
                    "ticker": selected_ticker,
                    "currency": new_currency,
                    "unit": new_unit,
                    "category": new_category,
                }])
                
                update_instrument_meta(con, meta_df)
                st.success("✅ 属性已保存")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 保存失败: {str(e)}")


# ===== TAB 4: DERIVED SERIES =====
with tab_derived:
    st.subheader(f"派生序列 - {selected_ticker}")
    
    # Show existing derived series
    if derived_tickers:
        st.markdown("**已创建的派生序列**")
        
        for derived_ticker in derived_tickers:
            with st.expander(f"📊 {derived_ticker}"):
                # Get transform details
                tf = transforms[transforms["derived_ticker"] == derived_ticker].iloc[0] if not transforms.empty else None
                
                if tf is not None:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**基础**: {tf.get('base_ticker', 'N/A')}")
                    with col2:
                        st.write(f"**汇率**: {tf.get('fx_ticker', 'N/A') if tf.get('fx_ticker') else '无'}")
                    with col3:
                        st.write(f"**操作**: {tf.get('fx_op', 'mul')}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"**目标货币**: {tf.get('target_currency', 'N/A')}")
                    with col2:
                        st.write(f"**目标单位**: {tf.get('target_unit', 'N/A')}")
                    with col3:
                        st.write(f"**乘数**: {tf.get('multiplier', 1.0)}")
                    with col4:
                        st.write(f"**除数**: {tf.get('divider', 1.0)}")
                    
                    # Show chart if data exists
                    if derived_ticker in derived_data and not derived_data[derived_ticker].empty:
                        fig = px.line(
                            derived_data[derived_ticker],
                            x="date",
                            y="value",
                            title=f"{derived_ticker} 走势",
                            labels={"value": "值", "date": "日期"},
                        )
                        st.plotly_chart(fig, width='stretch')
                    
                    # Actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"🔄 重算 {derived_ticker}", key=f"recompute_{derived_ticker}"):
                            try:
                                with st.spinner("重算中..."):
                                    recompute_transform(con, tf.get("transform_id"))
                                st.success(f"✅ {derived_ticker} 已重算")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 重算失败: {str(e)}")
                    
                    with col2:
                        st.caption("编辑请在下方“派生管理”页签进行")
                    
                    with col3:
                        if st.button(f"🗑️ 删除 {derived_ticker}", key=f"delete_{derived_ticker}"):
                            try:
                                delete_transform(con, tf.get("transform_id"), delete_derived=True)
                                st.success(f"✅ {derived_ticker} 已删除")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 删除失败: {str(e)}")
    else:
        st.info("暂无派生序列")
    
    st.divider()
    st.info("新建/编辑派生序列请使用左侧 Data Workspace 下的『Derived Management』页面。")


# ===== TAB 5: DERIVED STUDIO =====
with tabs[5]:
    st.subheader(f"派生管理 - {selected_ticker}")
    st.caption("支持基于两条序列创建 spread 作为派生序列，便于监控与回测复用。")

    all_inst = list_instruments(con, only_watched=False)
    all_tickers = sorted(all_inst["ticker"].dropna().astype(str).tolist()) if not all_inst.empty else []

    c1, c2, c3 = st.columns(3)
    spread_left = c1.selectbox("左侧序列", all_tickers, index=0 if all_tickers else None, key="ds_left")
    spread_right = c2.selectbox("右侧序列", all_tickers, index=1 if len(all_tickers) > 1 else 0, key="ds_right")
    spread_mode = c3.selectbox("公式", ["L-R", "L/R", "(L-R)/R"], key="ds_mode")

    m1, m2 = st.columns(2)
    left_mult = m1.number_input("左侧倍率", value=1.0, step=0.1, key="ds_lm")
    right_mult = m2.number_input("右侧倍率", value=1.0, step=0.1, key="ds_rm")

    out_name = st.text_input("派生代码", value=f"SPREAD_{selected_ticker}")

    if st.button("💾 保存Spread派生序列", type="primary", width='stretch'):
        if not spread_left or not spread_right:
            st.error("请选择左右序列")
        else:
            l_raw = query_prices_long(con, [spread_left], field="close")
            if l_raw.empty:
                l_raw = query_derived_long(con, [spread_left])
            r_raw = query_prices_long(con, [spread_right], field="close")
            if r_raw.empty:
                r_raw = query_derived_long(con, [spread_right])

            if l_raw.empty or r_raw.empty:
                st.error("左右序列有一侧没有数据")
            else:
                ldf = l_raw[["date", "value"]].rename(columns={"value": "L"})
                rdf = r_raw[["date", "value"]].rename(columns={"value": "R"})
                mm = pd.merge(ldf, rdf, on="date", how="inner").dropna().sort_values("date")
                mm["L"] = mm["L"] * float(left_mult)
                mm["R"] = mm["R"] * float(right_mult)
                if spread_mode == "L-R":
                    mm["value"] = mm["L"] - mm["R"]
                elif spread_mode == "L/R":
                    mm["value"] = mm["L"] / mm["R"]
                else:
                    mm["value"] = (mm["L"] - mm["R"]) / mm["R"]
                save_name = (out_name or "").strip().upper()
                if not save_name:
                    st.error("派生代码不能为空")
                else:
                    from core.db import upsert_derived_daily, upsert_instruments
                    rows = upsert_derived_daily(con, save_name, mm[["date", "value"]])
                    upsert_instruments(con, pd.DataFrame([{"ticker": save_name, "name": save_name, "quote_type": "derived", "exchange": "local", "currency": "", "unit": "", "category": "spread", "source": "derived_studio"}]))
                    st.success(f"已保存 {rows} 行至 {save_name}")
                    st.line_chart(mm.set_index("date")["value"])

# ===== TAB 6: OPERATIONS =====
with tabs[6]:
    st.subheader(f"操作 - {selected_ticker}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**数据操作**")
        
        if st.button("🔄 立即刷新", width='stretch'):
            from core.refresh import refresh_many
            try:
                with st.spinner(f"刷新 {selected_ticker} 中..."):
                    results = refresh_many(con, [selected_ticker], first_period="10y", backfill_days=7)
                    if results[0]["status"] == "success":
                        st.success(f"✅ 已刷新 {results[0]['rows']} 行")
                        st.rerun()
                    else:
                        st.error(f"❌ 刷新失败")
            except Exception as e:
                st.error(f"❌ 错误: {str(e)}")
        
        if st.button("📥 导出数据", width='stretch'):
            csv = prices.to_csv(index=False)
            st.download_button(
                label="下载 CSV",
                data=csv,
                file_name=f"{selected_ticker}_prices.csv",
                mime="text/csv"
            )
    
    with col2:
        st.markdown("**关注管理**")
        
        from core.db import set_watch
        
        is_watched = ticker_info.get("is_watched", False)
        
        if is_watched:
            if st.button("⭐ 取消关注", width='stretch'):
                set_watch(con, [selected_ticker], False)
                st.success(f"已取消关注 {selected_ticker}")
                st.rerun()
        else:
            if st.button("⭐ 加入关注", width='stretch'):
                set_watch(con, [selected_ticker], True)
                st.success(f"已关注 {selected_ticker}")
                st.rerun()

