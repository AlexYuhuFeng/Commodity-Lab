from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests
from requests import Session

TUSHARE_HTTP_URL = "https://api.tushare.pro"
FUTURE_EXCHANGES = ["DCE", "SHFE", "CZCE", "INE", "CFFEX", "GFEX"]


def _fetch_fut_basic_via_http(token: str, exchange: str) -> pd.DataFrame:
    payload = {
        "api_name": "fut_basic",
        "token": token,
        "params": {"exchange": exchange},
        "fields": "ts_code,symbol,name,fut_code,trade_unit,quote_unit,list_date,delist_date",
    }

    try:
        resp = requests.post(TUSHARE_HTTP_URL, json=payload, timeout=20)
    except requests.exceptions.ProxyError:
        direct_session = Session()
        direct_session.trust_env = False
        resp = direct_session.post(TUSHARE_HTTP_URL, json=payload, timeout=20)

    resp.raise_for_status()
    body = resp.json()

    if body.get("code") != 0:
        raise RuntimeError(body.get("msg") or "tushare api error")

    data = body.get("data") or {}
    fields = data.get("fields") or []
    items = data.get("items") or []
    if not fields or not items:
        return pd.DataFrame(columns=fields)

    return pd.DataFrame(items, columns=fields)


def tushare_status(token: str) -> Tuple[bool, str]:
    tk = (token or "").strip()
    if not tk:
        return False, "missing_token"

    try:
        _fetch_fut_basic_via_http(tk, "SHFE")
        return True, "ok"
    except Exception as exc:
        if "invalid token" in str(exc).lower():
            return False, "invalid_token"
        return False, "unreachable"


def search_tushare(query: str, max_results: int = 20, token: str | None = None) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return []

    tk = (token or os.getenv("TUSHARE_TOKEN", "")).strip()
    if not tk:
        return []

    frames: List[pd.DataFrame] = []
    for exchange in FUTURE_EXCHANGES:
        try:
            frame = _fetch_fut_basic_via_http(tk, exchange)
        except Exception:
            continue
        if frame is not None and not frame.empty:
            frame = frame.copy()
            frame["exchange"] = exchange
            frames.append(frame)

    if not frames:
        return []

    full = pd.concat(frames, ignore_index=True)
    mask = (
        full["ts_code"].fillna("").str.lower().str.contains(q)
        | full["symbol"].fillna("").str.lower().str.contains(q)
        | full["name"].fillna("").str.lower().str.contains(q)
    )
    out = full[mask].head(max_results)

    records: List[Dict[str, Any]] = []
    for _, row in out.iterrows():
        records.append(
            {
                "ticker": row.get("ts_code", ""),
                "name": row.get("name", "") or row.get("symbol", ""),
                "quote_type": "futures",
                "exchange": row.get("exchange", ""),
                "currency": "CNY",
                "category": "commodity",
                "source": "tushare",
            }
        )
    return records
