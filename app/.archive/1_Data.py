# app/pages/1_Data.py
from __future__ import annotations

import sys
from pathlib import Path

# Add the workspace root to the Python path so core module can be imported
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from datetime import date, datetime
import pandas as pd
import streamlit as st
import plotly.express as px

from core.db import (
    default_db_path,
    get_conn,
    init_db,
    list_instruments,
    list_transforms,
    query_prices_long,
    query_derived_long,
    list_refresh_log,
)
from core.refresh import refresh_many

st.set_page_config(page_title="Commodity Lab - Data", layout="wide")
st.title("Data - Raw / Derived（单位不一致就用派生序列再比较）")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = default_db_path(PROJECT_ROOT)

con = get_conn(DB_PATH)
init_db(con)


def qc_summary(df_long: pd.DataFrame) -> pd.DataFrame:
    if df_long.empty:
        return pd.DataFrame(columns=["ticker", "start", "end", "rows", "missing_bdays", "staleness_days"])

    today = datetime.now().date()
    out_rows = []

    for tk, g in df_long.groupby("ticker"):
        g = g.dropna(subset=["date"]).copy()
        if g.empty:
            continue

        dmin = g["date"].min().date()
        dmax = g["date"].max().date()
        nrows = int(g.shape[0])

        expected = pd.bdate_range(dmin, dmax)
        have = pd.to_datetime(g["date"].dt.date.unique())
        missing = len(set(expected.date) - set(have.date))

        staleness = (today - dmax).days

        out_rows.append(
            {
                "ticker": tk,
                "start": dmin,
                "end": dmax,
                "rows": nrows,
                "missing_bdays": int(missing),
                "staleness_days": int(staleness),
            }
        )
    return pd.DataFrame(out_rows).sort_values(["staleness_days", "missing_bdays"], ascending=[False, False])


inst = list_instruments(con, only_watched=False)
tf = list_transforms(con, enabled_only=False)

with st.sidebar:
    st.header("一键全体同步更新（Raw）")
    watched = inst[inst["is_watched"] == True]["ticker"].tolist()
    first_period = st.selectbox("首次下载周期（仅用于尚无数据的ticker）", ["max", "10y", "5y", "2y", "1y"], index=0)
    backfill_days = st.slider("回补最近N天（raw）", 0, 30, 7, 1)
    derived_backfill_days = st.slider("回补最近N天（derived）", 0, 30, 7, 1)

    if st.button("刷新全部已关注（raw + 自动更新派生）", type="primary"):
        if not watched:
            st.warning("没有已关注 ticker。先去 Catalog 页关注并下载。")
        else:
            prog = st.progress(0.0)
            results = []
            for i in range(len(watched)):
                prog.progress((i + 1) / len(watched))
            # 用 refresh_many：内部会统一触发派生更新
            results = refresh_many(
                con,
                watched,
                first_period=first_period,
                backfill_days=backfill_days,
                derived_backfill_days=derived_backfill_days,
            )
            ok = sum(1 for r in results if r["status"] == "success")
            st.success(f"刷新完成：success={ok}/{len(results)}（派生已自动重算）")
            st.rerun()

    st.divider()
    st.header("数据集选择")
    dataset = st.selectbox("选择数据集", ["Raw (prices_daily)", "Derived (derived_daily)"], index=0)

    use_range = st.checkbox("指定日期范围", value=False)
    start = st.date_input("Start", value=date(2020, 1, 1)) if use_range else None
    end = st.date_input("End", value=date.today()) if use_range else None

    if dataset.startswith("Raw"):
        field = st.selectbox("Raw 字段", ["close", "adj_close"], index=0)
        view = inst[inst["is_watched"] == True]
        options = [f"{r.ticker} | {r.name}" if r.name else r.ticker for r in view.itertuples()]
        mp = {o: o.split("|")[0].strip() for o in options}
        picks_disp = st.multiselect("选择 raw ticker", options=options, default=options[:1] if options else [])
        picks = [mp[x] for x in picks_disp]
    else:
        enabled_tf = tf[tf["enabled"] == True] if not tf.empty else tf
        derived_opts = enabled_tf["derived_ticker"].tolist() if not enabled_tf.empty else []
        picks = st.multiselect("选择 derived_ticker（来自 transforms）", options=derived_opts, default=derived_opts[:1] if derived_opts else [])
        field = "value"

# Query
if dataset.startswith("Raw"):
    df = query_prices_long(con, picks, start=start, end=end, field=field)
else:
    df = query_derived_long(con, picks, start=start, end=end)

if df.empty:
    st.warning("没有数据。要么还没下载入库，要么 derived 尚未计算。")
    st.stop()

st.subheader("覆盖与质量（QC）")
st.dataframe(qc_summary(df), use_container_width=True, height=220)

st.subheader("曲线")
fig = px.line(df.dropna(subset=["value"]), x="date", y="value", color="ticker", title=f"{dataset}")
st.plotly_chart(fig, use_container_width=True)

st.subheader("数据预览（宽表）")
wide = df.pivot_table(index="date", columns="ticker", values="value", aggfunc="last").reset_index()
st.dataframe(wide.sort_values("date"), use_container_width=True, height=420)

st.subheader("快速 Spread 预览（A - B）")
if len(picks) >= 2:
    a, b = picks[0], picks[1]
    w = wide.dropna(subset=[a, b]).copy()
    if not w.empty:
        w["spread"] = w[a] - w[b]
        fig2 = px.line(w, x="date", y="spread", title=f"Spread: {a} - {b}")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("两条序列重叠日期太少，暂时无法算 spread。")
else:
    st.info("至少选择两个 ticker 才能预览 spread。")

st.subheader("刷新日志（refresh_log）")
st.dataframe(list_refresh_log(con), use_container_width=True, height=260)

st.caption(f"DB: {DB_PATH}")
