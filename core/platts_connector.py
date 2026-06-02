from __future__ import annotations

import os
from datetime import date
from typing import Any, Optional

import pandas as pd
import requests

DEFAULT_PLATTS_URL = "https://api.platts.com/v1"


class PlattsAPIError(RuntimeError):
    pass


def _get_api_settings() -> tuple[str, str]:
    api_key = os.getenv("PLATTS_API_KEY", "").strip()
    api_url = os.getenv("PLATTS_API_URL", DEFAULT_PLATTS_URL).rstrip("/")
    if not api_key:
        raise PlattsAPIError("PLATTS_API_KEY is not configured. Set it in the environment or app settings.")
    return api_url, api_key


def _fetch_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    base_url, api_key = _get_api_settings()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    url = f"{base_url}/{path.lstrip('/') }"
    resp = requests.get(url, headers=headers, params=params or {}, timeout=20)
    if resp.status_code != 200:
        raise PlattsAPIError(
            f"Platts API request failed: {resp.status_code} {resp.text}"
        )
    return resp.json()


def search_platts(query: str, max_results: int = 25) -> list[dict[str, Any]]:
    """
    Search Platts instrument universe.
    This is an approximate connector. If the real Platts API uses a different path,
    adjust PLATTS_API_URL in the environment or app settings accordingly.
    """
    if not query:
        return []
    data = _fetch_json("search", {"q": query, "limit": max_results})
    rows = []
    for item in data.get("results", [])[:max_results]:
        rows.append({
            "ticker": item.get("symbol") or item.get("ticker") or item.get("id"),
            "name": item.get("name") or item.get("description") or "",
            "quote_type": item.get("type") or "commodity",
            "exchange": item.get("exchange") or "PLATTS",
            "currency": item.get("currency") or "USD",
        })
    return rows


def fetch_platts_history(
    ticker: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    period_if_no_start: str = "max",
) -> pd.DataFrame:
    """
    Fetch daily price history from Platts for a given contract.
    Returns standard columns: date, open, high, low, close, adj_close, volume.
    """
    if not ticker:
        return pd.DataFrame(
            columns=["date", "open", "high", "low", "close", "adj_close", "volume"]
        )

    params: dict[str, Any] = {"symbol": ticker}
    if start is not None:
        params["start_date"] = start.isoformat()
    if end is not None:
        params["end_date"] = end.isoformat()
    else:
        params["end_date"] = date.today().isoformat()
    params["period"] = period_if_no_start

    data = _fetch_json(f"prices/{ticker}", params=params)
    rows = data.get("prices") or data.get("historical") or []
    if not isinstance(rows, list):
        raise PlattsAPIError("Unexpected Platts history format")

    output = []
    for row in rows:
        dt = row.get("date") or row.get("day")
        if not dt:
            continue
        output.append(
            {
                "date": pd.to_datetime(dt).date(),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close") or row.get("price"),
                "adj_close": row.get("adj_close") or row.get("close") or row.get("price"),
                "volume": row.get("volume") or row.get("open_interest") or pd.NA,
            }
        )

    df = pd.DataFrame(output)
    if df.empty:
        return pd.DataFrame(
            columns=["date", "open", "high", "low", "close", "adj_close", "volume"]
        )

    df = df.dropna(subset=["close"]).sort_values("date").reset_index(drop=True)
    return df
