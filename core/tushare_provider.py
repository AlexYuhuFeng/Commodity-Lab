from __future__ import annotations

import os
from typing import Any, Dict, List

import pandas as pd
import requests

_TUSHARE_PRO_URL = "https://api.tushare.pro"


def _resolve_token(token: str | None = None) -> str:
    return (token if token is not None else os.getenv("TUSHARE_TOKEN", "")).strip()


def _fetch_fut_basic_via_http(token: str, exchange: str) -> pd.DataFrame:
    payload = {
        "api_name": "fut_basic",
        "token": token,
        "params": {"exchange": exchange},
        "fields": "ts_code,symbol,name,fut_code,trade_unit,quote_unit,list_date,delist_date",
    }
    resp = requests.post(_TUSHARE_PRO_URL, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json() or {}
    if data.get("code") != 0:
        msg = data.get("msg", "unknown_error")
        raise RuntimeError(f"tushare api error: {msg}")
    result = data.get("data") or {}
    fields = result.get("fields") or []
    items = result.get("items") or []
    if not fields or not items:
        return pd.DataFrame()
    return pd.DataFrame(items, columns=fields)


def tushare_status(token: str | None = None) -> tuple[bool, str]:
    resolved = _resolve_token(token)
    if not resolved:
        return False, "missing_token"

    # SDK is optional. HTTP API fallback is supported.
    try:
        _fetch_fut_basic_via_http(resolved, "SHFE")
        return True, "ok"
    except requests.RequestException:
        return False, "network_error"
    except Exception as exc:
        msg = str(exc).lower()
        if "invalid token" in msg or "token" in msg:
            return False, "invalid_token"
        return False, "api_error"


def search_tushare(query: str, max_results: int = 20, token: str | None = None) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return []

    resolved = _resolve_token(token)
    if not resolved:
        return []

    frames = []
    for ex in ["DCE", "SHFE", "CZCE", "INE", "CFFEX", "GFEX"]:
        try:
            df = _fetch_fut_basic_via_http(resolved, ex)
            if not df.empty:
                df["exchange"] = ex
                frames.append(df)
        except Exception:
            continue

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
    for _, r in out.iterrows():
        records.append(
            {
                "ticker": r.get("ts_code", ""),
                "name": r.get("name", "") or r.get("symbol", ""),
                "quote_type": "futures",
                "exchange": r.get("exchange", ""),
                "currency": "CNY",
                "category": "commodity",
                "source": "tushare",
            }
        )
    return records
