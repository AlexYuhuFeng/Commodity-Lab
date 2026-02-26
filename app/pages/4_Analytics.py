from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
from core.db import (
    default_db_path,
    get_conn,
    init_db,
    list_instruments,
    query_derived_long,
    query_prices_long,
    upsert_derived_daily,
    upsert_instruments,
)

init_language()
st.set_page_config(page_title="Commodity Lab - Analytics", layout="wide")
render_language_switcher()

lang = get_language()


def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en


st.title(f"📊 {t('analytics')}")
st.caption(l("Spread + correlation toolkit for raw/derived series.", "面向 raw/derived 序列的价差与相关性分析工具箱。"))

con = get_conn(default_db_path(workspace_root))
init_db(con)
inst = list_instruments(con, only_watched=False)
raw_tickers = sorted(inst["ticker"].dropna().astype(str).tolist()) if not inst.empty else []
derived_df = con.execute("SELECT DISTINCT derived_ticker FROM derived_daily ORDER BY 1").df()
derived_tickers = derived_df["derived_ticker"].tolist() if not derived_df.empty else []
all_tickers = sorted(set(raw_tickers + derived_tickers))

if not all_tickers:
    st.warning(l("No data found. Please import data first.", "未找到可用数据，请先导入数据。"))
    st.stop()


@st.cache_data(show_spinner=False)
def _load_series_cached(ticker: str, _version: int = 0) -> pd.DataFrame:
    # _version used only for manual cache-bust if needed
    raw = query_prices_long(con, [ticker], field="close")
    if not raw.empty:
        return raw[["date", "value"]].rename(columns={"value": ticker})
    der = query_derived_long(con, [ticker])
    if not der.empty:
        return der[["date", "value"]].rename(columns={"value": ticker})
    return pd.DataFrame(columns=["date", ticker])


def load_series(ticker: str) -> pd.DataFrame:
    return _load_series_cached(ticker)


spread_tab, corr_tab = st.tabs([
    l("Spread Studio", "价差工作台"),
    l("Correlation Lab", "相关性实验室"),
])

with spread_tab:
    colA, colB, colC = st.columns(3)
    left_ticker = colA.selectbox(l("Left series", "左侧序列"), all_tickers, index=0)
    right_ticker = colB.selectbox(l("Right series", "右侧序列"), all_tickers, index=1 if len(all_tickers) > 1 else 0)
    mode = colC.selectbox(l("Spread formula", "价差计算方式"), ["L-R", "L/R", "(L-R)/R"])

    n1, n2 = st.columns(2)
    left_mult = n1.number_input(l("Left multiplier", "左侧倍率"), value=1.0, step=0.1)
    right_mult = n2.number_input(l("Right multiplier", "右侧倍率"), value=1.0, step=0.1)

    left_df = load_series(left_ticker)
    right_df = load_series(right_ticker)
    if left_df.empty or right_df.empty:
        st.error(l("One side has no data in local DB.", "某一侧在本地数据库中无数据。"))
        st.stop()

    merged = pd.merge(left_df, right_df, on="date", how="inner").dropna().sort_values("date")
    merged["left_norm"] = merged[left_ticker] * float(left_mult)
    merged["right_norm"] = merged[right_ticker] * float(right_mult)

    if mode == "L-R":
        merged["spread"] = merged["left_norm"] - merged["right_norm"]
    elif mode == "L/R":
        merged["spread"] = merged["left_norm"] / merged["right_norm"]
    else:
        merged["spread"] = (merged["left_norm"] - merged["right_norm"]) / merged["right_norm"]

    merged["spread_z20"] = (merged["spread"] - merged["spread"].rolling(20, min_periods=5).mean()) / merged["spread"].rolling(20, min_periods=5).std()

    chart_df = merged[["date", "left_norm", "right_norm", "spread", "spread_z20"]].copy()
    st.plotly_chart(px.line(chart_df, x="date", y=["left_norm", "right_norm", "spread"], title=l("Comparison + spread", "对比与价差")), width="stretch")
    st.plotly_chart(px.line(chart_df, x="date", y="spread_z20", title=l("Spread Z-score (20d)", "价差 Z-score（20天）")), width="stretch")

    k1, k2, k3 = st.columns(3)
    k1.metric(l("Latest spread", "最新价差"), f"{chart_df['spread'].iloc[-1]:.4f}")
    k2.metric(l("Spread mean", "价差均值"), f"{chart_df['spread'].mean():.4f}")
    k3.metric(l("Spread std", "价差标准差"), f"{chart_df['spread'].std():.4f}")

    st.dataframe(chart_df.tail(250), width="stretch", hide_index=True)

    st.subheader(l("Save spread as derived series", "将价差保存为派生序列"))
    default_name = f"SPREAD_{left_ticker}_{right_ticker}_{mode.replace('/','DIV').replace('-','MINUS')}"
    derived_name = st.text_input(l("Derived ticker", "派生代码"), value=default_name)
    notes = st.text_area(l("Description", "描述"), value=f"{left_ticker} {mode} {right_ticker}; left_mult={left_mult}; right_mult={right_mult}")

    if st.button(l("Save derived spread", "保存派生价差"), type="primary"):
        clean = (derived_name or "").strip().upper()
        if not clean:
            st.error(l("Derived ticker is required.", "派生代码不能为空。"))
        else:
            save_df = merged[["date", "spread"]].rename(columns={"spread": "value"})
            rows = upsert_derived_daily(con, clean, save_df)
            upsert_instruments(
                con,
                pd.DataFrame([
                    {
                        "ticker": clean,
                        "name": clean,
                        "quote_type": "derived",
                        "exchange": "local",
                        "currency": "",
                        "unit": "",
                        "category": "spread",
                        "source": "analytics",
                    }
                ]),
            )
            con.execute("UPDATE instruments SET is_watched=TRUE WHERE ticker=?", [clean])
            st.success(l(f"Saved {rows} rows to {clean}.", f"已保存 {rows} 行到 {clean}。"))
            if notes:
                st.caption(notes)

with corr_tab:
    st.caption(l("Compute pair correlation, rolling correlation, and return correlation matrix.", "计算双边相关、滚动相关以及收益率相关矩阵。"))

    c1, c2 = st.columns(2)
    corr_left = c1.selectbox(l("Series A", "序列A"), all_tickers, index=0, key="corr_left")
    corr_right = c2.selectbox(l("Series B", "序列B"), all_tickers, index=1 if len(all_tickers) > 1 else 0, key="corr_right")

    w1, w2, w3 = st.columns(3)
    corr_window = int(w1.number_input(l("Rolling window", "滚动窗口"), min_value=5, max_value=180, value=30))
    method = w2.selectbox(l("Correlation method", "相关系数方法"), ["pearson", "spearman"])
    matrix_top_n = int(w3.slider(l("Matrix tickers", "矩阵标的数"), 3, min(20, len(all_tickers)), min(8, len(all_tickers))))

    a_df = load_series(corr_left)
    b_df = load_series(corr_right)
    pair = pd.merge(a_df, b_df, on="date", how="inner").dropna().sort_values("date")

    if pair.empty:
        st.warning(l("No overlapping data for selected pair.", "所选序列没有重叠数据。"))
    else:
        pair["ret_a"] = pair[corr_left].pct_change()
        pair["ret_b"] = pair[corr_right].pct_change()
        pair = pair.dropna()

        point_corr = pair["ret_a"].corr(pair["ret_b"], method=method)
        pair["rolling_corr"] = pair["ret_a"].rolling(corr_window, min_periods=max(5, corr_window // 3)).corr(pair["ret_b"])

        m1, m2 = st.columns(2)
        m1.metric(l("Return correlation", "收益率相关系数"), f"{point_corr:.4f}" if pd.notna(point_corr) else "N/A")
        m2.metric(l("Latest rolling corr", "最新滚动相关"), f"{pair['rolling_corr'].iloc[-1]:.4f}" if pair["rolling_corr"].notna().any() else "N/A")

        st.plotly_chart(
            px.line(pair, x="date", y="rolling_corr", title=l("Rolling correlation", "滚动相关系数")),
            width="stretch",
        )

    st.divider()
    st.subheader(l("Return correlation matrix", "收益率相关矩阵"))

    default_matrix = all_tickers[:matrix_top_n]
    matrix_tickers = st.multiselect(
        l("Select tickers for matrix", "选择矩阵标的"),
        options=all_tickers,
        default=default_matrix,
        key="corr_matrix_tickers",
    )

    if len(matrix_tickers) < 2:
        st.info(l("Select at least 2 tickers.", "请至少选择2个标的。"))
    else:
        ret_cols = []
        for tk in matrix_tickers:
            s = load_series(tk)
            if s.empty:
                continue
            s = s.sort_values("date")
            s[tk] = s[tk].pct_change()
            ret_cols.append(s[["date", tk]])

        if len(ret_cols) < 2:
            st.warning(l("Not enough valid series for matrix.", "有效序列不足，无法生成矩阵。"))
        else:
            mat = ret_cols[0]
            for df_i in ret_cols[1:]:
                mat = pd.merge(mat, df_i, on="date", how="inner")
            mat = mat.dropna()

            corr_m = mat.drop(columns=["date"]).corr(method=method)
            heat = px.imshow(
                corr_m,
                text_auto=True,
                color_continuous_scale="RdBu",
                zmin=-1,
                zmax=1,
                title=l("Return correlation heatmap", "收益率相关热力图"),
            )
            st.plotly_chart(heat, width="stretch")
            st.dataframe(corr_m, width="stretch")
