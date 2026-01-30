# core/watch.py
from __future__ import annotations

from typing import Iterable
import pandas as pd

from core.db import upsert_instruments, set_watch, update_instrument_meta
from core.refresh import refresh_many


def add_to_catalog(con, rows: pd.DataFrame) -> None:
    """
    将搜索结果写入 instruments（不改变 is_watched）
    """
    if rows is None or rows.empty:
        return
    upsert_instruments(con, rows)


def watch_and_download(
    con,
    selected_rows: pd.DataFrame,
    first_period: str = "max",
    backfill_days: int = 7,
    derived_backfill_days: int = 7,
) -> list[dict]:
    """
    一步到位：
    1) upsert instruments（含 currency 等元数据）
    2) set_watch=True
    3) 下载并入库 prices_daily（增量/回补）
    4) 自动触发 derived 更新（refresh_many 内部会做）
    """
    if selected_rows is None or selected_rows.empty:
        return []

    add_to_catalog(con, selected_rows)

    tickers = selected_rows["ticker"].astype(str).tolist()
    set_watch(con, tickers, True)

    return refresh_many(
        con,
        tickers,
        first_period=first_period,
        backfill_days=backfill_days,
        derived_backfill_days=derived_backfill_days,
    )


def unwatch(con, tickers: Iterable[str]) -> None:
    tickers = [str(t).strip() for t in (tickers or []) if str(t).strip()]
    if not tickers:
        return
    set_watch(con, tickers, False)


def unwatch_and_delete_prices(con, tickers: Iterable[str]) -> None:
    """
    取消关注 + 删除本地历史行情（raw）+ 清理对应 refresh_log（不删 instruments 记录）
    """
    tickers = [str(t).strip() for t in (tickers or []) if str(t).strip()]
    if not tickers:
        return

    set_watch(con, tickers, False)
    con.execute("DELETE FROM prices_daily WHERE ticker IN (SELECT * FROM UNNEST(?))", [tickers])
    con.execute("DELETE FROM refresh_log WHERE ticker IN (SELECT * FROM UNNEST(?))", [tickers])
