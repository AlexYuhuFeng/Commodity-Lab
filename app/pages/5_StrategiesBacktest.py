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
from core.db import get_conn, default_db_path, list_instruments, query_prices_long
from pathlib import Path

init_language()

st.set_page_config(page_title="Commodity Lab - Strategies & Backtest", layout="wide")
render_language_switcher()

st.title(f"🎯 {t('strategies')}")

con = get_conn(default_db_path(Path(workspace_root)))
instruments_df = list_instruments(con)
available_tickers = instruments_df["ticker"].tolist() if not instruments_df.empty else []

with st.sidebar:
	st.header(t("backtest_controls") if t("backtest_controls") else "Backtest Controls")
	strategy = st.selectbox("Strategy", ["SMA Crossover", "RSI Mean Reversion"])
	capital = st.number_input("Initial Capital", value=100000.0, step=1000.0)
	position_size_pct = st.slider("Position Size (% of equity)", 0.01, 1.0, 0.95)
	cost_per_trade = st.number_input("Transaction Cost (pct)", value=0.001)
	slippage = st.number_input("Slippage (fraction)", value=0.0)
	fixed_fee = st.number_input("Fixed fee per trade", value=0.0)
	max_position_value = st.number_input("Max position value (0 = no limit)", value=0.0)
	selected_tickers = st.multiselect("Tickers (from DB)", options=available_tickers, default=(available_tickers[:1] if available_tickers else []))
	start = st.date_input("Start date", value=pd.Timestamp.today().date() - timedelta(days=365))
	end = st.date_input("End date", value=pd.Timestamp.today().date())

st.info(t("backtest_info") if t("backtest_info") else "Configure strategy parameters and run backtest")

if st.button("Run Backtest"):
	# For demo use synthetic prices; in production allow ticker selection
	if not selected_tickers:
		st.warning("请选择至少一个标的（Tickers）以运行回测")
	else:
		results = []
		for tk in selected_tickers:
			# fetch prices from DB
			px = query_prices_long(con, [tk], start=start, end=end, field="value")
			# query_prices_long returns columns date,ticker,value; rename value to close
			if px.empty:
				st.warning(f"未找到 {tk} 的历史价格，跳过")
				continue
			px = px.rename(columns={"value": "close"})[["date", "close"]]
			if strategy == "SMA Crossover":
				signals_df = sma_crossover_signals(px, short=20, long=50)
			else:
				signals_df = rsi_mean_reversion_signals(px, window=14)

			max_pos = None if max_position_value == 0 else float(max_position_value)
			bt = SimpleBacktester(prices_df=px, signals_df=signals_df, capital=float(capital))
			r = bt.run(
				position_size_pct=float(position_size_pct),
				cost_per_trade=float(cost_per_trade),
				slippage=float(slippage),
				fixed_fee=float(fixed_fee),
				max_position_value=max_pos,
			)
			results.append((tk, r))

		# aggregate equity curves by date (sum equities across tickers)
		if not results:
			st.error("没有可用回测结果")
		else:
			# build DataFrame merged on date
			merged = None
			for tk, r in results:
				eq = r.get("equity_curve")
				if eq is None:
					continue
				eq = eq.rename(columns={"equity": f"equity_{tk}"})
				if merged is None:
					merged = eq
				else:
					merged = pd.merge(merged, eq, on="date", how="outer")
			merged = merged.sort_values("date").fillna(method="ffill").fillna(0)
			# sum equity columns
			eq_cols = [c for c in merged.columns if c.startswith("equity_")]
			merged["equity"] = merged[eq_cols].sum(axis=1)
			eq = merged[["date", "equity"]]
			metrics = {tk: r.get("metrics") for tk, r in results}
			trades = []
			for tk, r in results:
				tlist = r.get("trades") or []
				# annotate trades with ticker
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
		st.plotly_chart(fig, use_container_width=True)

	st.subheader("Performance Metrics")
	if metrics:
		st.json(metrics)

	st.subheader("Trades")
	if trades:
		trades_df = pd.DataFrame(trades)
		st.dataframe(trades_df)

	# close DB connection
	try:
		con.close()
	except Exception:
		pass
