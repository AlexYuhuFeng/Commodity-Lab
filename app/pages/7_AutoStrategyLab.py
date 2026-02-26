"""Automated strategy lab for energy/commodity traders."""

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

from app.i18n import get_language, init_language, render_language_switcher
from core.auto_strategy import detect_hardware_acceleration, run_auto_strategy_search
from core.db import (
    default_db_path,
    get_conn,
    init_db,
    insert_strategy_run,
    list_instruments,
    list_strategy_runs,
    query_prices_long,
)

init_language()
st.set_page_config(page_title="Commodity Lab - Auto Strategy Lab", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title("🤖 Auto Strategy Lab")
st.caption(l("Generate, rank, and track common strategy families.", "生成、排名并追踪常见策略族。"))

con = get_conn(default_db_path(workspace_root))
init_db(con)

instruments_df = list_instruments(con, only_watched=True)
tickers = instruments_df["ticker"].tolist() if not instruments_df.empty else []

cap = detect_hardware_acceleration()
h1, h2 = st.columns(2)
h1.metric("Numba", "✅ Available" if cap["numba"] else "⚪ Not detected")
h2.metric("CuPy", "✅ Available" if cap["cupy"] else "⚪ Not detected")

st.info(l(
    "Numba/CuPy are used for acceleration in larger parameter sweeps; if unavailable, pipeline still runs on CPU.",
    "Numba/CuPy 用于大规模参数扫描加速；未安装时仍可在CPU上运行。",
))

c1, c2, c3 = st.columns(3)
selected = c1.multiselect(l("Tickers", "标的"), options=tickers, default=tickers[:1] if tickers else [])
lookback_days = c2.slider(l("Lookback days", "回看天数"), min_value=120, max_value=3650, value=730, step=30)
top_k = c3.slider(l("Top candidates", "候选数量"), min_value=3, max_value=30, value=10)

c4, c5, c6 = st.columns(3)
position_size_pct = c4.slider(l("Position Size %", "仓位比例"), min_value=0.1, max_value=1.0, value=0.9)
cost_per_trade = c5.number_input(l("Transaction Cost", "交易成本"), value=0.001, format="%.4f")
slippage = c6.number_input(l("Slippage", "滑点"), value=0.0, format="%.4f")

strategy_names = st.multiselect(
    l("Strategy families", "策略族"),
    options=["sma_crossover", "rsi_mean_reversion", "bollinger_reversion", "breakout"],
    default=["sma_crossover", "rsi_mean_reversion", "bollinger_reversion", "breakout"],
)

run_clicked = st.button(l("🚀 Run Automated Search", "🚀 运行自动策略搜索"), type="primary")

if run_clicked:
    if not selected:
        st.warning(l("Please select at least one ticker.", "请至少选择一个标的。"))
    elif not strategy_names:
        st.warning(l("Please select at least one strategy family.", "请至少选择一个策略族。"))
    else:
        start = pd.Timestamp.today().date() - timedelta(days=int(lookback_days))
        end = pd.Timestamp.today().date()

        all_rankings: list[pd.DataFrame] = []
        for tk in selected:
            pxdf = query_prices_long(con, [tk], start=start, end=end, field="close")
            if pxdf.empty:
                st.warning(f"No data for {tk}; skipped.")
                continue

            prices = pxdf.rename(columns={"value": "close"})[["date", "close"]]
            ranking = run_auto_strategy_search(
                prices=prices,
                strategy_names=strategy_names,
                initial_capital=100000,
                position_size_pct=float(position_size_pct),
                cost_per_trade=float(cost_per_trade),
                slippage=float(slippage),
                fixed_fee=0.0,
                top_k=int(top_k),
            )
            if ranking.empty:
                continue

            ranking["ticker"] = tk
            all_rankings.append(ranking)

            for _, row in ranking.iterrows():
                insert_strategy_run(
                    con,
                    {
                        "run_id": str(uuid.uuid4()),
                        "ticker": tk,
                        "strategy_name": row.get("strategy_name"),
                        "params_json": json.dumps(row.get("params", {}), ensure_ascii=False),
                        "score": row.get("score"),
                        "total_return_pct": row.get("total_return_pct"),
                        "max_drawdown_pct": row.get("max_drawdown_pct"),
                        "sharpe_ratio": row.get("sharpe_ratio"),
                        "win_rate": row.get("win_rate"),
                    },
                )

        if not all_rankings:
            st.error(l("No strategy candidates generated.", "未生成候选策略。"))
        else:
            leaderboard = pd.concat(all_rankings, ignore_index=True).sort_values(["score"], ascending=False)
            st.success(l(f"Generated {len(leaderboard)} candidates.", f"共生成 {len(leaderboard)} 个候选策略。"))
            st.dataframe(leaderboard[["ticker", "rank", "strategy_name", "params", "score", "total_return_pct", "max_drawdown_pct", "sharpe_ratio", "win_rate"]], width="stretch", hide_index=True)

            fig = px.bar(leaderboard.head(20), x="strategy_name", y="score", color="ticker", title=l("Top strategy scores", "策略评分Top"))
            st.plotly_chart(fig, width="stretch")

st.subheader(l("Strategy tracking history", "策略追踪历史"))
history = list_strategy_runs(con, limit=300)
if history.empty:
    st.info(l("No auto-search runs logged yet.", "暂无历史记录。"))
else:
    st.dataframe(history, width="stretch", hide_index=True)
