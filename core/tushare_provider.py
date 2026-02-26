from __future__ import annotations

import os
from typing import Any, Dict, List


def search_tushare(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return []

    token = os.getenv("TUSHARE_TOKEN", "").strip()
    if not token:
        return []

    try:
        import tushare as ts
    except Exception:
        return []

    try:
        pro = ts.pro_api(token)
    except Exception:
        return []

    frames = []
    # futures exchanges in tushare
    for ex in ["DCE", "SHFE", "CZCE", "INE", "CFFEX", "GFEX"]:
        try:
            df = pro.fut_basic(exchange=ex, fields="ts_code,symbol,name,fut_code,trade_unit,quote_unit,list_date,delist_date")
            if df is not None and not df.empty:
                df["exchange"] = ex
                frames.append(df)
        except Exception:
            continue

    if not frames:
        return []

    full = __import__("pandas").concat(frames, ignore_index=True)
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
