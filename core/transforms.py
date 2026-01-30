# core/transforms.py
from __future__ import annotations

from datetime import timedelta
import pandas as pd

from core.db import (
    query_prices_long,
    upsert_derived_daily,
    get_last_derived_date,
    get_min_price_date,
    log_refresh,
    list_transforms,
)


def _asof_fx_merge(base: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    # base: date,ticker,value ; fx: date,ticker,value
    fx2 = fx.sort_values("date").rename(columns={"value": "fx"})[["date", "fx"]]
    out = base.sort_values("date").copy()
    out = pd.merge_asof(out, fx2, on="date", direction="backward")
    out["fx"] = out["fx"].bfill()
    return out


def recompute_transform(
    con,
    transform_row: dict,
    backfill_days: int = 7,
    field: str = "close",
) -> dict:
    """
    计算一个 transform 的派生序列并落库。
    公式：
      derived = base
      if fx: derived = derived * fx (mul) or / fx (div)
      derived = derived * multiplier / divider

    注意：base/fx 都取 prices_daily 的 close（你以后需要可以扩展成可选字段）
    """
    derived_ticker = transform_row["derived_ticker"]
    base_ticker = transform_row["base_ticker"]
    fx_ticker = transform_row.get("fx_ticker")
    fx_op = (transform_row.get("fx_op") or "mul").lower()
    multiplier = float(transform_row.get("multiplier") or 1.0)
    divider = float(transform_row.get("divider") or 1.0)

    # 选择计算起点：已有派生 -> 从 last_derived - backfill；没有 -> 从 base 的最早日期
    last_d = get_last_derived_date(con, derived_ticker)
    if last_d is not None:
        start = last_d - timedelta(days=backfill_days)
    else:
        start = get_min_price_date(con, base_ticker)

    if start is None:
        log_refresh(con, derived_ticker, "empty", "no base data in prices_daily", None)
        return {"derived": derived_ticker, "status": "empty", "rows": 0, "message": "no base data"}

    base = query_prices_long(con, [base_ticker], start=start, end=None, field=field)
    if base.empty:
        log_refresh(con, derived_ticker, "empty", "base query empty", last_d)
        return {"derived": derived_ticker, "status": "empty", "rows": 0, "message": "base empty"}

    base = base.rename(columns={"value": "base"}).drop(columns=["ticker"])

    if fx_ticker:
        fx = query_prices_long(con, [fx_ticker], start=start, end=None, field="close")
        if fx.empty:
            log_refresh(con, derived_ticker, "empty", f"fx query empty: {fx_ticker}", last_d)
            return {"derived": derived_ticker, "status": "empty", "rows": 0, "message": f"fx empty: {fx_ticker}"}

        fx = fx.rename(columns={"value": "value"})  # keep signature for merge helper
        tmp = pd.DataFrame({"date": base["date"], "ticker": base_ticker, "value": base["base"]})
        merged = _asof_fx_merge(tmp, fx)
        base["base"] = merged["value"]
        base["fx"] = merged["fx"]

        if fx_op == "div":
            base["value"] = (base["base"] / base["fx"]) * multiplier / divider
        else:
            base["value"] = (base["base"] * base["fx"]) * multiplier / divider
    else:
        base["value"] = base["base"] * multiplier / divider

    out = base[["date", "value"]].dropna(subset=["value"]).copy()
    out["date"] = pd.to_datetime(out["date"]).dt.date

    n = upsert_derived_daily(con, derived_ticker, out)
    last_success = out["date"].max() if not out.empty else last_d

    log_refresh(con, derived_ticker, "success" if n > 0 else "empty", f"derived upsert {n} rows", last_success)
    return {"derived": derived_ticker, "status": "success" if n > 0 else "empty", "rows": n, "message": ""}


def update_derived_for_tickers(con, updated_tickers: list[str], backfill_days: int = 7) -> list[dict]:
    """
    当 raw base 或 fx 有更新时，找出受影响的 transforms，并重算派生序列。
    """
    updated_tickers = list({t for t in (updated_tickers or []) if t})
    if not updated_tickers:
        return []

    tf = list_transforms(con, enabled_only=True)
    if tf.empty:
        return []

    affected = tf[
        tf["base_ticker"].isin(updated_tickers)
        | tf["fx_ticker"].isin(updated_tickers)
    ]

    results = []
    for _, r in affected.iterrows():
        row = r.to_dict()
        results.append(recompute_transform(con, row, backfill_days=backfill_days, field="close"))
    return results
