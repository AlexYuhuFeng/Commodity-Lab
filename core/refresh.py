# core/refresh.py
from __future__ import annotations

from datetime import timedelta, date
import pandas as pd

from core.db import get_last_price_date, upsert_prices_daily, log_refresh
from core.yf_prices import fetch_history_daily
from core.transforms import update_derived_for_tickers


def refresh_one(
    con,
    ticker: str,
    first_period: str = "max",
    backfill_days: int = 7,
    derived_backfill_days: int = 7,
) -> dict:
    """
    刷新 raw ticker：
    - 若库里无数据：按 first_period 拉历史
    - 若库里有数据：从 last_date-backfill_days 起拉，回补最近 N 天
    成功后自动触发受影响 transforms 的派生重算（base/fx 更新 -> derived 更新）。
    """
    last_dt = get_last_price_date(con, ticker)

    try:
        if last_dt is None:
            px = fetch_history_daily(ticker, start=None, period_if_no_start=first_period)
        else:
            start = last_dt - timedelta(days=backfill_days)
            px = fetch_history_daily(ticker, start=start, period_if_no_start=first_period)

        if px is None or px.empty:
            log_refresh(con, ticker, status="empty", message="no data returned by provider", last_success_date=last_dt)
            return {"ticker": ticker, "status": "empty", "rows": 0, "last": last_dt, "message": "no data"}

        n = upsert_prices_daily(con, ticker, px)
        last_success = px["date"].max()
        log_refresh(con, ticker, status="success", message=f"upserted {n} rows", last_success_date=last_success)

        # ✅ 派生自动更新：这个 ticker 可能是 base 或 fx
        update_derived_for_tickers(con, [ticker], backfill_days=derived_backfill_days)

        return {"ticker": ticker, "status": "success", "rows": n, "last": last_success, "message": ""}

    except Exception as e:
        log_refresh(con, ticker, status="error", message=str(e), last_success_date=last_dt)
        return {"ticker": ticker, "status": "error", "rows": 0, "last": last_dt, "message": str(e)}


def refresh_many(
    con,
    tickers: list[str],
    first_period: str = "max",
    backfill_days: int = 7,
    derived_backfill_days: int = 7,
) -> list[dict]:
    """
    批量刷新 raw tickers，然后一次性触发派生更新（更省）。
    """
    tickers = [t for t in (tickers or []) if t]
    if not tickers:
        return []

    results = []
    updated = []

    for tk in tickers:
        r = refresh_one(
            con,
            tk,
            first_period=first_period,
            backfill_days=backfill_days,
            derived_backfill_days=0,  # 这里先不触发，最后统一触发
        )
        results.append(r)
        if r["status"] == "success" and r["rows"] > 0:
            updated.append(tk)

    # 统一派生更新（包含 base & fx）
    if updated:
        update_derived_for_tickers(con, updated, backfill_days=derived_backfill_days)

    return results
