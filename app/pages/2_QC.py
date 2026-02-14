import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

from core.db import (
    default_db_path,
    get_conn,
    init_db,
    list_instruments,
    query_prices_long,
)
from core.qc import run_qc_report, summarize_qc_reports

st.set_page_config(page_title="Commodity Lab - QC", layout="wide")
st.title("QC - 数据质量检查（Step 2）")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = default_db_path(PROJECT_ROOT)

con = get_conn(DB_PATH)
init_db(con)

st.markdown("""
这一页展示**数据质量控制（QC）**检查，包括：
- 缺失值、重复、异常值检查
- 单位/币种校验
- 数据对齐与业务日历
- 数据新鲜度监控
""")

# Sidebar controls
with st.sidebar:
    st.header("QC 设置")
    instruments = list_instruments(con)
    
    if not instruments.empty:
        selected_tickers = st.multiselect(
            "选择关注序列",
            instruments["ticker"].tolist(),
            default=instruments["ticker"].tolist()[:5]
        )
    else:
        selected_tickers = []
        st.warning("没有找到任何关注序列，请先在 Data 页面添加。")
    
    st.divider()
    st.header("QC 参数")
    zscore_threshold = st.slider("离群值阈值（z-score）", 1.0, 5.0, 3.0, 0.5)
    missing_threshold = st.slider("缺失值阈值（%）", 0.0, 50.0, 5.0, 1.0)
    max_bday_gap = st.slider("最大业务日间隔（天）", 1, 30, 10, 1)


# Run QC checks
if selected_tickers:
    st.header("📊 QC 报告")
    
    tab1, tab2, tab3 = st.tabs(["总览", "详细检查", "数据视图"])
    
    with tab1:
        st.subheader("QC 检查摘要")
        
        reports = []
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(selected_tickers):
            # Query price data
            prices = query_prices_long(con, [ticker], field="close")
            
            if not prices.empty:
                # Rename columns for QC
                df = prices[["date", "ticker"]].copy()
                df["close"] = prices["value"]
                
                # Run QC report
                report = run_qc_report(df, ticker)
                reports.append(report)
            
            progress_bar.progress((i + 1) / len(selected_tickers))
        
        # Summarize reports
        if reports:
            summary_df = summarize_qc_reports(reports)
            
            # Color code status
            def status_color(status):
                return "🟢 PASSED" if status == "PASSED" else "🔴 FAILED"
            
            summary_df["状态"] = summary_df["status"].apply(status_color)
            
            display_cols = ["ticker", "状态", "missing_values", "duplicates", "outliers", "staleness_days", "missing_bdays"]
            st.dataframe(summary_df[display_cols].style.highlight_max(axis=0), use_container_width=True)
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                passed = (summary_df["status"] == "PASSED").sum()
                st.metric("✅ 通过", f"{passed}/{len(summary_df)}")
            
            with col2:
                total_missing = summary_df["missing_values"].sum()
                st.metric("❌ 缺失值", total_missing)
            
            with col3:
                total_dupes = summary_df["duplicates"].sum()
                st.metric("⚠️ 重复", total_dupes)
            
            with col4:
                total_outliers = summary_df["outliers"].sum()
                st.metric("📈 异常值", total_outliers)
    
    with tab2:
        st.subheader("详细 QC 检查")
        
        selected_ticker = st.selectbox("选择序列查看详细信息", selected_tickers)
        
        prices = query_prices_long(con, [selected_ticker], field="close")
        
        if not prices.empty:
            df = prices[["date", "ticker"]].copy()
            df["close"] = prices["value"]
            
            report = run_qc_report(df, selected_ticker)
            
            # Display detailed checks
            st.json(report)
    
    with tab3:
        st.subheader("数据视图")
        
        ticker = st.selectbox("选择序列", selected_tickers, key="data_view_ticker")
        
        prices = query_prices_long(con, [ticker], field="close")
        
        if not prices.empty:
            st.dataframe(prices.tail(20), use_container_width=True)
            
            st.line_chart(
                prices.rename(columns={"value": "Price"}).set_index("date"),
                use_container_width=True
            )
else:
    st.info("请先在 Data 页面添加并关注一些序列")

