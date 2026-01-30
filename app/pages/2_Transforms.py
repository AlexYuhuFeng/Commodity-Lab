# app/pages/2_Transforms.py
from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
import streamlit as st
import plotly.express as px

from core.db import (
    default_db_path,
    get_conn,
    init_db,
    list_instruments,
    update_instrument_meta,
    list_transforms,
    upsert_transform,
    delete_transform,
    query_prices_long,
    query_derived_long,
)
from core.transforms import recompute_transform

st.set_page_config(page_title="Commodity Lab - Transforms", layout="wide")
st.title("Transforms - 货币/单位调整 + 派生序列（自动随 base/fx 更新）")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = default_db_path(PROJECT_ROOT)

con = get_conn(DB_PATH)
init_db(con)

MMBTU_PER_MWH = 3.412


def sanitize_derived_name(s: str) -> str:
    s = (s or "").strip()
    s = s.replace(" ", "_")
    # keep letters digits _ = - .
    s = re.sub(r"[^A-Za-z0-9_\-=\.:]+", "_", s)
    return s


inst = list_instruments(con, only_watched=False)
if inst.empty:
    st.warning("目录为空。先去 Catalog 页关注并下载一些 ticker。")
    st.stop()

with st.sidebar:
    st.header("视图过滤")
    only_watched = st.checkbox("只显示已关注 instruments", value=True)
    show_fx_candidates = st.checkbox("FX 候选仅显示 '=X' 或 quote_type=CURRENCY", value=True)

view = inst[inst["is_watched"] == True] if only_watched else inst

# -----------------------
# A) Metadata Editor
# -----------------------
st.subheader("A) Ticker 主数据（currency / unit）")
st.caption("yfinance 往往不给单位；我们把 currency/unit 当主数据维护。后续接入 Refinitiv/ICE/Platts 也同样需要这层。")

meta_cols = ["ticker", "name", "currency", "unit", "category", "is_watched", "source", "updated_at"]
meta_df = view[meta_cols].copy()
meta_df = meta_df.sort_values(["is_watched", "ticker"], ascending=[False, True])

edited = st.data_editor(
    meta_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "ticker": st.column_config.TextColumn("ticker", disabled=True),
        "name": st.column_config.TextColumn("name", disabled=True, width="large"),
        "currency": st.column_config.TextColumn("currency", help="价格币种，例如 EUR / USD"),
        "unit": st.column_config.TextColumn("unit", help="价格单位，例如 MWh / MMBtu / bbl / mt"),
        "category": st.column_config.TextColumn("category"),
        "is_watched": st.column_config.CheckboxColumn("watched", disabled=True),
        "source": st.column_config.TextColumn("source", disabled=True),
        "updated_at": st.column_config.TextColumn("updated_at", disabled=True),
    },
)

if st.button("保存主数据（currency/unit/category）", type="primary"):
    update_instrument_meta(con, edited[["ticker", "currency", "unit", "category"]])
    st.success("已保存。")
    st.rerun()

# -----------------------
# B) Transform Builder
# -----------------------
st.divider()
st.subheader("B) Transform 配方：用本地 FX ticker + 单位因子生成派生序列（落库）")

watched = inst[inst["is_watched"] == True].copy()
base_options = watched["ticker"].tolist() if not watched.empty else inst["ticker"].tolist()

base = st.selectbox("Base ticker（原始序列）", options=base_options, index=0)
base_row = inst[inst["ticker"] == base].iloc[0].to_dict()
base_ccy = (base_row.get("currency") or "").upper()
base_unit = (base_row.get("unit") or "")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Base currency", base_ccy or "(unset)")
with c2:
    st.metric("Base unit", base_unit or "(unset)")
with c3:
    st.metric("Base source", base_row.get("source") or "")

target_currency = st.text_input("Target currency（目标币种）", value=(base_ccy or "USD"))
target_unit = st.text_input("Target unit（目标单位）", value=(base_unit or "MMBtu"))

need_fx = (base_ccy and target_currency and base_ccy != target_currency)

fx_candidates = watched.copy()
if show_fx_candidates:
    fx_candidates = fx_candidates[
        fx_candidates["ticker"].str.contains("=X", na=False)
        | fx_candidates["quote_type"].str.contains("CURRENCY", na=False)
    ]
fx_list = fx_candidates["ticker"].tolist()
fx_list = [""] + fx_list

fx_ticker = ""
fx_op = "mul"
if need_fx:
    st.markdown("**货币不同：需要 FX ticker（来自本地已关注/已下载）**")
    fx_ticker = st.selectbox("FX ticker（例如 EURUSD=X）", options=fx_list, index=0)
    fx_op = st.radio("FX 作用方式", options=["mul", "div"], index=0, horizontal=True)
else:
    st.caption("货币相同或未设置 currency：不强制 FX。你也可以手动指定 FX（用于特殊情况）。")
    fx_ticker = st.selectbox("FX ticker（可选）", options=fx_list, index=0)
    fx_op = st.radio("FX 作用方式（可选）", options=["mul", "div"], index=0, horizontal=True)

# 单位因子：mult/div
st.markdown("**单位因子（multiplier/divider）**")
preset = st.selectbox(
    "单位换算预设",
    options=[
        "none (1/1)",
        "MWh -> MMBtu (divide 3.412)",
        "MMBtu -> MWh (multiply 3.412)",
        "custom",
    ],
    index=0,
)

multiplier = 1.0
divider = 1.0
if preset == "MWh -> MMBtu (divide 3.412)":
    multiplier, divider = 1.0, float(MMBTU_PER_MWH)
elif preset == "MMBtu -> MWh (multiply 3.412)":
    multiplier, divider = float(MMBTU_PER_MWH), 1.0

colm, cold = st.columns(2)
with colm:
    multiplier = st.number_input("multiplier", value=float(multiplier), min_value=0.0, format="%.8f")
with cold:
    divider = st.number_input("divider", value=float(divider), min_value=0.0, format="%.8f")

suggested = sanitize_derived_name(f"{base}_{target_currency}_{target_unit}")
derived_ticker = st.text_input("Derived ticker（派生ticker名）", value=suggested)
derived_ticker = sanitize_derived_name(derived_ticker)

notes = st.text_area("Notes（可选）", value="")

enabled = st.checkbox("enabled", value=True)

col_save, col_compute = st.columns([1, 1])
with col_save:
    if st.button("保存/更新 Transform", type="primary"):
        upsert_transform(
            con,
            {
                "transform_id": derived_ticker,
                "derived_ticker": derived_ticker,
                "base_ticker": base,
                "fx_ticker": fx_ticker.strip() or None,
                "fx_op": fx_op,
                "target_currency": target_currency.strip().upper(),
                "target_unit": target_unit.strip(),
                "multiplier": float(multiplier),
                "divider": float(divider if divider != 0 else 1.0),
                "enabled": bool(enabled),
                "notes": notes,
            },
        )
        st.success("Transform 已保存。")
        st.rerun()

with col_compute:
    if st.button("立即计算（重算该派生序列）"):
        tf = list_transforms(con, enabled_only=False)
        row = tf[tf["transform_id"] == derived_ticker]
        if row.empty:
            st.error("找不到该 transform，请先保存。")
        else:
            r = recompute_transform(con, row.iloc[0].to_dict(), backfill_days=7, field="close")
            st.success(f"{r['derived']} => {r['status']} rows={r['rows']}")
            st.rerun()

# -----------------------
# C) Transform List + Preview
# -----------------------
st.divider()
st.subheader("C) Transforms 列表（启用/删除/预览）")

tf = list_transforms(con, enabled_only=False)
if tf.empty:
    st.info("暂无 transforms。先在上面创建一个，比如 TTF(EUR/MWh) + EURUSD=X -> USD/MMBtu。")
    st.stop()

tf_show = tf[
    [
        "transform_id",
        "derived_ticker",
        "base_ticker",
        "fx_ticker",
        "fx_op",
        "target_currency",
        "target_unit",
        "multiplier",
        "divider",
        "enabled",
        "updated_at",
    ]
].copy()

tf_edit = st.data_editor(
    tf_show,
    use_container_width=True,
    hide_index=True,
    column_config={
        "transform_id": st.column_config.TextColumn("transform_id", disabled=True),
        "derived_ticker": st.column_config.TextColumn("derived_ticker", disabled=True),
        "enabled": st.column_config.CheckboxColumn("enabled"),
        "multiplier": st.column_config.NumberColumn("multiplier", format="%.8f"),
        "divider": st.column_config.NumberColumn("divider", format="%.8f"),
    },
)

if st.button("保存 transforms 变更（enabled/mult/div）"):
    # 简单做法：逐行 upsert（保持 UI 直观）
    for r in tf_edit.to_dict(orient="records"):
        upsert_transform(con, r)
    st.success("已保存。")
    st.rerun()

st.markdown("### 删除 transform")
del_id = st.selectbox("选择要删除的 transform_id", options=[""] + tf["transform_id"].tolist(), index=0)
del_derived = st.checkbox("同时删除 derived_daily 数据", value=False)
if st.button("删除", type="secondary"):
    if del_id:
        delete_transform(con, del_id, delete_derived=del_derived)
        st.success("已删除。")
        st.rerun()

st.markdown("### 预览派生序列（derived_daily）")
derived_opts = tf[tf["enabled"] == True]["derived_ticker"].tolist()
pick_derived = st.multiselect("选择 derived_ticker", options=derived_opts, default=derived_opts[:1])

if pick_derived:
    d = query_derived_long(con, pick_derived, start=None, end=None)
    if d.empty:
        st.warning("派生表里暂时没数据。点上面的“立即计算”或先刷新 base/fx。")
    else:
        fig = px.line(d.dropna(subset=["value"]), x="date", y="value", color="ticker", title="Derived series")
        st.plotly_chart(fig, use_container_width=True)
