# app/pages/0_Catalog.py
from __future__ import annotations

from datetime import timedelta, date
from pathlib import Path

import pandas as pd
import streamlit as st

from core.db import (
    default_db_path,
    get_conn,
    init_db,
    upsert_instruments,
    list_instruments,
    set_watch,
    get_last_price_date,
    upsert_prices_daily,
    log_refresh,
    list_refresh_log,
    update_instrument_meta,
    delete_instruments,
)
from core.yf_provider import search_yahoo, normalize_search_results
from core.yf_prices import fetch_history_daily


st.set_page_config(page_title="Commodity Lab - Catalog", layout="wide")
st.title("Catalog / Search - 产品目录与关注列表（Step 1）")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = default_db_path(PROJECT_ROOT)

con = get_conn(DB_PATH)
init_db(con)


# -------------------------
# Sidebar controls
# -------------------------
with st.sidebar:
    st.header("搜索（Yahoo Finance via yfinance）")
    query = st.text_input("关键词（如: natural gas, brent, ttf, eurusd）", value="")
    max_results = st.slider("候选数量", 5, 50, 25, 5)

    st.divider()
    st.header("下载设置")
    auto_download_on_watch = st.checkbox("关注后自动下载历史并入库", value=True)
    default_period = st.selectbox("首次下载周期", ["max", "10y", "5y", "2y", "1y"], index=0)
    backfill_days = st.slider("增量更新回补天数（建议 3~10）", 0, 30, 7, 1)

    st.divider()
    st.header("刷新")
    refresh_mode = st.radio("刷新范围", ["全部已关注", "仅选中"], index=0)
    run_refresh = st.button("执行刷新（raw）", type="primary")


def _download_and_upsert_one(tk: str) -> dict:
    """
    增量下载并入库（带 backfill）：
    - 没数据：按 period 拉全量
    - 有数据：从 last_date - backfill_days 回补
    """
    tk = (tk or "").strip()
    last_dt = get_last_price_date(con, tk)

    try:
        if last_dt is None:
            px = fetch_history_daily(tk, start=None, period_if_no_start=default_period)
        else:
            start = last_dt - timedelta(days=int(backfill_days))
            px = fetch_history_daily(tk, start=start, period_if_no_start=default_period)

        if px is None or px.empty:
            log_refresh(con, tk, status="empty", message="no data returned", last_success_date=last_dt)
            return {"ticker": tk, "status": "empty", "rows": 0, "last": last_dt, "message": "no data"}

        n = upsert_prices_daily(con, tk, px)
        last_success = px["date"].max() if "date" in px.columns and not px.empty else last_dt

        if n > 0:
            log_refresh(con, tk, status="success", message=f"upserted {n} rows", last_success_date=last_success)
            return {"ticker": tk, "status": "success", "rows": n, "last": last_success, "message": ""}
        else:
            # 有可能这段回补区间数据一致（不新增/不变更）
            log_refresh(con, tk, status="empty", message="no new rows", last_success_date=last_success)
            return {"ticker": tk, "status": "empty", "rows": 0, "last": last_success, "message": "no new rows"}

    except Exception as e:
        log_refresh(con, tk, status="error", message=str(e), last_success_date=last_dt)
        return {"ticker": tk, "status": "error", "rows": 0, "last": last_dt, "message": str(e)}


def _run_download_for(tickers: list[str]) -> None:
    tickers = [t for t in (tickers or []) if str(t).strip()]
    if not tickers:
        st.warning("没有要下载的 ticker。")
        return

    prog = st.progress(0.0)
    box = st.empty()

    results = []
    for i, tk in enumerate(tickers, start=1):
        r = _download_and_upsert_one(tk)
        results.append(r)

        if r["status"] == "success":
            box.write(f"✅ {tk}: +{r['rows']} rows (last {r['last']})")
        elif r["status"] == "empty":
            box.write(f"⚪ {tk}: {r['message']} (last {r['last']})")
        else:
            box.write(f"❌ {tk}: {r['message']}")

        prog.progress(i / len(tickers))

    ok = sum(1 for r in results if r["status"] == "success")
    err = sum(1 for r in results if r["status"] == "error")
    st.success(f"完成：success={ok}, error={err}, total={len(results)}")


# -------------------------
# 1) Search candidates
# -------------------------
st.subheader("1) 搜索候选")

if query.strip():
    try:
        quotes = search_yahoo(query, max_results=max_results)
        norm = normalize_search_results(quotes)
        df = pd.DataFrame(norm)

        if df.empty:
            st.warning("未找到候选。换个关键词或直接输入 ticker（如 NG=F、TTF=F、EURUSD=X）。")
        else:
            # 允许你在搜索阶段就补充 unit/category
            if "unit" not in df.columns:
                df["unit"] = ""
            if "category" not in df.columns:
                df["category"] = ""

            df.insert(0, "pick", False)

            edited = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "pick": st.column_config.CheckboxColumn("选择"),
                    "ticker": st.column_config.TextColumn("Ticker", width="small"),
                    "name": st.column_config.TextColumn("Name", width="large"),
                    "quote_type": st.column_config.TextColumn("Type", width="small"),
                    "exchange": st.column_config.TextColumn("Exchange", width="small"),
                    "currency": st.column_config.TextColumn("CCY", width="small"),
                    "unit": st.column_config.TextColumn("Unit", help="例如 MWh / MMBtu / bbl / mt"),
                    "category": st.column_config.TextColumn("Category", help="自定义分类：Gas / Power / FX / ..."),
                },
            )

            picked = edited[edited["pick"] == True].drop(columns=["pick"])
            c1, c2, c3 = st.columns([1, 1, 2])

            with c1:
                if st.button("写入本地目录（Catalog）", type="secondary"):
                    if picked.empty:
                        st.warning("你还没勾选任何候选。")
                    else:
                        upsert_instruments(con, picked)
                        st.success(f"已写入 {len(picked)} 个 ticker 到本地目录。")
                        st.rerun()

            with c2:
                if st.button("写入并关注（一步到位）", type="primary"):
                    if picked.empty:
                        st.warning("你还没勾选任何候选。")
                    else:
                        upsert_instruments(con, picked)
                        set_watch(con, picked["ticker"].tolist(), True)

                        if auto_download_on_watch:
                            st.info("已关注，开始下载历史数据并入库…")
                            _run_download_for(picked["ticker"].tolist())

                        st.success("完成。")
                        st.rerun()

            with c3:
                st.caption("提示：建议直接搜 NG=F / TTF=F / JKM=F / EURUSD=X。单位（unit）通常需要你手工维护。")

    except Exception as e:
        st.error(f"搜索失败：{e}")
else:
    st.info("在左侧输入关键词开始搜索。")


# -------------------------
# 2) Local catalog (editable + batch ops)
# -------------------------
st.subheader("2) 本地目录（Catalog）")

catalog = list_instruments(con, only_watched=False)

if catalog.empty:
    st.write("目录为空。先在上面搜索并写入。")
    st.stop()

watched_only = st.checkbox("只看已关注", value=False)
view = catalog[catalog["is_watched"] == True] if watched_only else catalog

# 追加 last_price_date/staleness（用 SQL 聚合一次，避免逐 ticker 查询）
last_px = con.execute(
    """
    SELECT ticker, MAX(date) AS last_price_date
    FROM prices_daily
    GROUP BY ticker
    """
).df()

if not last_px.empty:
    last_px["last_price_date"] = pd.to_datetime(last_px["last_price_date"]).dt.date
    view = view.merge(last_px, on="ticker", how="left")
else:
    view["last_price_date"] = pd.NA

today = date.today()
view["staleness_days"] = view["last_price_date"].apply(
    lambda d: (today - d).days if pd.notna(d) else None
)

show_cols = [
    "ticker",
    "name",
    "quote_type",
    "exchange",
    "currency",
    "unit",
    "category",
    "is_watched",
    "last_price_date",
    "staleness_days",
    "updated_at",
]
for c in show_cols:
    if c not in view.columns:
        view[c] = ""

view = view[show_cols].copy()
view.insert(0, "pick", False)

edited_catalog = st.data_editor(
    view,
    use_container_width=True,
    hide_index=True,
    column_config={
        "pick": st.column_config.CheckboxColumn("选择"),
        "ticker": st.column_config.TextColumn("ticker", disabled=True),
        "name": st.column_config.TextColumn("name", width="large", disabled=True),
        "quote_type": st.column_config.TextColumn("type", disabled=True),
        "exchange": st.column_config.TextColumn("exchange", disabled=True),
        "currency": st.column_config.TextColumn("currency"),
        "unit": st.column_config.TextColumn("unit", help="例如 MWh / MMBtu / bbl / mt"),
        "category": st.column_config.TextColumn("category"),
        "is_watched": st.column_config.CheckboxColumn("watched", disabled=True),
        "last_price_date": st.column_config.TextColumn("last_price_date", disabled=True),
        "staleness_days": st.column_config.NumberColumn("staleness_days", disabled=True),
        "updated_at": st.column_config.TextColumn("updated_at", disabled=True),
    },
)

picked_rows = edited_catalog[edited_catalog["pick"] == True].copy()
picked_tickers = picked_rows["ticker"].tolist() if not picked_rows.empty else []

colS1, colS2, colS3, colS4, colS5 = st.columns([1.2, 1.2, 1.2, 1.6, 1.6])

with colS1:
    if st.button("保存元数据（CCY/Unit/Category）", type="primary"):
        # 只保存目录里的可编辑字段
        update_instrument_meta(con, edited_catalog[["ticker", "currency", "unit", "category"]])
        st.success("已保存。")
        st.rerun()

with colS2:
    if st.button("设为关注 ✅", disabled=(len(picked_tickers) == 0)):
        set_watch(con, picked_tickers, True)
        if auto_download_on_watch:
            st.info("已关注，开始下载历史数据并入库…")
            _run_download_for(picked_tickers)
        st.success(f"已关注：{len(picked_tickers)}")
        st.rerun()

with colS3:
    if st.button("取消关注 ❌", disabled=(len(picked_tickers) == 0)):
        set_watch(con, picked_tickers, False)
        st.success(f"已取消关注：{len(picked_tickers)}")
        st.rerun()

with colS4:
    if st.button("取消关注并删除本地 raw 🗑️", disabled=(len(picked_tickers) == 0)):
        set_watch(con, picked_tickers, False)
        con.execute("DELETE FROM prices_daily WHERE ticker IN (SELECT * FROM UNNEST(?))", [picked_tickers])
        con.execute("DELETE FROM refresh_log WHERE ticker IN (SELECT * FROM UNNEST(?))", [picked_tickers])
        st.success(f"已取消关注并删除 raw：{len(picked_tickers)}")
        st.rerun()

with colS5:
    delete_raw = st.checkbox("从目录删除时同时删除 raw", value=False)
    if st.button("从目录删除（硬删除）", disabled=(len(picked_tickers) == 0)):
        # 为了兼容你当前 db.py 的 delete_instruments 签名，这里只调用删除 instruments，
        # raw/refresh_log 由我们自己控制。
        if delete_raw:
            con.execute("DELETE FROM prices_daily WHERE ticker IN (SELECT * FROM UNNEST(?))", [picked_tickers])
        con.execute("DELETE FROM refresh_log WHERE ticker IN (SELECT * FROM UNNEST(?))", [picked_tickers])
        delete_instruments(con, picked_tickers)  # 仅删目录记录
        st.success(f"已从目录删除：{len(picked_tickers)}")
        st.rerun()


# -------------------------
# Sidebar-triggered refresh (raw)
# -------------------------
if run_refresh:
    if refresh_mode == "全部已关注":
        tgt = list_instruments(con, only_watched=True)["ticker"].tolist()
    else:
        tgt = picked_tickers

    if not tgt:
        st.warning("没有可刷新的 ticker（要么没关注，要么你没选中）。")
    else:
        st.info(f"开始刷新 raw：{len(tgt)} 个 ticker（回补 {backfill_days} 天）…")
        _run_download_for(tgt)
        st.rerun()


# -------------------------
# 3) Logs
# -------------------------
st.caption(f"本地数据库：{DB_PATH}")
st.subheader("3) 刷新日志（refresh_log）")
st.dataframe(list_refresh_log(con), use_container_width=True, height=320)
