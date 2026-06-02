from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from core.platts_connector import fetch_platts_history, search_platts
from core.yf_prices import fetch_history_daily
from core.yf_provider import normalize_search_results, search_yahoo


def search_market(query: str, source: str = "yfinance", max_results: int = 25) -> list[dict[str, Any]]:
    source = (source or "yfinance").strip().lower()
    if source == "platts":
        return search_platts(query, max_results=max_results)
    return normalize_search_results(search_yahoo(query, max_results=max_results))


def fetch_price_history(
    ticker: str,
    source: str = "yfinance",
    start: date | None = None,
    period_if_no_start: str = "max",
    end: date | None = None,
) -> pd.DataFrame:
    source = (source or "yfinance").strip().lower()
    if source == "platts":
        return fetch_platts_history(ticker, start=start, end=end, period_if_no_start=period_if_no_start)
    return fetch_history_daily(ticker, start=start, period_if_no_start=period_if_no_start)


def available_sources() -> list[str]:
    return ["yfinance", "platts"]
