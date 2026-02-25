"""Automated strategy lab for energy/commodity traders."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import init_language, render_language_switcher
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

st.title("🤖 Auto Strategy Lab")
st.caption("Automate model generation, parameter search, backtesting, and candidate ranking.")

with st.expander("🧭 Trader-oriented guidance", expanded=True):
    st.markdown(
        """
- Focus objective: **risk-adjusted returns**, not raw return alone.
- Run this screen daily after refresh to maintain a rolling model leaderboard.
- Prefer stable candidates with acceptable drawdown and turnover.
- Use this page as pre-trade idea generation; validate in monitoring + discretionary context.
        """
    )

con = get_conn(default_db_path(workspace_root))
init_db(con)

instruments_df = list_instruments(con, only_watched=True)
tickers = instruments_df["ticker"].tolist() if not instruments_df.empty else []

cap = detect_hardware_acceleration()
h1, h2 = st.columns(2)
h1.metric("Numba", "✅ Available" if cap["numba"] else "⚪ Not detected")
h2.metric("CuPy", "✅ Available" if cap["cupy"] else "⚪ Not detected")

with st.sidebar:
    st.header("Automation Controls")
    selected = st.multiselect("Tickers", options=tickers, default=tickers[:1] if tickers else [])
    lookback_days = st.slider("Lookback days", min_value=120, max_value=3650, value=730, step=30)
    top_k = st.slider("Top candidates", min_value=3, max_value=30, value=10)
    position_size_pct = st.slider("Position Size %", min_value=0.1, max_value=1.0, value=0.9)
    cost_per_trade = st.number_input("Transaction Cost", value=0.001, format="%.4f")
    slippage = st.number_input("Slippage", value=0.0, format="%.4f")
    fixed_fee = st.number_input("Fixed Fee", value=0.0, format="%.2f")

run_clicked = st.button("🚀 Run Automated Search", type="primary")

if run_clicked:
    if not selected:
        st.warning("Please select at least one ticker.")
    else:
        start = pd.Timestamp.today().date() - timedelta(days=int(lookback_days))
        end = pd.Timestamp.today().date()

        all_rankings: list[pd.DataFrame] = []
        for tk in selected:
            px = query_prices_long(con, [tk], start=start, end=end, field="close")
            if px.empty:
                st.warning(f"No data for {tk}; skipped.")
                continue

            prices = px.rename(columns={"value": "close"})[["date", "close"]]
            ranking = run_auto_strategy_search(
                prices=prices,
                initial_capital=100000,
                position_size_pct=float(position_size_pct),
                cost_per_trade=float(cost_per_trade),
                slippage=float(slippage),
                fixed_fee=float(fixed_fee),
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
            st.error("No strategy candidates generated.")
        else:
            leaderboard = pd.concat(all_rankings, ignore_index=True)
            leaderboard = leaderboard.sort_values(["score"], ascending=False)

            st.success(f"Generated {len(leaderboard)} candidates across {len(selected)} tickers.")
            st.subheader("🏆 Current Candidate Leaderboard")
            st.dataframe(
                leaderboard[
                    [
                        "ticker",
                        "rank",
                        "strategy_name",
                        "params",
                        "score",
                        "total_return_pct",
                        "max_drawdown_pct",
                        "sharpe_ratio",
                        "win_rate",
                    ]
                ],
                use_container_width=True,
            )

st.subheader("📚 Historical Auto-Search Runs")
history = list_strategy_runs(con, limit=300)
if history.empty:
    st.info("No auto-search runs logged yet.")
else:
    st.dataframe(history, use_container_width=True)

try:
    con.close()
except Exception:
    pass
