# app/pages/5_StrategiesBacktest.py
"""
Strategies & Backtest Page
提供策略参数化、运行回测并展示结果（图表、指标、交易清单）
"""

import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import t, render_language_switcher, init_language
from core.backtest import SimpleBacktester
from core.db import default_db_path, get_conn, list_instruments, query_prices_long
from core.strategy_examples import rsi_mean_reversion_signals, sma_crossover_signals

init_language()

st.set_page_config(page_title="Commodity Lab - Strategies & Backtest", layout="wide")
render_language_switcher()

st.title(f"🎯 {t('strategies')}")

con = get_conn(default_db_path(workspace_root))
instruments_df = list_instruments(con)
available_tickers = instruments_df["ticker"].tolist() if not instruments_df.empty else []

with st.sidebar:
    st.header("Backtest Controls")
    strategy = st.selectbox("Strategy", ["SMA Crossover", "RSI Mean Reversion"])
    capital = st.number_input("Initial Capital", value=100000.0, step=1000.0)
    position_size_pct = st.slider("Position Size (% of equity)", 0.01, 1.0, 0.95)
    cost_per_trade = st.number_input("Transaction Cost (pct)", value=0.001)
    slippage = st.number_input("Slippage (fraction)", value=0.0)
    fixed_fee = st.number_input("Fixed fee per trade", value=0.0)
    max_position_value = st.number_input("Max position value (0 = no limit)", value=0.0)
    selected_tickers = st.multiselect(
        "Tickers (from DB)",
        options=available_tickers,
        default=(available_tickers[:1] if available_tickers else []),
    )
    start = st.date_input("Start date", value=pd.Timestamp.today().date() - timedelta(days=365))
    end = st.date_input("End date", value=pd.Timestamp.today().date())

with st.expander("🧭 Backtest Guide / 回测说明", expanded=False):
    st.markdown(
        """
- 先选 1~3 个标的测试流程，再扩展到组合回测。
- 建议开启交易成本与滑点，避免过度乐观结果。
- 如果权益曲线为空，请检查日期范围和本地数据是否已刷新。
        """
    )

st.info("Configure strategy parameters and run backtest")

eq = None
metrics = {}
trades: list[dict] = []

if st.button("Run Backtest"):
    if not selected_tickers:
        st.warning("请选择至少一个标的（Tickers）以运行回测")
    else:
        results = []
        for tk in selected_tickers:
            px_df = query_prices_long(con, [tk], start=start, end=end, field="close")
            if px_df.empty:
                st.warning(f"未找到 {tk} 的历史价格，跳过")
                continue

            px_df = px_df.rename(columns={"value": "close"})[["date", "close"]]
            if strategy == "SMA Crossover":
                signals_df = sma_crossover_signals(px_df, short=20, long=50)
            else:
                signals_df = rsi_mean_reversion_signals(px_df, window=14)

            max_pos = None if max_position_value == 0 else float(max_position_value)
            bt = SimpleBacktester(prices_df=px_df, signals_df=signals_df, capital=float(capital))
            r = bt.run(
                position_size_pct=float(position_size_pct),
                cost_per_trade=float(cost_per_trade),
                slippage=float(slippage),
                fixed_fee=float(fixed_fee),
                max_position_value=max_pos,
            )
            results.append((tk, r))

        if not results:
            st.error("没有可用回测结果")
        else:
            merged = None
            for tk, r in results:
                curve = r.get("equity_curve")
                if curve is None:
                    continue
                curve = curve.rename(columns={"equity": f"equity_{tk}"})
                if merged is None:
                    merged = curve
                else:
                    merged = pd.merge(merged, curve, on="date", how="outer")

            merged = merged.sort_values("date").ffill().fillna(0)
            eq_cols = [c for c in merged.columns if c.startswith("equity_")]
            merged["equity"] = merged[eq_cols].sum(axis=1)
            eq = merged[["date", "equity"]]

            metrics = {tk: r.get("metrics") for tk, r in results}
            trades = []
            for tk, r in results:
                tlist = r.get("trades") or []
                for tr in tlist:
                    try:
                        tr_dict = tr.__dict__.copy()
                        tr_dict["ticker"] = tk
                        trades.append(tr_dict)
                    except Exception:
                        trades.append({**tr, "ticker": tk})

    st.subheader("Equity Curve")
    if eq is not None:
        fig = px.line(eq, x="date", y="equity", title="Equity Curve")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Performance Metrics")
    if metrics:
        st.json(metrics)

    st.subheader("Trades")
    if trades:
        st.dataframe(pd.DataFrame(trades), width="stretch")

try:
    con.close()
except Exception:
    pass
