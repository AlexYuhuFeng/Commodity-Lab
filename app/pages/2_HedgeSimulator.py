from __future__ import annotations

import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
from core.db import default_db_path, get_conn, init_db, list_instruments, query_series_long
from core.hedge import HEDGE_TYPES, ORDER_SIDES, VirtualOrder, simulate_portfolio, summarize_hedge_performance, score_portfolio

init_language()
st.set_page_config(page_title="Hedge Lab - Simulator", layout="wide")
render_language_switcher()
lang = get_language()


def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title("🧠 Hedge Simulator")
st.caption(l("Place virtual hedge orders, review simulated P&L, and learn contract exposure.", "下虚拟对冲单，查看模拟盈亏，学习合约敞口。"))

con = get_conn(default_db_path(workspace_root))
init_db(con)

instruments = list_instruments(con, only_watched=True)
tickers = instruments["ticker"].tolist() if not instruments.empty else []
selected_ticker = st.selectbox(l("Contract to simulate", "模拟合约"), options=tickers, index=0 if tickers else None)

if not selected_ticker:
    st.warning(l("Please add at least one contract in Market Explorer first.", "请先在市场探索页面添加至少一个合约。"))
    st.stop()

st.divider()

st.subheader(l("Build a virtual hedge order", "构建虚拟对冲单"))
cols = st.columns(3)
side = cols[0].selectbox(l("Side", "方向"), options=ORDER_SIDES)
hedge_type = cols[1].selectbox(l("Hedge type", "对冲类型"), options=HEDGE_TYPES)
quantity = cols[2].number_input(l("Quantity", "数量"), value=1.0, min_value=0.01, step=0.1)

cols2 = st.columns(3)
open_date = cols2[0].date_input(l("Open date", "开仓日期"), value=date.today() - timedelta(days=30))
close_date = cols2[1].date_input(l("Close date", "平仓日期"), value=date.today())
open_price = cols2[2].number_input(l("Open price (optional)", "开仓价格（可选）"), value=0.0, min_value=0.0, step=0.01)

note = st.text_input(l("Order note", "订单备注"), value="")

if "virtual_orders" not in st.session_state:
    st.session_state.virtual_orders = []

if st.button(l("Add virtual order", "添加虚拟订单")):
    order = VirtualOrder(
        order_id=str(uuid.uuid4()),
        ticker=selected_ticker,
        side=side,
        quantity=float(quantity),
        open_date=open_date,
        close_date=close_date,
        open_price=float(open_price) if open_price > 0 else 0.0,
        close_price=None,
        hedge_type=hedge_type,
        note=note or f"{hedge_type} {side}",
    )
    st.session_state.virtual_orders.append(order)
    st.experimental_rerun()

if st.session_state.virtual_orders:
    st.subheader(l("Active virtual orders", "当前虚拟订单"))
    orders_df = pd.DataFrame([o.to_dict() for o in st.session_state.virtual_orders])
    st.dataframe(orders_df, width="stretch")

    remove_id = st.text_input(l("Order ID to remove", "删除订单 ID"), value="")
    if st.button(l("Remove order", "删除订单")):
        st.session_state.virtual_orders = [o for o in st.session_state.virtual_orders if o.order_id != remove_id]
        st.experimental_rerun()

    data = query_series_long(con, [selected_ticker], field="close")
    data = data.sort_values("date")
    if data.empty:
        st.warning(l("No price history available for this contract. Refresh in Market Explorer.", "该合约暂无价格历史。请在市场探索页面刷新。"))
    else:
        min_date = min(o.open_date for o in st.session_state.virtual_orders)
        max_date = max(o.close_date for o in st.session_state.virtual_orders)
        prices = data[(data["date"] >= pd.to_datetime(min_date)) & (data["date"] <= pd.to_datetime(max_date))].copy()
        prices["date"] = pd.to_datetime(prices["date"]).dt.date

        if prices.empty:
            st.warning(l("Price range is outside available history for the selected contract.", "所选合约的价格范围不在历史数据内。"))
        else:
            order_results = simulate_portfolio(prices, st.session_state.virtual_orders)
            metrics = summarize_hedge_performance(st.session_state.virtual_orders, order_results)
            portfolio_score = score_portfolio(order_results)

            st.subheader(l("Simulation results", "模拟结果"))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(l("Total P&L", "总盈亏"), f"{metrics['total_pnl']:.2f}")
            c2.metric(l("Total notional", "总名义"), f"{metrics['total_notional']:.2f}")
            c3.metric(l("Average profit %", "平均收益率"), f"{metrics['average_profit_pct']:.2f}%")
            c4.metric(l("Portfolio score", "组合评分"), f"{portfolio_score:.1f}/100")

            st.markdown(l("### Order performance", "### 订单表现"))
            st.dataframe(order_results, width="stretch", hide_index=True)
            st.caption(l(
                "The score reflects risk-adjusted hedge execution and order consistency.",
                "该评分反映了风险调整后的对冲执行和订单一致性。"
            ))

            curve = prices.rename(columns={"value": "close"})
            fig = px.line(curve, x="date", y="close", title=l("Contract Close Price", "合约收盘价"))
            st.plotly_chart(fig, width="stretch")
else:
    st.info(l("Build your first virtual hedge order to start learning.", "创建首个虚拟对冲订单开始学习。"))

try:
    con.close()
except Exception:
    pass
