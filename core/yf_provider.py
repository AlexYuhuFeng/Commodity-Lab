# core/yf_provider.py
from __future__ import annotations

from typing import Any, Dict, List
import yfinance as yf

# Prefer the more defensive search implementation when available
try:
    from core.yf_search import search_quotes
except Exception:
    search_quotes = None


def search_yahoo(query: str, max_results: int = 25) -> List[Dict[str, Any]]:
    """
    yfinance Search results (Yahoo)
    Returns list of dicts containing keys like symbol/shortName/longName/quoteType/exchange/currency.
    """
    query = (query or "").strip()
    if not query:
        return []

    # If we have our more robust `search_quotes` implementation, use it
    if search_quotes is not None:
        try:
            df = search_quotes(query, max_results=max_results)
            if df is None or df.empty:
                return []
            # convert dataframe rows to dicts compatible with normalize_search_results
            records = []
            for _, row in df.iterrows():
                records.append({
                    "ticker": row.get("ticker") or row.get("symbol"),
                    "name": row.get("name"),
                    "quoteType": row.get("quote_type") or row.get("quoteType"),
                    "exchange": row.get("exchange"),
                    "currency": row.get("currency"),
                })
            return records
        except Exception:
            pass

    if not hasattr(yf, "Search"):
        raise RuntimeError("yfinance.Search not found. Please upgrade: pip install -U yfinance")

    s = yf.Search(query, max_results=max_results)
    quotes = getattr(s, "quotes", None) or []

    results: List[Dict[str, Any]] = []
    for q in quotes:
        if isinstance(q, dict):
            symbol = q.get("symbol") or q.get("ticker")
            if symbol:
                results.append(q)
    return results


def normalize_search_results(quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize to our instrument schema.
    """
    out = []
    for q in quotes:
        ticker = q.get("symbol") or q.get("ticker")
        if not ticker:
            continue

        # Prefer long name if available
        name = (
            q.get("longName") or q.get("longname")
            or q.get("shortName") or q.get("shortname")
            or q.get("name") or ""
        )

        quote_type = q.get("quoteType") or q.get("type") or ""
        exchange = q.get("exchange") or q.get("exchDisp") or q.get("market") or ""
        currency = q.get("currency") or ""

        out.append(
            {
                "ticker": ticker,
                "name": name,
                "quote_type": quote_type,
                "exchange": exchange,
                "currency": currency,
                "category": "",
                "source": "yfinance",
            }
        )
    return out
