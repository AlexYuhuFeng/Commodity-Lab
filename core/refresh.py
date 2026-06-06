# core/refresh.py
from __future__ import annotations

from core.data_source import AI_GENERATED_SOURCE
from core.db import get_last_price_date, log_refresh


def refresh_one(
    con,
    ticker: str,
    source: str = AI_GENERATED_SOURCE,
    first_period: str = "max",
    backfill_days: int = 7,
    derived_backfill_days: int = 7,
) -> dict:
    """External price refresh is disabled in the AI-generated V1 workflow."""
    _ = (source, first_period, backfill_days, derived_backfill_days)
    last_dt = get_last_price_date(con, ticker)
    message = "Commodity Lab V1 uses AI-generated training cases and does not refresh external market prices."
    log_refresh(con, ticker, status="disabled", message=message, last_success_date=last_dt)
    return {"ticker": ticker, "status": "disabled", "rows": 0, "last": last_dt, "message": message}


def refresh_many(
    con,
    tickers: list[str],
    source: str = AI_GENERATED_SOURCE,
    first_period: str = "max",
    backfill_days: int = 7,
    derived_backfill_days: int = 7,
) -> list[dict]:
    """Return disabled refresh rows for compatibility with old watcher code."""
    return [
        refresh_one(
            con,
            ticker,
            source=source,
            first_period=first_period,
            backfill_days=backfill_days,
            derived_backfill_days=derived_backfill_days,
        )
        for ticker in (tickers or [])
        if ticker
    ]
