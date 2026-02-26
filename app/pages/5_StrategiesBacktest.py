from __future__ import annotations

import json
import sys
import uuid
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
from core.backtest import SimpleBacktester
from core.db import (
    default_db_path,
    delete_strategy_profile,
    get_conn,
    list_instruments,
    list_strategy_profiles,
    query_prices_long,
    upsert_strategy_profile,
)
from core.strategy_examples import rsi_mean_reversion_signals, sma_crossover_signals

init_language()
st.set_page_config(page_title="Commodity Lab - Strategies & Backtest", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title(f"🎯 {t('strategies')}")
st.caption(l("Build strategy profiles, attach risk policy, run and compare.", "创建策略档案，配置风控策略，运行并比较表现。"))

con = get_conn(default_db_path(workspace_root))
instruments_df = list_instruments(con, only_watched=True)
available_tickers = instruments_df["ticker"].tolist() if not instruments_df.empty else []

st.subheader(l("Strategy profile editor", "策略档案编辑器"))

profiles = list_strategy_profiles(con)
options = ["__new__"] + (profiles["profile_id"].tolist() if not profiles.empty else [])
sel = st.selectbox(l("Profile", "档案"), options, format_func=lambda x: l("New profile", "新建档案") if x == "__new__" else x)

selected_row = None
if sel != "__new__" and not profiles.empty:
    selected_row = profiles[profiles["profile_id"] == sel].iloc[0]

params = json.loads(selected_row["params_json"]) if selected_row is not None and selected_row.get("params_json") else {}
risk_params = json.loads(selected_row["risk_params_json"]) if selected_row is not None and selected_row.get("risk_params_json") else {}

r1, r2, r3, r4 = st.columns(4)
profile_name = r1.text_input(l("Profile name", "档案名称"), value=(selected_row["profile_name"] if selected_row is not None else ""))
strategy = r2.selectbox(l("Trading strategy", "交易策略"), ["SMA Crossover", "RSI Mean Reversion"], index=0 if params.get("strategy_name", "SMA Crossover") == "SMA Crossover" else 1)
ticker = r3.selectbox(l("Ticker", "标的"), options=available_tickers, index=(available_tickers.index(selected_row["ticker"]) if selected_row is not None and selected_row.get("ticker") in available_tickers else 0) if available_tickers else None)
risk_policy = r4.selectbox(l("Risk policy", "风控策略"), ["none", "rolling_drop_guard"], index=0 if (selected_row is None or selected_row.get("risk_policy") in [None, "none"]) else 1)

c1, c2, c3, c4 = st.columns(4)
capital = c1.number_input(l("Initial Capital", "初始资金"), value=float(params.get("capital", 100000.0)), step=1000.0)
position_size_pct = c2.slider(l("Position Size (% equity)", "仓位比例（权益%）"), 0.01, 1.0, float(params.get("position_size_pct", 0.95)))
cost_per_trade = c3.number_input(l("Transaction Cost (pct)", "交易成本（比例）"), value=float(params.get("cost_per_trade", 0.001)))
slippage = c4.number_input(l("Slippage", "滑点"), value=float(params.get("slippage", 0.0)))

c5, c6, c7 = st.columns(3)
start = c5.date_input(l("Start date", "开始日期"), value=pd.Timestamp.today().date() - timedelta(days=int(params.get("lookback_days", 365))))
end = c6.date_input(l("End date", "结束日期"), value=pd.Timestamp.today().date())
fixed_fee = c7.number_input(l("Fixed fee", "固定费用"), value=float(params.get("fixed_fee", 0.0)))

rg1, rg2 = st.columns(2)
rolling_days = int(rg1.number_input(l("Risk window days", "风控窗口天数"), min_value=2, max_value=60, value=int(risk_params.get("window", 10))))
rolling_drop_pct = float(rg2.number_input(l("Risk max cumulative drop (%)", "风控最大累计跌幅(%)"), min_value=0.1, max_value=50.0, value=float(risk_params.get("drop_pct", 2.0))))

notes = st.text_area(l("Notes", "备注"), value=(selected_row["notes"] if selected_row is not None and selected_row.get("notes") else ""))

save_col, del_col, run_col = st.columns(3)
if save_col.button(l("💾 Save profile", "💾 保存档案"), type="primary"):
    if not profile_name.strip() or not ticker:
        st.error(l("Profile name and ticker required.", "档案名称和标的不能为空。"))
    else:
        pid = sel if sel != "__new__" else str(uuid.uuid4())
        cfg = {
            "capital": float(capital),
            "position_size_pct": float(position_size_pct),
            "cost_per_trade": float(cost_per_trade),
            "slippage": float(slippage),
            "fixed_fee": float(fixed_fee),
            "lookback_days": int((pd.Timestamp(end) - pd.Timestamp(start)).days),
            "strategy_name": strategy,
        }
        rp = {"window": rolling_days, "drop_pct": rolling_drop_pct}
        upsert_strategy_profile(con, {
            "profile_id": pid,
            "profile_name": profile_name,
            "strategy_name": strategy,
            "ticker": ticker,
            "params_json": json.dumps(cfg, ensure_ascii=False),
            "risk_policy": risk_policy,
            "risk_params_json": json.dumps(rp, ensure_ascii=False),
            "notes": notes,
        })
        st.success(l("Profile saved.", "档案已保存。"))
        st.rerun()

if del_col.button(l("🗑️ Delete profile", "🗑️ 删除档案"), disabled=(sel == "__new__")):
    delete_strategy_profile(con, sel)
    st.success(l("Profile deleted.", "档案已删除。"))
    st.rerun()

run_clicked = run_col.button(l("🚀 Run profile", "🚀 运行档案"), type="secondary")

if run_clicked:
    if not ticker:
        st.warning(l("Please choose ticker.", "请选择标的。"))
    else:
        px_df = query_prices_long(con, [ticker], start=start, end=end, field="close")
        if px_df.empty:
            st.error(l("No price data for ticker.", "该标的无价格数据。"))
        else:
            px_df = px_df.rename(columns={"value": "close"})[["date", "close"]]
            signals_df = sma_crossover_signals(px_df, short=20, long=50) if strategy == "SMA Crossover" else rsi_mean_reversion_signals(px_df, window=14)
            bt = SimpleBacktester(prices_df=px_df, signals_df=signals_df, capital=float(capital))
            run = bt.run(
                position_size_pct=float(position_size_pct),
                cost_per_trade=float(cost_per_trade),
                slippage=float(slippage),
                fixed_fee=float(fixed_fee),
            )
            eq = run.get("equity_curve")
            metrics = run.get("metrics") or {}

            risk_stats = {}
            if eq is not None and not eq.empty:
                e = eq.sort_values("date").copy()
                e["cum_peak"] = e["equity"].cummax()
                e["drawdown_pct"] = (e["equity"] / e["cum_peak"] - 1.0) * 100
                risk_stats["max_drawdown_pct"] = float(e["drawdown_pct"].min())

                if risk_policy == "rolling_drop_guard":
                    e["roll_ret"] = e["equity"] / e["equity"].shift(int(rolling_days)) - 1
                    breach = e[e["roll_ret"] <= -(rolling_drop_pct / 100.0)]
                    risk_stats["risk_breach_count"] = int(len(breach))
                    risk_stats["risk_window_days"] = int(rolling_days)
                    risk_stats["risk_drop_pct"] = float(rolling_drop_pct)

            st.subheader(l("Backtest result", "回测结果"))
            if eq is not None:
                st.plotly_chart(px.line(eq, x="date", y="equity", title=l("Equity curve", "权益曲线")), width="stretch")

            colm1, colm2 = st.columns(2)
            colm1.dataframe(pd.DataFrame([metrics]), width="stretch", hide_index=True)
            colm2.dataframe(pd.DataFrame([risk_stats]), width="stretch", hide_index=True)

st.divider()
st.subheader(l("Profile comparison", "档案对比"))
profiles = list_strategy_profiles(con)
if profiles.empty:
    st.info(l("No profiles yet.", "暂无档案。"))
else:
    picks = st.multiselect(l("Select profiles", "选择档案"), profiles["profile_id"].tolist())
    if picks:
        show = profiles[profiles["profile_id"].isin(picks)][["profile_id", "profile_name", "strategy_name", "ticker", "risk_policy", "updated_at"]]
        st.dataframe(show, width="stretch", hide_index=True)
