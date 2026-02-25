# app/pages/5_StrategiesBacktest.py
"""
Strategies & Backtest Page
提供策略参数化、运行回测并展示结果（图表、指标、交易清单）
"""

import sys
from pathlib import Path

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

from app.i18n import t, render_language_switcher, init_language
from core.strategy_examples import sma_crossover_signals, rsi_mean_reversion_signals
from core.backtest import SimpleBacktester

init_language()

st.set_page_config(page_title="Commodity Lab - Strategies & Backtest", layout="wide")
render_language_switcher()

st.title(f"🎯 {t('strategies')}")

with st.sidebar:
	st.header(t("backtest_controls") if t("backtest_controls") else "Backtest Controls")
	strategy = st.selectbox("Strategy", ["SMA Crossover", "RSI Mean Reversion"])
	capital = st.number_input("Initial Capital", value=100000.0, step=1000.0)
	position_size_pct = st.slider("Position Size (% of equity)", 0.01, 1.0, 0.95)
	cost_per_trade = st.number_input("Transaction Cost (pct)", value=0.001)
	slippage = st.number_input("Slippage (fraction)", value=0.0)
	fixed_fee = st.number_input("Fixed fee per trade", value=0.0)
	max_position_value = st.number_input("Max position value (0 = no limit)", value=0.0)
	start = st.date_input("Start date", value=pd.Timestamp.today().date() - timedelta(days=365))
	end = st.date_input("End date", value=pd.Timestamp.today().date())

st.info(t("backtest_info") if t("backtest_info") else "Configure strategy parameters and run backtest")

if st.button("Run Backtest"):
	# For demo use synthetic prices; in production allow ticker selection
	dates = pd.date_range(start=start, end=end, freq="D")
	rng = pd.np.random.default_rng(seed=42)
	prices = 100 + rng.normal(0, 1, len(dates)).cumsum()
	prices_df = pd.DataFrame({"date": dates, "close": prices})

	if strategy == "SMA Crossover":
		signals_df = sma_crossover_signals(prices_df, short=20, long=50)
	else:
		signals_df = rsi_mean_reversion_signals(prices_df, window=14)

	max_pos = None if max_position_value == 0 else float(max_position_value)

	bt = SimpleBacktester(prices_df=prices_df, signals_df=signals_df, capital=float(capital))
	result = bt.run(
		position_size_pct=float(position_size_pct),
		cost_per_trade=float(cost_per_trade),
		slippage=float(slippage),
		fixed_fee=float(fixed_fee),
		max_position_value=max_pos,
	)

	eq = result.get("equity_curve")
	metrics = result.get("metrics")
	trades = result.get("trades")

	st.subheader("Equity Curve")
	if eq is not None:
		fig = px.line(eq, x="date", y="equity", title="Equity Curve")
		st.plotly_chart(fig, use_container_width=True)

	st.subheader("Performance Metrics")
	if metrics:
		st.json(metrics)

	st.subheader("Trades")
	if trades:
		try:
			trades_df = pd.DataFrame([t.__dict__ for t in trades])
		except Exception:
			trades_df = pd.DataFrame(trades)
		st.dataframe(trades_df)
