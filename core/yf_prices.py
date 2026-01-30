# core/yf_prices.py
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf


def fetch_history_daily(
    ticker: str,
    start: Optional[date] = None,
    period_if_no_start: str = "max",
) -> pd.DataFrame:
    """
    返回标准化日度数据：
    columns: date, open, high, low, close, adj_close, volume
    """
    tk = (ticker or "").strip()
    if not tk:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adj_close", "volume"])

    try:
        if start is None:
            df = yf.download(
                tk,
                period=period_if_no_start,
                interval="1d",
                auto_adjust=False,
                actions=False,
                progress=False,
                threads=False,
            )
        else:
            df = yf.download(
                tk,
                start=start,
                interval="1d",
                auto_adjust=False,
                actions=False,
                progress=False,
                threads=False,
            )
    except Exception:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adj_close", "volume"])

    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adj_close", "volume"])

    # yfinance 偶尔会给 MultiIndex（理论上单 ticker 不该有，但这里兜底）
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 统一列名（yfinance: Open/High/Low/Close/Adj Close/Volume）
    col_map = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    }
    for k, v in col_map.items():
        if k in df.columns and v not in df.columns:
            df[v] = df[k]

    # 有些市场可能没 Adj Close，就用 close 兜底
    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"] if "close" in df.columns else pd.NA

    # volume 兜底
    if "volume" not in df.columns:
        df["volume"] = pd.NA

    # index -> date
    idx = df.index
    try:
        # 去掉 tz（有些会带时区）
        idx = idx.tz_localize(None)
    except Exception:
        pass

    out = pd.DataFrame(
        {
            "date": pd.to_datetime(idx).date,
            "open": df.get("open", pd.NA),
            "high": df.get("high", pd.NA),
            "low": df.get("low", pd.NA),
            "close": df.get("close", pd.NA),
            "adj_close": df.get("adj_close", pd.NA),
            "volume": df.get("volume", pd.NA),
        }
    )

    # 去掉全空行
    out = out.dropna(subset=["close"], how="all").copy()
    out = out.sort_values("date").reset_index(drop=True)
    return out
