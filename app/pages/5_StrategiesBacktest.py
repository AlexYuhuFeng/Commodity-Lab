from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
from core.backtest import SimpleBacktester
from core.db import default_db_path, get_conn, list_instruments, query_prices_long
from core.strategy_examples import rsi_mean_reversion_signals, sma_crossover_signals

init_language()
st.set_page_config(page_title="Commodity Lab - Strategies & Backtest", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title(f"🎯 {t('strategies')}")
st.caption(l("All controls are on the main page for faster workflow.", "所有控制项已移到主页面，便于操作。"))

con = get_conn(default_db_path(workspace_root))
instruments_df = list_instruments(con, only_watched=True)
available_tickers = instruments_df["ticker"].tolist() if not instruments_df.empty else []

c1, c2, c3, c4 = st.columns(4)
strategy = c1.selectbox(l("Strategy", "策略"), ["SMA Crossover", "RSI Mean Reversion"])
capital = c2.number_input(l("Initial Capital", "初始资金"), value=100000.0, step=1000.0)
position_size_pct = c3.slider(l("Position Size (% equity)", "仓位比例（权益%）"), 0.01, 1.0, 0.95)
cost_per_trade = c4.number_input(l("Transaction Cost (pct)", "交易成本（比例）"), value=0.001)

c5, c6, c7, c8 = st.columns(4)
slippage = c5.number_input(l("Slippage", "滑点"), value=0.0)
fixed_fee = c6.number_input(l("Fixed fee per trade", "每笔固定费用"), value=0.0)
max_position_value = c7.number_input(l("Max position value (0=unlimited)", "最大仓位金额（0=不限制）"), value=0.0)
selected_tickers = c8.multiselect(l("Tickers", "标的"), options=available_tickers, default=available_tickers[:1] if available_tickers else [])

c9, c10 = st.columns(2)
start = c9.date_input(l("Start date", "开始日期"), value=pd.Timestamp.today().date() - timedelta(days=365))
end = c10.date_input(l("End date", "结束日期"), value=pd.Timestamp.today().date())

if st.button(l("Run Backtest", "运行回测"), type="primary"):
    if not selected_tickers:
        st.warning(l("Please select at least one ticker.", "请至少选择一个标的。"))
    else:
        results = []
        for tk in selected_tickers:
            px_df = query_prices_long(con, [tk], start=start, end=end, field="close")
            if px_df.empty:
                st.warning(l(f"No data for {tk}", f"{tk} 无数据"))
                continue
            px_df = px_df.rename(columns={"value": "close"})[["date", "close"]]
            signals_df = sma_crossover_signals(px_df, short=20, long=50) if strategy == "SMA Crossover" else rsi_mean_reversion_signals(px_df, window=14)
            bt = SimpleBacktester(prices_df=px_df, signals_df=signals_df, capital=float(capital))
            run = bt.run(
                position_size_pct=float(position_size_pct),
                cost_per_trade=float(cost_per_trade),
                slippage=float(slippage),
                fixed_fee=float(fixed_fee),
                max_position_value=None if max_position_value == 0 else float(max_position_value),
            )
            results.append((tk, run))

        if not results:
            st.error(l("No valid backtest result.", "没有有效回测结果。"))
        else:
            merged = None
            trade_rows = []
            metric_rows = []
            for tk, run in results:
                eq = run.get("equity_curve")
                if eq is not None:
                    eq = eq.rename(columns={"equity": f"equity_{tk}"})
                    merged = eq if merged is None else pd.merge(merged, eq, on="date", how="outer")
                metric_rows.append({"ticker": tk, **(run.get("metrics") or {})})
                for tr in (run.get("trades") or []):
                    item = tr.__dict__.copy() if hasattr(tr, "__dict__") else dict(tr)
                    item["ticker"] = tk
                    trade_rows.append(item)

            merged = merged.sort_values("date").ffill().fillna(0)
            eq_cols = [c for c in merged.columns if c.startswith("equity_")]
            merged["equity"] = merged[eq_cols].sum(axis=1)

            st.plotly_chart(px.line(merged, x="date", y="equity", title=l("Portfolio Equity", "组合权益曲线")), width="stretch")
            st.subheader(l("Metrics", "指标"))
            st.dataframe(pd.DataFrame(metric_rows), width="stretch", hide_index=True)
            st.subheader(l("Trades", "成交明细"))
            st.dataframe(pd.DataFrame(trade_rows), width="stretch", hide_index=True)


st.divider()
st.subheader(l("Risk Control Stress Test", "风控压力测试"))
rc1, rc2, rc3 = st.columns(3)
rc_ticker = rc1.selectbox(l("Risk test ticker", "风控测试标的"), options=available_tickers, index=0 if available_tickers else None)
rc_window = rc2.number_input(l("Consecutive days", "连续天数"), min_value=2, max_value=60, value=10)
rc_drop = rc3.number_input(l("Cumulative drop threshold (%)", "累计跌幅阈值(%)"), min_value=0.1, max_value=50.0, value=2.0)

if st.button(l("Run Risk Test", "运行风控测试"), disabled=not available_tickers):
    pxf = query_prices_long(con, [rc_ticker], start=start, end=end, field="close")
    if pxf.empty:
        st.warning(l("No data for selected ticker.", "所选标的无数据。"))
    else:
        pxf = pxf.sort_values("date").copy()
        pxf["roll_return"] = pxf["value"] / pxf["value"].shift(int(rc_window)) - 1
        pxf["breach"] = pxf["roll_return"] <= (-float(rc_drop) / 100.0)
        breaches = pxf[pxf["breach"]].copy()
        worst = float(pxf["roll_return"].min()) if pxf["roll_return"].notna().any() else 0.0

        m1, m2, m3 = st.columns(3)
        m1.metric(l("Worst rolling return", "最差滚动收益"), f"{worst*100:.2f}%")
        m2.metric(l("Breach count", "触发次数"), int(len(breaches)))
        m3.metric(l("Threshold", "阈值"), f"-{float(rc_drop):.2f}% / {int(rc_window)}d")

        st.plotly_chart(
            px.line(pxf, x="date", y="roll_return", title=l("Rolling cumulative return", "滚动累计收益")),
            width="stretch",
        )
        st.dataframe(breaches[["date", "value", "roll_return"]].tail(200), width="stretch", hide_index=True)
