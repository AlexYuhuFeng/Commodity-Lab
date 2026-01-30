# core/yf_search.py
from __future__ import annotations

from typing import Any
import pandas as pd
import yfinance as yf


def _pick(d: dict, keys: list[str], default="") -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _to_row(q: dict) -> dict:
    # Yahoo/YFinance 字段经常有大小写/命名差异，这里做容错映射
    ticker = _pick(q, ["symbol", "ticker"])
    name = _pick(q, ["shortname", "shortName", "longname", "longName", "name"])
    quote_type = _pick(q, ["quoteType", "quote_type", "typeDisp", "type"])
    exchange = _pick(q, ["exchange", "exchDisp", "fullExchangeName", "exchangeName"])
    currency = _pick(q, ["currency", "financialCurrency"])
    return {
        "ticker": str(ticker).strip(),
        "name": str(name).strip(),
        "quote_type": str(quote_type).strip(),
        "exchange": str(exchange).strip(),
        "currency": str(currency).strip(),
        "unit": "",          # yfinance 通常不给“计量单位”，留给用户维护
        "category": "",      # 用户自定义分类
        "source": "yfinance",
    }


def search_quotes(query: str, max_results: int = 20, enable_fuzzy: bool = True) -> pd.DataFrame:
    q = (query or "").strip()
    if not q:
        return pd.DataFrame(columns=["ticker", "name", "quote_type", "exchange", "currency", "unit", "category", "source"])

    # 1) 优先 Search（更像“搜索”）
    quotes = []
    try:
        s = yf.Search(q, max_results=max_results, enable_fuzzy_query=enable_fuzzy, raise_errors=False)
        quotes = s.quotes or []
    except Exception:
        quotes = []

    # 2) fallback：Lookup（有时对期货/外汇更稳）
    if not quotes:
        try:
            lk = yf.Lookup(q, raise_errors=False)
            # 优先 future/currency/index，其次 all
            buckets = []
            for attr in ["future", "currency", "index", "stock", "all"]:
                try:
                    v = getattr(lk, attr)
                    if isinstance(v, list):
                        buckets.extend(v)
                except Exception:
                    pass
            quotes = buckets
        except Exception:
            quotes = []

    rows = []
    for item in quotes:
        if isinstance(item, dict):
            row = _to_row(item)
            if row["ticker"]:
                rows.append(row)

    df = pd.DataFrame(rows).drop_duplicates(subset=["ticker"], keep="first")
    if df.empty:
        return df

    # 让 name 更可读（避免 None）
    df["name"] = df["name"].fillna("")
    return df.reset_index(drop=True)
